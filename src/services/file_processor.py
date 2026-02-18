class FolderStructure:
    def __init__(self, files_data, whitelist=None):
        """
        Инициализирует структуру папок.
        
        Args:
            files_data: список кортежей (путь, содержимое) или просто список путей
            whitelist: список расширений файлов, для которых нужно сохранять содержимое
                      (например, ['.py', '.txt', '.md'])
        """
        self.ROOT_PATH = '.'
        self.whitelist = set(whitelist) if whitelist else set()
        self.dict = {self.ROOT_PATH: []}
        self.file_contents = {}  # Словарь для хранения содержимого файлов
        
        # Обрабатываем входные данные
        for item in files_data:
            if isinstance(item, tuple):
                file_path, content = item
            else:
                file_path = item
                content = None
            
            splitted = file_path.split('/')
            
            # Строим структуру директорий
            for i in reversed(range(1, len(splitted))):
                parent = splitted[i - 1]
                child = splitted[i]
                if parent not in self.dict:
                    self.dict[parent] = []
                if child not in self.dict[parent]:
                    self.dict[parent].append(child)
            
            if splitted[0] not in self.dict[self.ROOT_PATH]:
                self.dict[self.ROOT_PATH].append(splitted[0])
            
            # Сохраняем содержимое файла, если его расширение в whitelist
            if content is not None:
                file_ext = '.' + file_path.split('.')[-1] if '.' in file_path.split('/')[-1] else ''
                if file_ext in self.whitelist:
                    self.file_contents[file_path] = content

        # Сортируем детей: сначала директории, потом файлы (оба в алфавитном порядке)
        for key in self.dict:
            children = self.dict[key]
            dirs = [child for child in children if child in self.dict]
            files = [child for child in children if child not in self.dict]
            self.dict[key] = sorted(dirs) + sorted(files)

    def __str__(self):
        """Возвращает строковое представление структуры директорий в виде дерева"""
        lines = []
        
        def build_tree(path, prefix='', is_last=True):
            connector = '└── ' if is_last else '├── '
            extension = '    ' if is_last else '│   '
            
            name = path if path == self.ROOT_PATH else path.split('/')[-1]
            
            if path == self.ROOT_PATH:
                lines.append('.')
            else:
                lines.append(f'{prefix}{connector}{name}')
            
            if path in self.dict:
                children = self.dict[path]
                for i, child in enumerate(children):
                    is_last_child = (i == len(children) - 1)
                    if path == self.ROOT_PATH:
                        child_path = child
                    else:
                        child_path = f'{path}/{child}'
                    
                    new_prefix = prefix + extension if path != self.ROOT_PATH else ''
                    build_tree(child_path, new_prefix, is_last_child)
        
        build_tree(self.ROOT_PATH)
        return "<folder_structure>\n" + '\n'.join(lines) + "\n</folder_structure>"

    def __repr__(self):
        """Возвращает строковое представление для отладки"""
        return self.__str__()
    
    def print_file_content(self, file_path):
        """
        Выводит содержимое одного файла в форматированном виде.
        
        Args:
            file_path: путь к файлу от корня проекта
        """
        if file_path in self.file_contents:
            print(f"<file name={file_path}>")
            print(self.file_contents[file_path])
            print("</file>")
    
    def print_files_content(self):
        """
        Выводит содержимое всех сохраненных файлов в форматированном виде.
        """
        if not self.file_contents:
            print("Нет сохраненных файлов")
            return
        
        for file_path in sorted(self.file_contents.keys()):
            self.print_file_content(file_path)
            print()  # Пустая строка между файлами

    def get_file_content(self, file_path):
        """
        Возвращает сохраненное содержимое файла в виде строки в формате
        <file name={file_path}>
        {file_content}
        </file>\n
        """
        return f"{file_path}\n{'=' * 40}\n{self.file_contents[file_path]}\n{'=' * 40}\n"
    
    def get_files_content(self):
        """
        Возвращает сохраненное содержимое всех файлов в виде строки в формате
        <file name={file_path}>
        {file_content}
        </file>\n
        ...
        """
        return '\n'.join([self.get_file_content(file_path) for file_path in self.file_contents.keys()])