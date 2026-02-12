from app.core.router import route


def test_route_billing_arabic():
    category, risk = route("عندي مشكلة في الفاتورة", None)
    assert category == "billing"
    assert risk == "medium"


def test_route_network_english():
    category, risk = route("Network coverage is weak", None)
    assert category == "network"
    assert risk == "low"


def test_route_plans_arabic():
    category, risk = route("أريد تغيير الباقة", None)
    assert category == "plans"
    assert risk == "low"


def test_route_roaming_arabic():
    category, risk = route("مشكلة في التجوال", None)
    assert category == "roaming"
    assert risk == "low"


def test_route_porting_arabic():
    category, risk = route("أبغى نقل الرقم", None)
    assert category == "porting"
    assert risk == "low"


def test_route_ownership_arabic():
    category, risk = route("طلب نقل ملكية", None)
    assert category == "ownership"
    assert risk == "low"


def test_route_complaints_arabic():
    category, risk = route("أريد تقديم شكوى", None)
    assert category == "complaints"
    assert risk == "medium"


def test_route_app_login():
    category, risk = route("لا يصلني رمز OTP", None)
    assert category == "app_login"
    assert risk == "low"


def test_route_auto_escalate_legal():
    category, risk = route("أحتاج استشارة قانونية", None)
    assert category == "legal"
    assert risk == "high"
