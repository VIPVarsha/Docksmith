import hashlib

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def sha256_file(path):
    with open(path, "rb") as f:
        return sha256_bytes(f.read())