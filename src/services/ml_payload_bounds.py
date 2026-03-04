"""Оценка объёма UTF-8 текста проекта после нормализации для ML."""

from __future__ import annotations

from src.services.file_processor import FolderStructure


def utf8_payload_size_bytes(project: FolderStructure) -> int:
    structure = str(project)
    files_blob = ""
    if hasattr(project, "get_files_content"):
        try:
            files_blob = project.get_files_content() or ""
        except Exception:
            files_blob = ""
    return len(structure.encode("utf-8")) + len(files_blob.encode("utf-8"))
