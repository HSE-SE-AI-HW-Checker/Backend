import requests
import urllib.parse

class GitHubRepoExplorer:
    # TODO: implement config support
    def __init__(self, token=None):
        self.token = token
        self.headers = {
            "Authorization": f"!token {self.token}" if self.token else None,
            "Accept": "application/vnd.github.v3+json"
        }

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
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 404:
            raise Exception("Репозиторий не найден или недоступен.")
        if response.status_code != 200:
            raise Exception(f"Ошибка GitHub API: {response.status_code} — {response.text}")

        items = response.json()
        result = {
            "path": path,
            "type": "directory",
            "children": []
        }

        for item in items:
            item_data = {
                "name": item["name"],
                "path": item["path"],
                "type": item["type"]
            }

            if item["type"] == "file":
                # Получаем содержимое файла
                file_content = self._get_file_content(item["download_url"])
                item_data["content"] = file_content
            elif item["type"] == "dir":
                # Рекурсивно получаем содержимое директории
                dir_url = item["url"]
                item_data["children"] = self._fetch_contents(dir_url, owner, repo, item["path"])["children"]

            result["children"].append(item_data)

        return result

    def _get_file_content(self, download_url):
        response = requests.get(download_url)
        if response.status_code == 200:
            return response.text
        else:
            return f"[Ошибка при чтении файла: {response.status_code}]"



if __name__ == "__main__":
    # Ваш токен GitHub (можно оставить None для публичных репозиториев, но с лимитами)
    TOKEN = "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"  # замените или оставьте None

    explorer = GitHubRepoExplorer(token=TOKEN)

    try:
        repo_url = "https://github.com/BaGGeRTeaMYT/Consultation-code"  # пример публичного репозитория
        structure = explorer.get_repo_contents(repo_url)

        # Выводим структуру (можно сериализовать в JSON)
        import json
        print(json.dumps(structure, indent=2, ensure_ascii=False))

    except Exception as e:
        print("Ошибка:", e)
