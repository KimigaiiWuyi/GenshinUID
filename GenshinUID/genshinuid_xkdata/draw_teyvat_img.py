from pathlib import Path

from PIL import Image

TEXT_PATH = Path(__file__).parent / "texture2d2"


def gen_char(char: Image.Image, char_star: int) -> Image.Image:
    char = char.resize((128, 128))
    char = char.convert("RGBA")
    char_bg = Image.open(TEXT_PATH / f"char{char_star}_bg.png")
    char_bg.paste(char, (11, 11), char)
    return char_bg
