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
1. 书本为本：所有分析必须以所提供的《{book_title}》原文为依据进行阐释与印证，优先从中寻找相关论述与理法。
2. 明确出处：引用原文或对应篇目论述时，请明确标注出处（例如“据《{book_title}·天干》”）；若原文文本中未显式标注某章名或某句出自何篇，不得自行臆造或补全篇名。
3. 严守边界：若原文无直接依据，请明确说明该部分属于命理推理或一般实务经验，而非《{book_title}》原典引文；切勿捏造引文、章节名称或原典中不存在的内容。
4. 实事求是：若原文证据不足或命盘信息存在歧义，请如实说明，不必强行下定论。
5. 语言规范：所有面向用户的分析内容均使用中文呈现。

分析输出要求（请按以下结构清晰呈现）：
1. 八字五行与十神：列出年柱、月柱、日柱、时柱对应的天干、地支五行，以及各干支相对日主（日干）的十神（并简述日主强弱与季节/月令背景）。
2. 地支及干支互动关系：列出命局中存在的合（如六合、三合、暗合等及是否成化）、会（如三会方局）、冲、刑、害、破等关系，并说明其对命局的影响及在所提供典籍中的对应理法依据。
3. 格局分析：结合月令、十神配置以及上述合（化）、会、冲、刑、害、破等互动关系，分析命局的格局成立与否、成格或破格/变格情况，并说明依据。
4. 喜用神分析：综合日主旺衰、寒暖燥湿、调候与通关需求，以及格局与干支刑冲合会的影响，分析喜神与用神（及忌神方向），并注明哪些属于书中有据、哪些属于推演。
5. 综合评价：给出整体命局综合评价，总结核心优势、潜在风险或制约因素，并再次明确原典依据与推理边界。\
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
