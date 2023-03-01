from typing import Union

from color import Color, check_if_color


class BaseTextContainer(list):
    @property
    def len(self):
        _len_count = 0
        for i_ in self:
            _len_count += len(i_)
        return _len_count

    def __and__(self, other):
        self.append(other)

    def __repr__(self):
        return f'BaseTextContainer({list(self)})'


class ColorText:
    def _set_color(self, color):
        self.color = Color(color)

    def __init__(self, text: str, color: Union[str, tuple] = 'black'):
        self._check_color = check_if_color
        if not self._check_color(color):
            print(f'Color: {color}\n' f'Type: {str(type(color))}')

        # assert self._check_color(color)
        self._set_color(color)
        self.text = text

    def __len__(self):
        return len(self.text)

    def __repr__(self):
        return f'ColorText(\'{self.text}\', {self.color})'

    def __str__(self):
        return self.text

    def __format__(self, format_spec):
        return self.__repr__()

    def __lshift__(self, other):
        self._set_color(other)

    def __getitem__(self, index):
        return ColorText(self.text[index], color=self.color)


class ColorTextGroup(BaseTextContainer):
    def __init__(self, texts=None):
        if texts is None:
            texts = []
        super().__init__(texts)

    def append(self, text):
        if isinstance(text, (str, ColorText)):
            super().append(text)
        else:
            raise TypeError('The text parameter is neither str nor ColorText')


class TextBuffer(BaseTextContainer):
    def __init__(self, seq, length: int):
        super().__init__(seq)
        self.max_length = length

    @property
    def free_size(self):
        return self.max_length - self.len


def split_ep(
    text: Union[str, ColorText], length: int, pre_len: int = 0
):  # Cut strings by length but discard the first N characters
    # https://github.com/PyCQA/pycodestyle/issues/373
    return text[:pre_len], [
        text[i : i + length] for i in range(pre_len, len(text), length)  # noqa
    ]


def split_ctg(
    group: Union[list, ColorTextGroup], length: int
) -> list:  # Cut strings from ColorTextGroup
    result = []
    buffer = TextBuffer([], length)

    if isinstance(group, list):
        group = ColorTextGroup(group)
    for t in group:
        if len(t) <= buffer.free_size:
            # buffer & t
            continue
        if len(t) > buffer.free_size:
            _long_text_result = split_ep(t, length, buffer.free_size)
            # buffer & _long_text_result[0]
            result.append(buffer.copy())
            buffer.clear()
            if len(_long_text_result[1][-1]) < length:
                buffer = TextBuffer(_long_text_result[1][-1:], length)
                result.append(_long_text_result[1][:-1])
            else:
                result.append(_long_text_result[1])
        if buffer.free_size == 0:
            result.append(buffer.copy())
            buffer.clear()

    return result


if __name__ == '__main__':
    from pprint import pformat

    from colorama import Fore, Style

    def test_ctg(length: int, *params):
        print(
            f'{Fore.GREEN}> running split_ctg(){Style.RESET_ALL}\
            \n    length: {length}\
            \n    texts: {params}'
        )
        groups_ = ColorTextGroup(list(params))
        f_ = pformat(split_ctg(groups_, length)).split('\n')
        print(Fore.CYAN, '\t', f_[0], '\n\t'.join(f_[0:]))

    print('*** ColorTextGroup cutting test ***')
    test_ctg(
        5,
        'test',
        ColorText('i am red', 'red'),
        'foo',
        ColorText('bar', color='cyan'),
    )
    test_ctg(
        10,
        '获得',
        ColorText('12%/15%/18%/21%/24%', color='rgb(69,113,236)'),
        '所有元素伤害加成；队伍中附近的其他角色在施放元素战技时，'
        '会为装备该武器的角色产生1层「波穗」效果，至多叠加2层，'
        '每0.3秒最多触发1次。装备该武器的角色施放元素战技时，'
        '如果有积累的「波穗」效果，则将消耗已有的「波穗」，'
        '获得「波乱」：根据消耗的层数，每层提升',
        ColorText('20%/25%/30%/35%/40%', (69, 113, 236)),
        '普通攻击伤害，持续8秒。',
    )
