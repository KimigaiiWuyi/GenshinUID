from enum import Enum
from typing import Tuple, Union

from PIL import ImageColor


class ColorCodes(Enum):
    HEX = 'hex'
    RGB = 'rgb'
    HSV = 'hsv'


class ConvertableColor:
    def __init__(self, v_color: tuple):
        self.v_color = v_color

    def __call__(self, space):
        if space == ColorCodes.HEX:
            return self.hex
        elif space == ColorCodes.RGB:
            return self.rgb
        elif space == ColorCodes.HSV:
            return self.hsv
        else:
            raise ValueError('Invalid color-code type')

    @property
    def hex(self):
        if len(self.v_color) == 3:
            r, g, b = self.v_color
            return f'#{r:02x}{g:02x}{b:02x}'
        elif len(self.v_color) == 4:
            r, g, b, a = self.v_color
            return f'#{r:02x}{g:02x}{b:02x}{a:02x}'
        else:
            raise ValueError('Invalid color value')

    @property
    def rgb(self):
        if len(self.v_color) == 3:
            r, g, b = self.v_color
            return f'rgb({r}, {g}, {b})'
        elif len(self.v_color) == 4:
            r, g, b, a = self.v_color
            return f'rgba({r}, {g}, {b}, {a})'
        else:
            raise ValueError('Invalid color value')

    @property
    def hsv(self):
        r, g, b = self.v_color[:3]
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx - mn
        if mx == mn:
            h = 0
        elif mx == r:
            h = (60 * ((g - b) / df) + 360) % 360
        elif mx == g:
            h = (60 * ((b - r) / df) + 120) % 360
        elif mx == b:
            h = (60 * ((r - g) / df) + 240) % 360
        else:
            h = 360

        if mx == 0:
            s = 0
        else:
            s = df / mx
        v = mx
        return f'hsv({h}, {s}, {v})'


class Color(tuple):
    @property
    def to(self):
        return ConvertableColor(self)

    def __new__(
        cls,
        _color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]],
    ):
        assert check_if_color(_color)
        if isinstance(_color, str):
            _color = ImageColor.getrgb(_color)
        return super().__new__(cls, _color)

    def __str__(self):
        return self.to.hex

    def __repr__(self):
        return f"Color('{self.to.rgb}')"

    def __setitem__(self, key, value):
        if 0 <= value <= 255:
            super().__setitem__(key, value)  # type: ignore
        else:
            raise ValueError("Color value must be between 0 and 255")


def check_if_color(color: Union[str, tuple]):
    if isinstance(color, str):
        try:
            return ImageColor.getrgb(color)
        except ValueError:
            return False
    if isinstance(color, (tuple, Color)):
        if len(color) <= 4:
            return all(isinstance(d, int) and 0 <= d <= 255 for d in color)
    return False


if __name__ == '__main__':
    red = Color((1, 1, 1))
    print(f'HEX: {red.to.hex}\nHSV: {red.to.hsv}\nRGB: {red.to.rgb}')
    print(
        f'rgb(123, 23, -1) \
        {check_if_color("rgb(123, 23, -1)")}\
        \n(100, 200, 255): \
        {check_if_color((100, 200, 256))}'
    )
    print(check_if_color('#ff0000'))
