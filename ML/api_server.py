#!/usr/bin/env python3
"""
FastAPI сервер для локального запуска ИИ моделей.
Предоставляет REST API для взаимодействия с локальной моделью ИИ.
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional, AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

# Добавляем src в путь для импорта модулей
sys.path.insert(0, str(Path(__file__).parent))

from src import (
    Logger,
    ConfigManager,
    ModelManager,
    ModelDownloader,
)


# ============================================================================
# Pydantic модели для валидации запросов и ответов
# ============================================================================

class GenerateRequest(BaseModel):
    """Модель запроса для генерации текста."""
    
    prompt: str = Field(..., description="Входной промпт для модели", min_length=1)
    temperature: Optional[float] = Field(None, description="Температура генерации (0.0-2.0)", ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, description="Максимальное количество токенов", ge=1, le=4096)
    top_p: Optional[float] = Field(None, description="Top-p sampling (0.0-1.0)", ge=0.0, le=1.0)
    top_k: Optional[int] = Field(None, description="Top-k sampling", ge=1, le=100)
    repeat_penalty: Optional[float] = Field(None, description="Штраф за повторения (1.0-2.0)", ge=1.0, le=2.0)
    stream: bool = Field(True, description="Использовать streaming режим")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        """Валидация промпта."""
        if not v or not v.strip():
            raise ValueError("Промпт не может быть пустым")
        return v.strip()


class GenerateResponse(BaseModel):
    """Модель ответа для генерации текста (non-streaming)."""
    
    text: str = Field(..., description="Сгенерированный текст")
    prompt: str = Field(..., description="Исходный промпт")


class HealthResponse(BaseModel):
    """Модель ответа для проверки здоровья сервера."""
    
    status: str = Field(..., description="Статус сервера")
    model_loaded: bool = Field(..., description="Загружена ли модель")


class ModelInfoResponse(BaseModel):
    """Модель ответа с информацией о модели."""
    
    path: str = Field(..., description="Путь к файлу модели")
    loaded: bool = Field(..., description="Загружена ли модель")
    n_ctx: int = Field(..., description="Размер контекста")
    n_gpu_layers: int = Field(..., description="Количество GPU слоев")
    temperature: float = Field(..., description="Температура генерации")
    top_p: float = Field(..., description="Top-p sampling")
    top_k: int = Field(..., description="Top-k sampling")
    repeat_penalty: float = Field(..., description="Штраф за повторения")
    max_tokens: int = Field(..., description="Максимальное количество токенов")
    stream: bool = Field(..., description="Streaming режим")


class ErrorResponse(BaseModel):
    """Модель ответа с ошибкой."""
    
    error: str = Field(..., description="Описание ошибки")
    detail: Optional[str] = Field(None, description="Детали ошибки")


# ============================================================================
# Глобальные переменные для singleton паттерна
# ============================================================================

logger: Optional[Logger] = None
config_manager: Optional[ConfigManager] = None
model_manager: Optional[ModelManager] = None
model_downloader: Optional[ModelDownloader] = None


# ============================================================================
# Lifecycle management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения.
    Инициализация при запуске и очистка при завершении.
    """
    global logger, config_manager, model_manager, model_downloader
    
    try:
        # Инициализация при запуске
        print("Инициализация API сервера...")
        
        # Загружаем конфигурацию
        config_manager = ConfigManager("config.yaml")
        config_manager.load()
        
        # Инициализируем логгер
        logger = Logger(
            name="AI_local_api",
            level=config_manager.app.log_level
        )
        logger.info("API сервер запущен")
        
        # Инициализируем загрузчик моделей
        model_downloader = ModelDownloader(
            models_dir="./models",
            logger=logger
        )
        
        # Проверяем наличие модели
        download_config = config_manager.download
        try:
            model_path = model_downloader.ensure_model_available(
                repo_id=download_config.repo_id,
                filename=download_config.filename,
                auto_download=download_config.auto_download,
                token=download_config.token
            )
            logger.info(f"Модель доступна: {model_path}")
        except Exception as e:
            logger.error(f"Ошибка при проверке модели: {e}")
            raise
        
        # Инициализируем и загружаем модель
        model_manager = ModelManager(
            config=config_manager.model,
            logger=logger
        )
        
        print("Загрузка модели AI...")
        logger.info("Начало загрузки модели")
        model_manager.load_model()
        logger.info("Модель успешно загружена")
        print("Модель успешно загружена!")
        
        # Выводим информацию о модели
        model_info = model_manager.get_model_info()
        logger.info(f"Модель: {model_info['path']}")
        logger.info(f"Контекст: {model_info['n_ctx']} токенов")
        logger.info(f"GPU слои: {model_info['n_gpu_layers']}")
        
        print("API сервер готов к работе!")
        
        yield
        
    finally:
        # Очистка при завершении
        logger.info("Завершение работы API сервера")
        if model_manager and model_manager.is_loaded():
            logger.info("Выгрузка модели")
            model_manager.unload_model()
        logger.info("API сервер остановлен")


# ============================================================================
# FastAPI приложение
# ============================================================================

app = FastAPI(
    title="AI Local API",
    description="REST API для взаимодействия с локальной моделью ИИ",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Вспомогательные функции
# ============================================================================

async def generate_stream(prompt: str, params: dict) -> AsyncIterator[str]:
    """
    Асинхронный генератор для streaming ответа.
    
    Args:
        prompt: Входной промпт
        params: Параметры генерации
        
    Yields:
        Токены ответа в формате Server-Sent Events
    """
    try:
        # Создаем временный конфиг с переопределенными параметрами
        temp_config = config_manager.model
        
        # Переопределяем параметры, если они указаны
        if params.get('temperature') is not None:
            temp_config.temperature = params['temperature']
        if params.get('max_tokens') is not None:
            temp_config.max_tokens = params['max_tokens']
        if params.get('top_p') is not None:
            temp_config.top_p = params['top_p']
        if params.get('top_k') is not None:
            temp_config.top_k = params['top_k']
        if params.get('repeat_penalty') is not None:
            temp_config.repeat_penalty = params['repeat_penalty']
        
        # Включаем streaming
        temp_config.stream = True
        
        # Создаем временный model_manager с новыми параметрами
        temp_model_manager = ModelManager(config=temp_config, logger=logger)
        temp_model_manager.model = model_manager.model
        temp_model_manager._is_loaded = True
        
        # Генерируем ответ
        for token in temp_model_manager.generate_response(prompt):
            # Формат Server-Sent Events
            yield f"data: {token}\n\n"
            # Даем возможность другим задачам выполниться
            await asyncio.sleep(0)
        
        # Отправляем сигнал завершения
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Ошибка при streaming генерации: {e}")
        yield f"data: [ERROR: {str(e)}]\n\n"


# ============================================================================
# API эндпоинты
# ============================================================================

@app.post(
    "/generate",
    response_model=GenerateResponse,
    responses={
        200: {"description": "Успешная генерация"},
        400: {"model": ErrorResponse, "description": "Неверный запрос"},
        500: {"model": ErrorResponse, "description": "Внутренняя ошибка сервера"}
    },
    summary="Генерация текста",
    description="Генерирует текст на основе входного промпта. Поддерживает streaming и non-streaming режимы."
)
async def generate(request: GenerateRequest):
    """
    Эндпоинт для генерации текста.
    
    В streaming режиме возвращает Server-Sent Events.
    В non-streaming режиме возвращает полный ответ в JSON.
    """
    logger.info("Получен запрос на /generate.")
    try:
        if not model_manager or not model_manager.is_loaded():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Модель не загружена"
            )
        
        logger.info(f"Получен запрос на генерацию: prompt_length={len(request.prompt)}, stream={request.stream}")
        
        # Собираем параметры генерации
        params = {
            'temperature': request.temperature,
            'max_tokens': request.max_tokens,
            'top_p': request.top_p,
            'top_k': request.top_k,
            'repeat_penalty': request.repeat_penalty,
        }
        
        if request.stream:
            # Streaming режим - возвращаем SSE
            logger.info("Запуск streaming генерации")
            return StreamingResponse(
                generate_stream(request.prompt, params),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # Non-streaming режим - возвращаем полный ответ
            logger.info("Запуск non-streaming генерации")
            
            # Создаем временный конфиг с переопределенными параметрами
            temp_config = config_manager.model
            
            if params.get('temperature') is not None:
                temp_config.temperature = params['temperature']
            if params.get('max_tokens') is not None:
                temp_config.max_tokens = params['max_tokens']
            if params.get('top_p') is not None:
                temp_config.top_p = params['top_p']
            if params.get('top_k') is not None:
                temp_config.top_k = params['top_k']
            if params.get('repeat_penalty') is not None:
                temp_config.repeat_penalty = params['repeat_penalty']
            
            # Отключаем streaming
            temp_config.stream = False
            
            # Создаем временный model_manager
            temp_model_manager = ModelManager(config=temp_config, logger=logger)
            temp_model_manager.model = model_manager.model
            temp_model_manager._is_loaded = True
            
            # Генерируем полный ответ
            response_text = temp_model_manager.generate_response_complete(request.prompt)
            
            logger.info(f"Генерация завершена: response_length={len(response_text)}")
            
            return GenerateResponse(
                text=response_text,
                prompt=''
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации: {str(e)}"
        )


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Проверка здоровья сервера",
    description="Возвращает статус сервера и информацию о загрузке модели"
)
async def health():
    """
    Эндпоинт для проверки здоровья сервера.
    """
    try:
        is_loaded = model_manager is not None and model_manager.is_loaded()
        
        return HealthResponse(
            status="ok" if is_loaded else "model_not_loaded",
            model_loaded=is_loaded
        )
    except Exception as e:
        logger.error(f"Ошибка при проверке здоровья: {e}")
        return HealthResponse(
            status="error",
            model_loaded=False
        )


@app.get(
    "/model-info",
    response_model=ModelInfoResponse,
    responses={
        200: {"description": "Информация о модели"},
        503: {"model": ErrorResponse, "description": "Модель не загружена"}
    },
    summary="Информация о модели",
    description="Возвращает детальную информацию о загруженной модели"
)
async def model_info():
    """
    Эндпоинт для получения информации о модели.
    """
    try:
        if not model_manager or not model_manager.is_loaded():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Модель не загружена"
            )
        
        info = model_manager.get_model_info()
        
        return ModelInfoResponse(**info)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении информации о модели: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении информации: {str(e)}"
        )


# ============================================================================
# Точка входа
# ============================================================================

def main():
    """Запуск API сервера."""
    print("="*70)
    print("AI Local API Server")
    print("="*70)
    print("\nЗапуск сервера на http://0.0.0.0:8000")
    print("Документация API: http://0.0.0.0:8000/docs")
    print("="*70 + "\n")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    main()