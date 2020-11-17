import hashlib


def hash_bytes(s: (str, bytes)) -> bytes:
    if isinstance(s, str):
        s = s.encode(encoding='utf8')
    return hashlib.md5(s).digest()


def hash_str(s: (str, bytes)) -> str:
    if isinstance(s, str):
        s = s.encode(encoding='utf8')
    return hashlib.md5(s).hexdigest()
