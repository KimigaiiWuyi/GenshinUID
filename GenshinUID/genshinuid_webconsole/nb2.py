from typing import TypeVar, Callable

T_Wrapped = TypeVar("T_Wrapped", bound=Callable)


def overrides(InterfaceClass: object) -> Callable[[T_Wrapped], T_Wrapped]:
    """标记一个方法为父类 interface 的 implement"""

    def overrider(func: T_Wrapped) -> T_Wrapped:
        assert func.__name__ in dir(
            InterfaceClass
        ), f"Error method: {func.__name__}"
        return func

    return overrider
