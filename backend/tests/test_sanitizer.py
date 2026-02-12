from app.core.sanitizer import sanitize_question


def test_sanitize_phone_local():
    text = "رقمي 0551234567"
    sanitized, detected, types_ = sanitize_question(text)
    assert detected is True
    assert "phone" in types_
    assert "***" in sanitized


def test_sanitize_phone_international():
    text = "اتصل على +966512345678"
    sanitized, detected, types_ = sanitize_question(text)
    assert detected is True
    assert "phone" in types_
    assert "***" in sanitized


def test_sanitize_iban():
    text = "IBAN SA03123456789012345678"
    sanitized, detected, types_ = sanitize_question(text)
    assert detected is True
    assert "iban" in types_
    assert "***" in sanitized


def test_sanitize_card_like():
    text = "رقم البطاقة 4111111111111111"
    sanitized, detected, types_ = sanitize_question(text)
    assert detected is True
    assert "card" in types_
    assert "***" in sanitized


def test_sanitize_national_id():
    text = "رقم الهوية 1023456789"
    sanitized, detected, types_ = sanitize_question(text)
    assert detected is True
    assert "national_id" in types_
    assert "***" in sanitized


def test_no_pii():
    text = "كيف أغير الباقة؟"
    sanitized, detected, types_ = sanitize_question(text)
    assert detected is False
    assert types_ == []
    assert sanitized == text
