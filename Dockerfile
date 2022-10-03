FROM python:3.9

# 1. 环境设置

# 使用镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple

RUN apt-get update && apt-get install -y tzdata

ENV TZ Asia/Shanghai

# 2. 安装 GenshinUID
WORKDIR /plugin

COPY ./pyproject.toml ./LICENSE ./README.md /plugin/

COPY ./GenshinUID /plugin/GenshinUID/

RUN pip install --editable "."

COPY ./.git /plugin/.git

# 3. 生成 nb2 项目
WORKDIR /nb2

RUN pip install tomlkit "cookiecutter>=2.1.1"

COPY ./deploy/cookiecutter.yml ./deploy/update_pyproject.py /nb2/

# RUN cookiecutter  --config-file ./cookiecutter.yml https://github.com/nonebot/nb-cli.git --directory="nb_cli/project" --no-input
# 使用镜像源
RUN cookiecutter  --config-file ./cookiecutter.yml https://ghproxy.com/https://github.com/nonebot/nb-cli.git --directory="nb_cli/project" --no-input

RUN python update_pyproject.py

COPY ./deploy/.env.dev /nb2/nb2/

WORKDIR /nb2/nb2

EXPOSE 8080


CMD python bot.py
