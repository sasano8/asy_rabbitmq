from typing import Callable, TypeVar

from fastapi_di import DI
from fastapi_di import Task as TaskBase

from .caller import CallInfo

F = TypeVar("F", bound=Callable)


class Task(TaskBase[F]):
    def depends_consumer(self, consumer: "Consumer") -> None:
        self.consumer = consumer

    @property
    def delay(self) -> F:
        return self._delay  # type: ignore

    def _delay(self, **kwargs) -> None:
        task = CallInfo(func=self.__name__, kwargs=kwargs)
        result = self.consumer.basic_publish(task)
        return result


class RabbitmqDI(DI):
    __task_class__ = Task
