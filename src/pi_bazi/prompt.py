"""
Prompt builder for the Bazi analysis assistant.

Produces a PromptParts object containing:
  - system_instruction: role definition, full book text, and analysis rules.
    This maps directly to Gemini's system_instruction parameter.
  - user_message: the user's Bazi chart and the analysis request.
    This maps to the first user turn in Gemini's contents parameter.

Keeping these two parts separate makes it easy to iterate on wording
independently and aligns with how explicit context caching works on paid tiers.
"""

from dataclasses import dataclass

from pi_bazi.book import BookSource
from pi_bazi.chart import BaziChart

# ---------------------------------------------------------------------------
# System instruction template
# ---------------------------------------------------------------------------

_SYSTEM_INSTRUCTION_TEMPLATE = """\
你是一位专业的八字命理分析师，以古典命理典籍为知识依据。

以下是《{book_title}》原文，作为你的核心知识来源：

===== 《{book_title}》原文开始 =====
{book_text}
===== 《{book_title}》原文结束 =====

分析规则：
1. 以上述原典为主要依据进行分析，优先从中寻找相关论述。
2. 引用原文时，请明确标注出处，例如"据《滴天髓·天干》"。
3. 若原文无直接依据，请明确说明该内容属于命理推理或一般经验，而非原典引文。
4. 切勿捏造引文、章节名称或原典中不存在的内容。
5. 若证据不足，请如实说明，不必强行给出结论。
6. 所有面向用户的分析内容均使用中文呈现。\
"""

# ---------------------------------------------------------------------------
# User message template
# ---------------------------------------------------------------------------

_USER_MESSAGE_TEMPLATE = """\
请根据以下八字命盘进行分析：

年柱：{year}
月柱：{month}
日柱：{day}
时柱：{hour}
性别：{gender}

请提供以下内容：
1. 日主五行属性及强弱
2. 格局判断与用神分析
3. 结合《{book_title}》相关论述，对此命盘作综合评析
4. 如有不确定之处，请明确说明\
"""

# ---------------------------------------------------------------------------
# PromptParts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PromptParts:
    """
    The two parts of a Gemini prompt.

    system_instruction: passed as the system_instruction parameter to Gemini.
    user_message:       passed as the user turn in Gemini's contents parameter.
    """

    system_instruction: str
    user_message: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_prompt(chart: BaziChart, book: BookSource) -> PromptParts:
    """
    Build a PromptParts from a validated BaziChart and a loaded BookSource.

    Args:
        chart: A validated BaziChart (four pillars + gender).
        book:  A loaded BookSource (full classical text).

    Returns:
        A PromptParts ready to be sent to the LLM.
    """
    system_instruction = _SYSTEM_INSTRUCTION_TEMPLATE.format(
        book_title=book.title,
        book_text=book.text,
    )

    user_message = _USER_MESSAGE_TEMPLATE.format(
        year=str(chart.year),
        month=str(chart.month),
        day=str(chart.day),
        hour=str(chart.hour),
        gender="男" if chart.gender == "male" else "女",
        book_title=book.title,
    )

    return PromptParts(
        system_instruction=system_instruction,
        user_message=user_message,
    )
