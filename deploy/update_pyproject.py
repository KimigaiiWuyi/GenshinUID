from typing import List

import tomlkit


def main():
    with open("./nb2/pyproject.toml", "r", encoding="utf-8") as f:
        data = tomlkit.load(f)
        plugins: List[str] = data["tool"]["nonebot"]["plugins"]  # type: ignore
        if "GenshinUID" in plugins:
            return
        plugins.append("GenshinUID")

    with open("./nb2/pyproject.toml", "w", encoding="utf-8") as f:
        tomlkit.dump(data, f)

    print("Update pyproject.toml done.")


if __name__ == "__main__":
    main()
