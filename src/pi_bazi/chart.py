"""
Core data structures and validation for Bazi four pillars (四柱八字).

Users provide the four pillars directly. No birth date conversion is performed.
"""

from dataclasses import dataclass

# The 10 Heavenly Stems (天干) in cycle order
HEAVENLY_STEMS: tuple[str, ...] = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")

# The 12 Earthly Branches (地支) in cycle order
EARTHLY_BRANCHES: tuple[str, ...] = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")

# The 60 valid stem-branch combinations (六十甲子).
# A combination is valid when stem index and branch index share the same parity
# (both even or both odd), reflecting the yin-yang pairing rule.
VALID_PILLARS: frozenset[tuple[str, str]] = frozenset(
    (stem, branch)
    for i, stem in enumerate(HEAVENLY_STEMS)
    for j, branch in enumerate(EARTHLY_BRANCHES)
    if i % 2 == j % 2
)

# Accepted gender input values mapped to canonical form
_GENDER_MAP: dict[str, str] = {
    "male": "male",
    "female": "female",
    "男": "male",
    "女": "female",
}


@dataclass(frozen=True)
class Pillar:
    """A single Bazi pillar consisting of one Heavenly Stem and one Earthly Branch."""

    stem: str
    branch: str

    def __post_init__(self) -> None:
        if self.stem not in HEAVENLY_STEMS:
            raise ValueError(
                f"Invalid Heavenly Stem: '{self.stem}'. Must be one of {HEAVENLY_STEMS}."
            )
        if self.branch not in EARTHLY_BRANCHES:
            raise ValueError(
                f"Invalid Earthly Branch: '{self.branch}'. Must be one of {EARTHLY_BRANCHES}."
            )
        if (self.stem, self.branch) not in VALID_PILLARS:
            raise ValueError(
                f"Invalid pillar combination: '{self.stem}{self.branch}'. "
                f"Stem and branch must share the same yin-yang parity (六十甲子 rule)."
            )

    @classmethod
    def from_str(cls, text: str) -> "Pillar":
        """Parse a two-character pillar string such as '甲子' into a Pillar."""
        text = text.strip()
        if len(text) != 2:
            raise ValueError(
                f"Pillar string must be exactly 2 characters (stem + branch), got: '{text}'."
            )
        return cls(stem=text[0], branch=text[1])

    def __str__(self) -> str:
        return f"{self.stem}{self.branch}"


@dataclass
class BaziChart:
    """The four pillars (四柱) of a Bazi chart together with the person's gender."""

    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar
    gender: str  # canonical: "male" or "female"

    def __post_init__(self) -> None:
        if self.gender not in ("male", "female"):
            raise ValueError(
                f"Invalid gender: '{self.gender}'. Must be 'male' or 'female'."
            )

    @classmethod
    def from_strings(
        cls,
        year: str,
        month: str,
        day: str,
        hour: str,
        gender: str,
    ) -> "BaziChart":
        """
        Create a BaziChart from four pillar strings and a gender string.

        Args:
            year:   Year pillar, e.g. '甲子'
            month:  Month pillar, e.g. '丙寅'
            day:    Day pillar, e.g. '戊午'
            hour:   Hour pillar, e.g. '庚申'
            gender: '男', '女', 'male', or 'female'

        Returns:
            A validated BaziChart instance.
        """
        canonical_gender = _GENDER_MAP.get(gender.strip())
        if canonical_gender is None:
            raise ValueError(
                f"Invalid gender: '{gender}'. "
                f"Accepted values: 'male', 'female', '男', '女'."
            )
        return cls(
            year=Pillar.from_str(year),
            month=Pillar.from_str(month),
            day=Pillar.from_str(day),
            hour=Pillar.from_str(hour),
            gender=canonical_gender,
        )

    def __str__(self) -> str:
        return (
            f"年柱: {self.year}  月柱: {self.month}  "
            f"日柱: {self.day}  时柱: {self.hour}  "
            f"性别: {'男' if self.gender == 'male' else '女'}"
        )
