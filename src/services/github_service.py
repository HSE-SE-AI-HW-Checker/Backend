import requests
import urllib.parse
from src.services.file_processor import FolderStructure

class GitHubRepoExplorer:
    # TODO: implement config support
    def __init__(self, token=None, whitelist=None):
        """
        Инициализирует GitHubRepoExplorer.
        
        Args:
            token: токен GitHub для авторизации
            whitelist: список расширений файлов, содержимое которых нужно сохранять
                      (например, ['.py', '.txt', '.md'])
        """
        self.token = token
        self.headers = {
            "Authorization": f"token {self.token}" if self.token else None,
            "Accept": "application/vnd.github.v3+json"
        }
        self.whitelist = whitelist if whitelist else ['.py', '.txt', '.md', '.json', '.yaml', '.yml']

    def get_repo_contents(self, repo_url):
        """
        Принимает URL репозитория GitHub (например, https://github.com/user/repo)
        Возвращает структуру и содержимое файлов.
        """
        # Извлекаем owner и repo из URL
        parsed = urllib.parse.urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError("Некорректный URL репозитория GitHub")

        owner, repo = path_parts[0], path_parts[1]

        base_url = f"https://api.github.com/repos/{owner}/{repo}/contents/"

        return self._fetch_contents(base_url, owner, repo)

    def _fetch_contents(self, url, owner, repo, path=""):
        """
        Рекурсивно получает содержимое репозитория.
        
        Returns:
            FolderStructure с путями и содержимым файлов
        """
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 404:
            raise Exception("Не удалось получить содержимое репозитория. Проверьте ссылку на наличие ошибок и убедитесь, что репозиторий публичный.")
        if response.status_code != 200:
            raise Exception(f"Ошибка GitHub API: {response.status_code} — {response.text}")

        items = response.json()
        files_data = []

        for item in items:
            item_path = item['path']
            
            if item["type"] == "file":
                # Проверяем, нужно ли сохранять содержимое файла
                file_ext = '.' + item_path.split('.')[-1] if '.' in item_path.split('/')[-1] else ''
                
                if file_ext in self.whitelist:
                    # Получаем содержимое файла
                    file_content = self._get_file_content(item["download_url"])
                    files_data.append((item_path, file_content))
                else:
                    # Добавляем только путь без содержимого
                    files_data.append((item_path, None))
                    
            elif item["type"] == "dir":
                # Рекурсивно получаем содержимое директории
                dir_url = item["url"]
                subdir_structure = self._fetch_contents(dir_url, owner, repo, item_path)
                # Добавляем файлы из поддиректории
                files_data.extend(subdir_structure)

        # Если это корневой вызов, создаем FolderStructure
        if path == "":
            return FolderStructure(files_data, whitelist=self.whitelist)
        else:
            # Для рекурсивных вызовов возвращаем список файлов
            return files_data

    def _get_file_content(self, download_url):
        """
        Получает содержимое файла по URL.
        
        Args:
            download_url: URL для скачивания файла
            
        Returns:
            Содержимое файла в виде строки
        """
        try:
            response = requests.get(download_url, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                return f"[Ошибка при чтении файла: {response.status_code}]"
        except Exception as e:
            return f"[Ошибка при чтении файла: {str(e)}]"



if __name__ == "__main__":
    # Ваш токен GitHub (можно оставить None для публичных репозиториев, но с лимитами)
    TOKEN = "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"  # замените или оставьте None

    # Указываем расширения файлов, содержимое которых нужно сохранить
    WHITELIST = ['.py', '.md', '.txt', '.json', '.yaml', '.yml', '.sty']

    explorer = GitHubRepoExplorer(token=TOKEN, whitelist=WHITELIST)

    try:
        repo_url = "https://github.com/BaGGeRTeaMYT/HSE-FCS-SE-231-lessons"  # пример публичного репозитория
        structure = explorer.get_repo_contents(repo_url)

        # Выводим структуру директорий
        print("Структура репозитория:")
        print(structure)
        print("\n" + "="*50 + "\n")
        
        # Выводим содержимое файлов
        print("Содержимое файлов:")
        structure.print_files_content()

    except Exception as e:
        print("Ошибка:", e)
