import hashlib

def sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()

def bcrypt(data):
    pass
    hashlib.algorithms_available