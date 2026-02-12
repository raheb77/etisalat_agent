from typing import List, Tuple

from app.services.facts import FactHit
from app.services.retrieval import ContextChunk


def _summarize_facts(facts: List[FactHit]) -> str:
    lines = []
    for fact in facts:
        if fact.values:
            lines.append(f"- {fact.statement} (القيم: {fact.values})")
        else:
            lines.append(f"- {fact.statement}")
    return "\n".join(lines)


def generate_answer(
    question: str, facts: List[FactHit], contexts: List[ContextChunk], locale: str
) -> Tuple[str, List[str]]:
    if facts:
        answer = "استناداً إلى الحقائق المتاحة:\n" + _summarize_facts(facts)
        steps = [
            "تحقق من مطابقة الاستفسار مع الحقائق المعروضة.",
            "قدّم الإجابة للعميل بصياغة واضحة ومباشرة.",
            "إذا احتاج العميل تفصيلاً إضافياً، ارجع للمستندات الداعمة.",
        ]
        return answer, steps

    answer = "لا تتوفر أدلة كافية للإجابة حالياً. يُرجى تحويل الطلب للجهة المختصة."
    steps = [
        "أبلغ العميل بعدم توفر أدلة كافية للرد.",
        "حوّل الحالة للقسم المختص مع ملخص مختصر.",
        "سجّل سبب التحويل ضمن الحوكمة.",
    ]
    return answer, steps
