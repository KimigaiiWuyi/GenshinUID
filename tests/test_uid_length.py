from __future__ import annotations

from GenshinUID.utils.convert import is_genshin_uid, split_uid_from_text


def test_uid_accepts_nine_or_ten_digits() -> None:
    assert is_genshin_uid("123456789")
    assert is_genshin_uid("1234567890")


def test_uid_rejects_other_lengths() -> None:
    assert not is_genshin_uid("12345678")
    assert not is_genshin_uid("12345678901")
    assert not is_genshin_uid("")
    assert not is_genshin_uid("123456789a")


def test_split_keeps_full_ten_digit_uid() -> None:
    uid, rest = split_uid_from_text("查1234567890面板")
    assert uid == "1234567890"
    assert rest == "查面板"


def test_split_keeps_nine_digit_uid_and_name() -> None:
    uid, rest = split_uid_from_text("123456789 胡桃")
    assert uid == "123456789"
    assert rest == " 胡桃"


def test_split_does_not_truncate_longer_digit_run() -> None:
    uid, rest = split_uid_from_text("12345678901")
    assert uid is None
    assert rest == "12345678901"


def test_split_removes_same_uid_without_eating_a_longer_one() -> None:
    uid, rest = split_uid_from_text("123456789 胡桃 123456789 1234567890")
    assert uid == "123456789"
    assert rest == " 胡桃  1234567890"
