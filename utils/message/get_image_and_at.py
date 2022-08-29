from typing import Union

from hoshino.typing import List, CQEvent, Iterable


# https://v2.nonebot.dev/docs/advanced/di/dependency-injection#class-%E4%BD%9C%E4%B8%BA%E4%BE%9D%E8%B5%96
class ImageAndAt:
    def __init__(self, event: CQEvent):
        self.images = []
        self.at = []
        for i in event.message:
            if i.type == "image":
                data = i.data
                if url := data.get("url"):
                    self.images.append(url)
                else:
                    continue
            elif i.type == "at":
                self.at.append(i.data["qq"])

    def get_at(self):
        return self.at

    def get_image(self):
        return self.images

    def get_first_image(self) -> Union[str, None]:
        try:
            return self.images[0]
        except IndexError:
            return None

    def get_first_at(self) -> Union[int, None]:
        try:
            return self.at[0]
        except IndexError:
            return None
