
# API Документация LLaMA Local

Подробное руководство по использованию REST API для взаимодействия с локальной моделью LLaMA.

## Содержание

- [Быстрый старт](#быстрый-старт)
- [Эндпоинты](#эндпоинты)
  - [POST /generate](#post-generate)
  - [GET /health](#get-health)
  - [GET /model-info](#get-model-info)
- [Параметры генерации](#параметры-генерации)
- [Режимы работы](#режимы-работы)
  - [Streaming режим](#streaming-режим)
  - [Non-streaming режим](#non-streaming-режим)
- [Примеры использования](#примеры-использования)
  - [cURL](#примеры-с-curl)
  - [Python](#примеры-с-python)
  - [JavaScript](#примеры-с-javascript)
- [Обработка ошибок](#обработка-ошибок)
- [Интеграция в приложения](#интеграция-в-приложения)

## Быстрый старт

1. Запустите API сервер:
```bash
cd llama_local
python api_server.py
```

2. Сервер будет доступен по адресу: `http://localhost:8000`

3. Интерактивная документация (Swagger UI): `http://localhost:8000/docs`

4. Альтернативная документация (ReDoc): `http://localhost:8000/redoc`

## Эндпоинты

### POST /generate

Генерирует текст на основе входного промпта.

**URL:** `/generate`

**Метод:** `POST`

**Content-Type:** `application/json`

**Тело запроса:**

```json
{
  "prompt": "Что такое машинное обучение?",
  "temperature": 0.7,
  "max_tokens": 512,
  "top_p": 0.9,
  "top_k": 40,
  "repeat_penalty": 1.1,
  "stream": true
}
```

**Параметры:**

| Параметр | Тип | Обязательный | Описание | Диапазон |
|----------|-----|--------------|----------|----------|
| `prompt` | string | Да | Входной промпт для модели | min: 1 символ |
| `temperature` | float | Нет | Температура генерации | 0.0 - 2.0 |
| `max_tokens` | integer | Нет | Максимальное количество токенов | 1 - 4096 |
| `top_p` | float | Нет | Nucleus sampling | 0.0 - 1.0 |
| `top_k` | integer | Нет | Top-K sampling | 1 - 100 |
| `repeat_penalty` | float | Нет | Штраф за повторения | 1.0 - 2.0 |
| `stream` | boolean | Нет | Использовать streaming режим | true/false (по умолчанию: true) |

**Ответ (non-streaming):**

```json
{
  "text": "Машинное обучение - это раздел искусственного интеллекта...",
  "prompt": "Что такое машинное обучение?"
}
```

**Ответ (streaming):**

Server-Sent Events (SSE) формат:
```
data: Машинное
data:  обучение
data:  -
data:  это
...
data: [DONE]
```

**Коды ответа:**

- `200` - Успешная генерация
- `400` - Неверный запрос (невалидные параметры)
- `503` - Модель не загружена
- `500` - Внутренняя ошибка сервера

---

### GET /health

Проверяет состояние сервера и загрузку модели.

**URL:** `/health`

**Метод:** `GET`

**Ответ:**

```json
{
  "status": "ok",
  "model_loaded": true
}
```

**Параметры ответа:**

- `status` - Статус сервера (`"ok"` или `"model_not_loaded"` или `"error"`)
- `model_loaded` - Загружена ли модель (boolean)

**Коды ответа:**

- `200` - Успешный запрос

---

### GET /model-info

Возвращает детальную информацию о загруженной модели.

**URL:** `/model-info`

**Метод:** `GET`

**Ответ:**

```json
{
  "path": "./models/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
  "loaded": true,
  "n_ctx": 2048,
  "n_gpu_layers": -1,
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 40,
  "repeat_penalty": 1.1,
  "max_tokens": 512,
  "stream": true
}
```

**Коды ответа:**

- `200` - Успешный запрос
- `503` - Модель не загружена
- `500` - Внутренняя ошибка сервера

## Параметры генерации

### temperature (температура)

Контролирует случайность генерации:
- **0.0-0.3**: Детерминированный, предсказуемый вывод
- **0.4-0.7**: Сбалансированный (рекомендуется)
- **0.8-1.5**: Креативный, разнообразный
- **1.6-2.0**: Очень случайный, может быть несвязным

**Пример:**
```json
{
  "prompt": "Напиши стихотворение",
  "temperature": 1.2
}
```

### max_tokens (максимум токенов)

Ограничивает длину генерируемого текста:
- **50-100**: Короткие ответы
- **200-512**: Средние ответы (рекомендуется)
- **1000+**: Длинные ответы

**Примечание:** 1 токен ≈ 0.75 слова в русском языке.

### top_p (nucleus sampling)

Выбирает токены из топ-P вероятностной массы:
- **0.9**: Рекомендуется для большинства случаев
- **0.95**: Более разнообразный вывод
- **1.0**: Учитывает все токены

### top_k (top-K sampling)

Ограничивает выбор K наиболее вероятными токенами:
- **40**: Рекомендуется по умолчанию
- **20**: Более консервативный
- **80**: Более разнообразный

### repeat_penalty (штраф за повторения)

Уменьшает вероятность повторения токенов:
- **1.0**: Без штрафа
- **1.1**: Легкий штраф (рекомендуется)
- **1.3+**: Сильный штраф (может снизить качество)

## Режимы работы

### Streaming режим

Токены отправляются по мере генерации в формате Server-Sent Events (SSE).

**Преимущества:**
- Мгновенная обратная связь
- Лучший UX для длинных ответов
- Возможность прерывания генерации

**Использование:**
```json
{
  "prompt": "Расскажи длинную историю",
  "stream": true
}
```

### Non-streaming режим

Полный ответ возвращается после завершения генерации.

**Преимущества:**
- Проще обрабатывать
- Подходит для коротких ответов
- Легче интегрировать

**Использование:**
```json
{
  "prompt": "Что такое AI?",
  "stream": false
}
```

## Примеры использования

### Примеры с cURL

#### Базовый запрос (non-streaming)

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Что такое машинное обучение?",
    "stream": false
  }'
```

#### Запрос с параметрами

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Напиши короткое стихотворение о весне",
    "temperature": 1.2,
    "max_tokens": 200,
    "top_p": 0.95,
    "stream": false
  }'
```

#### Streaming запрос

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -N \
  -d '{
    "prompt": "Расскажи историю",
    "stream": true
  }'
```

#### Проверка здоровья

```bash
curl "http://localhost:8000/health"
```

#### Информация о модели

```bash
curl "http://localhost:8000/model-info"
```

### Примеры с Python

#### Базовый запрос (non-streaming)

```python
import requests

url = "http://localhost:8000/generate"
payload = {
    "prompt": "Что такое машинное обучение?",
    "stream": False
}

response = requests.post(url, json=payload)
data = response.json()

print(f"Промпт: {data['prompt']}")
print(f"Ответ: {data['text']}")
```

#### Запрос с параметрами

```python
import requests

url = "http://localhost:8000/generate"
payload = {
    "prompt": "Объясни квантовую физику простыми словами",
    "temperature": 0.7,
    "max_tokens": 512,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "stream": False
}

response = requests.post(url, json=payload)
if response.status_code == 200:
    data = response.json()
    print(data['text'])
else:
    print(f"Ошибка: {response.status_code}")
    print(response.json())
```

#### Streaming запрос

```python
import requests
import json

url = "http://localhost:8000/generate"
payload = {
    "prompt": "Расскажи длинную историю о космосе",
    "temperature": 0.8,
    "stream": True
}

response = requests.post(url, json=payload, stream=True)

print("Ответ модели:")
for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            token = line[6:]  # Убираем 'data: '
            if token == '[DONE]':
                print("\n\nГенерация завершена!")
                break
            elif token.startswith('[ERROR'):
                print(f"\nОшибка: {token}")
                break
            else:
                print(token, end='', flush=True)
```

#### Полный пример с обработкой ошибок

```python
import requests
from typing import Optional, Dict, Any

class LlamaLocalClient:
    """Клиент для взаимодействия с LLaMA Local API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repeat_penalty: Optional[float] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Генерирует текст на основе промпта."""
        url = f"{self.base_url}/generate"
        payload = {"prompt": prompt, "stream": stream}
        
        # Добавляем опциональные параметры
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        if top_k is not None:
            payload["top_k"] = top_k
        if repeat_penalty is not None:
            payload["repeat_penalty"] = repeat_penalty
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")
            raise
    
    def generate_stream(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Генерирует текст в streaming режиме."""
        url = f"{self.base_url}/generate"
        payload = {"prompt": prompt, "stream": True}
        
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        # Добавляем остальные параметры
        payload.update(kwargs)
        
        try:
            response = requests.post(url, json=payload, stream=True, timeout=300)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        token = line[6:]
                        if token == '[DONE]':
                            break
                        elif token.startswith('[ERROR'):
                            raise Exception(token)
                        else:
                            yield token
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при streaming запросе: {e}")
            raise
    
    def health(self) -> Dict[str, Any]:
        """Проверяет состояние сервера."""
        url = f"{self.base_url}/health"
        response = requests.get(url)
        return response.json()
    
    def model_info(self) -> Dict[str, Any]:
        """Получает информацию о модели."""
        url = f"{self.base_url}/model-info"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


# Пример использования
if __name__ == "__main__":
    client = LlamaLocalClient()
    
    # Проверка здоровья
    health = client.health()
    print(f"Статус сервера: {health['status']}")
    print(f"Модель загружена: {health['model_loaded']}")
    
    # Информация о модели
    info = client.model_info()
    print(f"\nМодель: {info['path']}")
    print(f"Контекст: {info['n_ctx']} токенов")
    
    # Non-streaming генерация
    print("\n--- Non-streaming режим ---")
    result = client.generate(
        prompt="Что такое Python?",
        temperature=0.7,
        max_tokens=200,
        stream=False
    )
    print(f"Ответ: {result['text']}")
    
    # Streaming генерация
    print("\n--- Streaming режим ---")
    print("Ответ: ", end='', flush=True)
    for token in client.generate_stream(
        prompt="Расскажи о машинном обучении",
        temperature=0.7,
        max_tokens=300
    ):
        print(token, end='', flush=True)
    print("\n")
```

### Примеры с JavaScript

#### Fetch API (non-streaming)

```javascript
async function generateText(prompt, options = {}) {
  const url = 'http://localhost:8000/generate';
  const payload = {
    prompt: prompt,
    stream: false,
    ...options
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.text;
  } catch (error) {
    console.error('Ошибка при генерации:', error);
    throw error;
  }
}

// Использование
generateText('Что такое JavaScript?', {
  temperature: 0.7,
  max_tokens: 300
}).then(text => {
  console.log('Ответ:', text);
});
```

#### Fetch API (streaming)

```javascript
async function generateTextStream(prompt, options = {}) {
  const url = 'http://localhost:8000/generate';
  const payload = {
    prompt: prompt,
    stream: true,
    ...options
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const token = line.slice(6);
          
          if (token === '[DONE]') {
            console.log('\nГенерация завершена!');
            return;
          } else if (token.startsWith('[ERROR')) {
            console.error('Ошибка:', token);
            return;
          } else {
            process.stdout.write(token);
          }
        }
      }
    }
  } catch (error) {
    console.error('Ошибка при streaming генерации:', error);
    throw error;
  }
}

// Использование
generateTextStream('Расскажи о Node.js', {
  temperature: 0.8,
  max_tokens: 500
});
```

#### Axios (с обработкой ошибок)

```javascript
const axios = require('axios');

class LlamaLocalClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.client = axios.create({
      baseURL: baseURL,
      timeout: 300000, // 5 минут
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }

  async generate(prompt, options = {}) {
    try {
      const response = await this.client.post('/generate', {
        prompt: prompt,
        stream: false,
        ...options
      });
      return response.data;
    } catch (error) {
      if (error.response) {
        console.error('Ошибка сервера:', error.response.data);
      } else if (error.request) {
        console.error('Нет ответа от сервера');
      } else {
        console.error('Ошибка:', error.message);
      }
      throw error;
    }
  }

  async health() {
    const response = await this.client.get('/health');
    return response.data;
  }

  async modelInfo() {
    const response = await this.client.get('/model-info');
    return response.data;
  }
}

// Использование
(async () => {
  const client = new LlamaLocalClient();
  
  // Проверка здоровья
  const health = await client.health();
  console.log('Статус:', health.status);
  
  // Генерация
  const result = await client.generate('Что такое TypeScript?', {
    temperature: 0.7,
    max_tokens: 300
  });
  console.log('Ответ:', result.text);
})();
```

## Обработка ошибок

### Коды ошибок

| Код | Описание | Причина |
|-----|----------|---------|
| 400 | Bad Request | Невалидные параметры запроса |
| 503 | Service Unavailable | Модель не загружена |
| 500 | Internal Server Error | Внутренняя ошибка сервера |

### Формат ошибки

```json
{
  "detail": "Описание ошибки"
}
```

### Примеры обработки

#### Python

```python
import requests

try:
    response = requests.post(
        "http://localhost:8000/generate",
        json={"prompt": "Test", "stream": False},
        timeout=300
    )
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 400:
        print("Неверные параметры запроса")
    elif e.response.status_code == 503:
        print("Модель не загружена, подождите")
    elif e.response.status_code == 500:
        print("Ошибка сервера")
    print(f"Детали: {e.response.json()}")
except requests.exceptions.Timeout:
    print("Превышено время ожидания")
except requests.exceptions.ConnectionError:
    print("Не удалось подключиться к серверу")
```

#### JavaScript

```javascript
try {
  const response = await fetch('http://localhost:8000/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: 'Test', stream: false })
  });

  if (!response.ok) {
    const error = await response.json();
    
    switch (response.status) {
      case 400:
        console.error('Неверные параметры:', error.detail);
        break;
      case 503:
        console.error('Модель не загружена');
        break;
      case 500:
        console.error('Ошибка сервера:', error.detail);
        break;
      default:
        console.error('Неизвестная ошибка:', error);
    }
    throw new Error(error.detail);
  }

  const data = await response.json();
  console.log(data.text);
} catch (error) {
  console.error('Ошибка запроса:', error);
}
```

## Интеграция в приложения

### Веб-приложение (React)

```jsx
import React, { useState } from 'react';

function ChatInterface() {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResponse('');

    try {
      const res = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompt,
          stream: true,
          temperature: 0.7,
          max_tokens: 512
        })
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const token = line.slice(6);
            if (token === '[DONE]') {
              setLoading(false);
              return;
            } else if (!token.startsWith('[ERROR')) {
              setResponse(prev => prev + token);
            }
          }
        }
      }
    } catch (error) {
      console.error('Ошибка:', error);
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Введите ваш вопрос..."
          rows={4}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Генерация...' : 'Отправить'}
        </button>
      </form>
      {response && (
        <div>
          <h3>Ответ:</h3>
          <p>{response}</p>
        </div>
      )}
    </div>
  );
}

export default ChatInterface;
```

### CLI приложение (Python)

```python
#!/usr/bin/env python3
"""Простой CLI клиент для LLaMA Local API."""

import sys
import requests
from typing import Optional

def generate_text(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 512,
    stream: bool = True
) -> None:
    """Генерирует текст и выводит результат."""
    url = "http://localhost:8000/generate"
    payload = {
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream
    }
    
    try:
        if stream:
            response = requests.post(url, json=payload, stream=True, timeout=300)
            response.raise_for_status()
            
            print("\nОтвет модели:")
            print("-" * 70)
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        token = line[6:]
                        if token == '[DONE]':
                            print("\n" + "-" * 70)
                            break
                        elif token.startswith('[ERROR'):
                            print(f"\nОшибка: {token}")
                            break
                        else:
                            print(token, end='', flush=True)
        else:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()
            
            print("\nОтвет модели:")
            print("-" * 70)
            print(data['text'])
            print("-" * 70)
    
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Главная функция CLI."""
    if len(sys.argv) < 2:
        print("Использование: python cli_client.py 'ваш промпт'")
        sys.exit(1)
    
    prompt = ' '.join(sys.argv[1:])
    generate_text(prompt)

if __name__ == "__main__":
    main()
```

### Telegram бот

```python
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LLAMA_API_URL = "http://localhost:8000/generate"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    await update.message.reply_text(
        "Привет! Я бот на основе LLaMA. Задай мне любой вопрос!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений."""
    user_message = update.message.text
    
    # Отправляем индикатор печати
    await update.message.chat.send_action("typing")
    
    try:
        # Запрос к API
        response = requests.post(
            LLAMA_API_URL,
            json={
                "prompt": user_message,
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 512
            },
            timeout=300
        )
        response.raise_for_status()
        
        data = response.json()
        await update.message.reply_text(data['text'])
    
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text(
            "Извините, произошла ошибка при обработке вашего запроса."
        )

def main():
    """Запуск бота."""
    # Замените YOUR_TOKEN на ваш токен
    application = Application.builder().token("YOUR_TOKEN").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
```

## Советы по использованию

### Оптимизация производительности

1. **Используйте streaming для длинных ответов** - улучшает UX
2. **Ограничивайте max_tokens** - ускоряет генерацию
3. **Настройте temperature** - баланс между качеством и скоростью
4. **Используйте connection pooling** - для множественных запросов

### Безопасность

1. **Валидируйте входные данные** - проверяйте промпты на стороне клиента
2. **Ограничивайте длину промптов** - защита от DoS
3. **Используйте rate limiting** - ограничение количества запросов
4. **Не передавайте чувствительные данные** - модель работает локально, но логи могут сохраняться

### Мониторинг

Регулярно проверяйте `/health` эндпоинт