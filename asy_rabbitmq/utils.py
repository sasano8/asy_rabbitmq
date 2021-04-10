import inspect
from fastapi.encoders import jsonable_encoder


def is_coroutine_callable(self):
    if inspect.iscoroutinefunction(self):
        return True

    # TODO: クラスの場合など検証が足りていない

    if func := getattr(self, "__call__", None):
        return inspect.iscoroutinefunction(func)
    else:
        return False
