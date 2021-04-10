from typing import Callable, Generic, Protocol, TypeVar
import functools

T = TypeVar("T")
F = TypeVar("F", bound=Callable, covariant=True)


class PExtender(Protocol[T]):
    __root__: T


class PFuncWrapper(Protocol[F]):
    @property
    def __call__(self) -> F:
        ...


T = TypeVar("T")


class Extender(PExtender[T]):
    """ある型の拡張機能群であることを表現するクラス"""

    __root__: T

    def __init__(self, __root__: T):
        self.__root__ = __root__


class Delegator(Extender[T]):
    """委任を表現するクラス"""

    def __getattr__(self, name):
        attr = getattr(self.__root__, name)
        return attr


class FuncMimicry(Delegator[F], PFuncWrapper[F]):
    """関数をラップし、その関数に擬態します。擬態しているため、メタプログラミングなどをすると想定外の結果を返すことがあります。
    例えば、__class__は自身のクラスでなく、functionを返します。
    """

    def __init__(self, func: F) -> None:
        super().__init__(func)
        functools.update_wrapper(self, func)
        self.__code__ = func.__code__
        self.__defaults__ = func.__defaults__  # type: ignore
        self.__kwdefaults__ = func.__kwdefaults__  # type: ignore

    @property
    def __call__(self) -> F:
        return self.__wrapped__

    @property  # type: ignore
    def __class__(self):
        return self.__wrapped__.__class__
