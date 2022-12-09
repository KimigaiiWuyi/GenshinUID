from pathlib import Path
from typing import Optional

from ..utils.alias.alias_to_char_name import alias_to_char_name

CARD_PATH = Path(__file__).parent / 'card'

CARD_DATA = {i.name[:-4]: i for i in CARD_PATH.rglob('*.jpg')}


async def get_gs_card(msg: str) -> Optional[bytes]:
    if not msg:
        return None
    msg = await alias_to_char_name(msg)
    if msg in CARD_DATA:
        img = CARD_DATA[msg]
    else:
        for filename in CARD_DATA:
            similarity = len(set(msg) & set(filename))
            if similarity >= 2:
                img = CARD_DATA[filename]
                break
        else:
            return None

    with open(img, 'rb') as f:
        return f.read()
