from typing import Optional

from nonebot.adapters.qqguild import MessageEvent


# https://v2.nonebot.dev/docs/advanced/di/dependency-injection#class-%E4%BD%9C%E4%B8%BA%E4%BE%9D%E8%B5%96
class ImageAndAt:
    def __init__(self, event: MessageEvent):
        self.images = []
        self.at = []
        for i in event.get_message():
            if i.type == "attachment":
                self.images.append(i.data["url"])
            elif i.type == "mention_user":
                self.at.append(i.data["user_id"])

    def get_at(self):
        return self.at

    def get_image(self):
        return self.images

    def get_first_image(self) -> Optional[str]:
        return self.images[0] if len(self.images) else None

    def get_first_at(self) -> Optional[str]:
        return self.at[0] if len(self.at) else None
