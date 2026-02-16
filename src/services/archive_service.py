import base64
import zipfile
import tarfile
import io
from src.services.file_processor import FolderStructure


class ArchiveProcessor:
    """
    Сервис для обработки архивов, переданных в формате base64,
    и преобразования их в класс FolderStructure.
    """

    def __init__(self, whitelist=None):
        """
        Инициализирует ArchiveProcessor.

        Args:
            whitelist: список расширений файлов для сохранения содержимого
                      (например, ['.py', '.txt', '.md'])
        """
        self.whitelist = whitelist if whitelist else ['.py', '.txt', '.md', '.json', '.yaml', '.yml']

    def process_base64_archive(self, base64_string, archive_type='auto'):
        """
        Обрабатывает архив, переданный в формате base64.

        Args:
            base64_string: строка с архивом в формате base64
            archive_type: тип архива ('zip', 'tar', 'tar.gz', 'auto')
                         'auto' - автоматическое определение типа

        Returns:
            FolderStructure с содержимым архива

        Raises:
            ValueError: если не удалось определить или обработать архив
        """
        # Декодируем base64
        try:
            archive_bytes = base64.b64decode(base64_string)
        except Exception as e:
            raise ValueError(f"Ошибка декодирования base64: {str(e)}")

        # Определяем тип архива
        if archive_type == 'auto':
            archive_type = self._detect_archive_type(archive_bytes)

        # Обрабатываем архив в зависимости от типа
        if archive_type == 'zip':
            return self._process_zip(archive_bytes)
        elif archive_type in ['tar', 'tar.gz', 'tar.bz2', 'tar.xz']:
            return self._process_tar(archive_bytes, archive_type)
        else:
            raise ValueError(f"Неподдерживаемый тип архива: {archive_type}")

    def _detect_archive_type(self, archive_bytes):
        """
        Автоматически определяет тип архива по сигнатуре.

        Args:
            archive_bytes: байты архива

        Returns:
            Тип архива ('zip', 'tar', 'tar.gz', и т.д.)
        """
        # Проверяем ZIP (сигнатура: PK)
        if archive_bytes[:2] == b'PK':
            return 'zip'

        # Проверяем TAR (сигнатура на позиции 257: ustar)
        if len(archive_bytes) > 262 and archive_bytes[257:262] == b'ustar':
            return 'tar'

        # Проверяем GZIP (сигнатура: 1f 8b)
        if archive_bytes[:2] == b'\x1f\x8b':
            return 'tar.gz'

        # Проверяем BZIP2 (сигнатура: BZ)
        if archive_bytes[:2] == b'BZ':
            return 'tar.bz2'

        # Проверяем XZ (сигнатура: fd 37 7a 58 5a 00)
        if archive_bytes[:6] == b'\xfd7zXZ\x00':
            return 'tar.xz'

        raise ValueError("Не удалось определить тип архива")

    def _process_zip(self, archive_bytes):
        """
        Обрабатывает ZIP архив.

        Args:
            archive_bytes: байты ZIP архива

        Returns:
            FolderStructure с содержимым архива
        """
        files_data = []

        try:
            with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zip_file:
                for file_info in zip_file.filelist:
                    # Пропускаем директории
                    if file_info.is_dir():
                        continue

                    file_path = file_info.filename

                    # Нормализуем путь (убираем начальный слеш, если есть)
                    if file_path.startswith('/'):
                        file_path = file_path[1:]

                    # Проверяем расширение файла
                    file_ext = '.' + file_path.split('.')[-1] if '.' in file_path.split('/')[-1] else ''

                    if file_ext in self.whitelist:
                        # Читаем содержимое файла
                        try:
                            content = zip_file.read(file_info.filename).decode('utf-8')
                            files_data.append((file_path, content))
                        except UnicodeDecodeError:
                            # Если не удалось декодировать как UTF-8, пропускаем содержимое
                            files_data.append((file_path, None))
                    else:
                        files_data.append((file_path, None))

        except zipfile.BadZipFile as e:
            raise ValueError(f"Некорректный ZIP архив: {str(e)}")

        return FolderStructure(files_data, whitelist=self.whitelist)

    def _process_tar(self, archive_bytes, archive_type):
        """
        Обрабатывает TAR архив (включая сжатые варианты).
        
        Args:
            archive_bytes: байты TAR архива
            archive_type: тип архива ('tar', 'tar.gz', 'tar.bz2', 'tar.xz')
        
        Returns:
            FolderStructure с содержимым архива
        """
        files_data = []

        # Определяем режим открытия
        mode_map = {
            'tar': 'r',
            'tar.gz': 'r:gz',
            'tar.bz2': 'r:bz2',
            'tar.xz': 'r:xz'
        }
        mode = mode_map.get(archive_type, 'r')

        try:
            with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode=mode) as tar_file:
                for member in tar_file.getmembers():
                    # Пропускаем директории
                    if member.isdir():
                        continue

                    file_path = member.name

                    # Нормализуем путь
                    if file_path.startswith('/'):
                        file_path = file_path[1:]

                    # Проверяем расширение файла
                    file_ext = '.' + file_path.split('.')[-1] if '.' in file_path.split('/')[-1] else ''

                    if file_ext in self.whitelist:
                        # Читаем содержимое файла
                        try:
                            file_obj = tar_file.extractfile(member)
                            if file_obj:
                                content = file_obj.read().decode('utf-8')
                                files_data.append((file_path, content))
                            else:
                                files_data.append((file_path, None))
                        except (UnicodeDecodeError, AttributeError):
                            files_data.append((file_path, None))
                    else:
                        files_data.append((file_path, None))

        except tarfile.TarError as e:
            raise ValueError(f"Некорректный TAR архив: {str(e)}")

        return FolderStructure(files_data, whitelist=self.whitelist)


if __name__ == "__main__":
    # Пример использования
    import os

    # Создаем тестовый ZIP архив
    test_zip = io.BytesIO()
    with zipfile.ZipFile(test_zip, 'w') as zf:
        zf.writestr('test.py', 'print("Hello, World!")')
        zf.writestr('src/main.py', 'def main():\n    pass')
        zf.writestr('README.md', '# Test Project')
        zf.writestr('data/file.dat', 'binary data')

    # Конвертируем в base64
    test_zip.seek(0)
    base64_archive = base64.b64encode(test_zip.read()).decode('utf-8')

    # Обрабатываем архив
    processor = ArchiveProcessor(whitelist=['.py', '.md'])
    structure = processor.process_base64_archive(base64_archive)

    print("Структура архива:")
    print(structure)
    print("\n" + "="*50 + "\n")

    print("Содержимое файлов:")
    structure.print_files_content()
