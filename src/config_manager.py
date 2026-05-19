import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class ServerConfig:
    host: str
    port: int
    reload: Optional[bool] = True

@dataclass
class DatabaseConfig:
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    file_path: Optional[Path] = None
    password: Optional[str] = None
    database: str = None
    drop: bool = False

@dataclass
class LoggerConfig:
    level: str

class ConfigManager:
    def __init__(self, config_path: Path):
        self.config_path = Path(config_path)
        self._server_config: Optional[Dict[str, Any]] = None
        self._database_config: Optional[Dict[str, Any]] = None
        self._logger_config: Optional[Dict[str, Any]] = None

    def load(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Конфигурационный файл {self.config_path} не найден")
        
        with open(self._config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

        self._validate_config()
        self._parse_config()

    def _check_section(self, section: str):
        if section not in self._config:
            raise ValueError(f"В конфигурационном файле отсутствует секция '{section}'")

    def _validate_config(self) -> None:
        if not self._config:
            raise ValueError("Конфигурационный файл пустой")
        self._check_section("server")
        self._check_section("database")
        self._check_section("logger")

    def _parse_config(self) -> None:
        self._server_config = ServerConfig(**self._config["server"])
        self._database_config = DatabaseConfig(**self._config["database"])
        self._logger_config = LoggerConfig(**self._config["logger"])
        