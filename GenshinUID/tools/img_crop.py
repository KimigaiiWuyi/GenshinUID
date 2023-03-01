from pathlib import Path

from PIL import Image

target = Path(__file__).parent / 'support'
img = Path(__file__).parent / '图.png'
image = Image.open(img)
# 设置要裁剪的图块的宽度和高度
width = 1750
height = 1045

# 设置要裁剪的图块的位置
positions = [
    (120 + width * x, 11540 + height * y) for x in range(2) for y in range(1)
]

# 循环裁剪每个图块
for i, position in enumerate(positions):
    # 获取起始位置
    x, y = position

    # 裁剪图片
    cropped_image = image.crop((x, y, x + width, y + height))

    # 保存裁剪后的图片
    cropped_image.save(target / "cropped_image_{}.png".format(i + 1))
