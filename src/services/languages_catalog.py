"""
Загрузка каталога языков программирования и белых списков расширений из JSON.
Формат: {"languages": [{ "id": "...", "name": "...", "extensions": ["py", ...] }, ...], "general": [...] }
расширения в JSON задаются без точки.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LanguageEntry:
    language_id: str
    display_name: str
    extensions: tuple[str, ...]


def _with_dot(ext: str) -> str:
    ext = ext.strip().lower().lstrip(".")
    return f".{ext}" if ext else ""


class LanguagesCatalog:
    def __init__(self, languages: Sequence[LanguageEntry], general_raw: Sequence[str]):
        self._languages = list(languages)
        self._general_dots = tuple(
            sorted({_with_dot(g) for g in general_raw if _with_dot(g)}, key=len, reverse=True)
        )
        self._by_id = {e.language_id: e for e in self._languages}

    @classmethod
    def load(cls, path: str | Path) -> "LanguagesCatalog":
        raw_path = Path(path)
        if not raw_path.exists():
            raise FileNotFoundError(f"Не найден каталог языков: {raw_path}")
        data = json.loads(raw_path.read_text(encoding="utf-8"))
        general = list(data.get("general") or [])
        entries: list[LanguageEntry] = []

        langs = data.get("languages") or []
        for row in langs:
            if isinstance(row, dict):
                if "id" in row:
                    lid = str(row["id"]).strip().lower()
                    name = str(row.get("name", lid)).strip()
                    extensions = tuple(str(x).lower() for x in (row.get("extensions") or []))
                    entries.append(
                        LanguageEntry(
                            language_id=lid,
                            display_name=name,
                            extensions=extensions,
                        )
                    )
                elif len(row) == 1:
                    (name_key, ext_list), = row.items()
                    lid = str(name_key).strip().lower().replace("+", "p").replace("#", "sharp")
                    lid = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in lid)
                    extensions = tuple(str(x).lower() for x in (ext_list or []))
                    entries.append(
                        LanguageEntry(
                            language_id=lid,
                            display_name=str(name_key),
                            extensions=extensions,
                        )
                    )
                else:
                    logger.warning("Пропуск непонятной записи языка: %s", row)
                    continue

        return cls(entries, general)

    def list_language_ids(self) -> list[str]:
        return [e.language_id for e in self._languages]

    def language_exists(self, language_id: str) -> bool:
        return language_id.strip().lower() in self._by_id

    def api_languages_payload(self) -> list[dict]:
        return [
            {
                "id": e.language_id,
                "name": e.display_name,
                "extensions": [ _with_dot(x).lstrip(".") for x in e.extensions ],
            }
            for e in self._languages
        ]

    def whitelist_for_language(self, language_id: str | None) -> list[str]:
        """
        Список расширений с ведущей точкой: general ∪ языковые для выбранного id.
        language_id=None — legacy-режим без привязки к комнате.
        """
        dots = list(self._general_dots)
        if language_id:
            lid = language_id.strip().lower()
            ent = self._by_id.get(lid)
            if ent:
                for ext in ent.extensions:
                    d = _with_dot(ext)
                    if d not in dots:
                        dots.append(d)
            else:
                logger.warning("Неизвестный language_id для whitelist: %s", language_id)
        else:
            for e in self._languages:
                for ext in e.extensions:
                    d = _with_dot(ext)
                    if d not in dots:
                        dots.append(d)

        dedup: dict[str, None] = {}
        for x in dots:
            if x:
                dedup[x] = None
        return list(dedup.keys())
