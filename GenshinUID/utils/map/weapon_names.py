"""武器名解析。专武在 JSON 里只存「角色正式名专武」，昵称在这里展开。"""

import re
from typing import Dict

SIGNATURE_SUFFIX = "专武"


def _has_latin(text: str) -> bool:
    return any(("A" <= ch <= "Z") or ("a" <= ch <= "z") for ch in text)


def unique_char_name(label: str, char_aliases: Dict[str, list[str]]) -> str:
    """称呼只属于一个角色时返回正式名。英文别名不参与。"""
    if not label or _has_latin(label):
        return ""
    hits: list[str] = []
    if label in char_aliases:
        hits.append(label)
    for official, aliases in char_aliases.items():
        if label in aliases and official not in hits:
            hits.append(official)
    if len(hits) == 1:
        return hits[0]
    return ""


def expand_signature_aliases(
    aliases: list[str],
    char_aliases: Dict[str, list[str]],
) -> list[str]:
    """给注册用：正式名专武再加上该角色中文别名的「××专武」。"""
    expanded = list(aliases)
    for alias in aliases:
        if not alias.endswith(SIGNATURE_SUFFIX):
            continue
        character = alias[: -len(SIGNATURE_SUFFIX)]
        if character not in char_aliases:
            continue
        for nick in char_aliases[character]:
            if unique_char_name(nick, char_aliases) != character:
                continue
            formed = f"{nick}{SIGNATURE_SUFFIX}"
            if formed not in expanded:
                expanded.append(formed)
    return expanded


def resolve_weapon_name(
    weapon_name: str,
    weapon_aliases: Dict[str, list[str]],
    char_aliases: Dict[str, list[str]],
) -> str:
    """正式名、武器别名，或「角色别名专武」都收成武器正式名。"""
    if weapon_name in weapon_aliases:
        return weapon_name
    for weapon, aliases in weapon_aliases.items():
        if weapon_name in aliases:
            return weapon
    if weapon_name.endswith(SIGNATURE_SUFFIX):
        character = unique_char_name(weapon_name[: -len(SIGNATURE_SUFFIX)], char_aliases)
        if character:
            signature = f"{character}{SIGNATURE_SUFFIX}"
            for weapon, aliases in weapon_aliases.items():
                if signature in aliases:
                    return weapon
    return weapon_name


def expand_name_tokens(
    text: str,
    weapon_aliases: Dict[str, list[str]],
    char_aliases: Dict[str, list[str]],
) -> str:
    """把查询里的独立词收成武器或角色正式名。不切进更长的词。"""
    parts = [part for part in re.split(r"[\s,，、；;]+", text.strip()) if part]
    if not parts:
        return text
    out: list[str] = []
    for part in parts:
        weapon = resolve_weapon_name(part, weapon_aliases, char_aliases)
        if weapon != part:
            out.append(weapon)
            continue
        char = unique_char_name(part, char_aliases)
        out.append(char or part)
    return " ".join(out)
