class SimpleLogger:
    def __init__(self, file_name=None):
        self.file_name = file_name

    def log(self, message):
        print(message)
        if self.file_name:
            with open(self.file_name, 'a') as f:
                f.write(message + '\n')