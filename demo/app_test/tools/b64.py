import base64


def enc_bytes(s: (str, bytes)) -> bytes:
    if isinstance(s, str):
        s = s.encode(encoding='utf8')
    return base64.b64encode(s)


def enc_str(s: (str, bytes)) -> str:
    return enc_bytes(s).decode(encoding='utf8')


def dec_bytes(s: (str, bytes)) -> bytes:
    if isinstance(s, str):
        s = s.encode(encoding='utf8')
    return base64.b64decode(s)


def dec_str(s: (str, bytes)) -> str:
    return dec_bytes(s).decode(encoding='utf8')
