from util import BackendPath

class Logger:
    def __init__(self, relative_file_path):
        if relative_file_path:
            self.file_path = BackendPath(f'{relative_file_path}')
        else:
            self.file_path = None

    def log(self, message):
        raise NotImplementedError()

class SimpleLogger(Logger):
    def __init__(self, relative_file_path=None):
        super().__init__(relative_file_path)

    def log(self, message):
        print(message)
        if self.file_path:
            with open(self.file_path, 'a') as f:
                f.write(message + '\n')

class TestingLogger(Logger):
    def __init__(self, relative_file_path='tests/output/log.txt'):
        super().__init__(relative_file_path)
        with open(self.file_path, 'w') as f:
            f.write('')

    def log(self, message):
        with open(self.file_path, 'a') as f:
            f.write(message + '\n')
class OtherLogger(Logger):
    pass