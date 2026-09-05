import pytest
import hashlib
import base64
import json


def test_hash_md5():
    result = hashlib.md5(b"hello").hexdigest()
    assert result == "5d41402abc4b2a76b9719d911017c592"


def test_hash_sha256():
    result = hashlib.sha256(b"test").hexdigest()
    assert result == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"


def test_base64_roundtrip():
    original = "Hello, AUTOMAT!"
    encoded = base64.b64encode(original.encode()).decode()
    decoded = base64.b64decode(encoded).decode()
    assert decoded == original


def test_json_roundtrip():
    data = {"name": "Тест", "items": [1, 2, 3]}
    dumped = json.dumps(data, ensure_ascii=False)
    loaded = json.loads(dumped)
    assert loaded == data
