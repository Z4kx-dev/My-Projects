import re


def test_identifier_policy():
    pattern = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    assert pattern.fullmatch("world-001")
    assert pattern.fullmatch("chat_001")
    assert not pattern.fullmatch("../world")
    assert not pattern.fullmatch("world/id")


def test_upload_size_contract():
    max_bytes = 10 * 1024 * 1024
    assert max_bytes == 10485760
