import asyncio
import inspect

import asy_rabbitmq as rabbitmq
from asy_rabbitmq import Rabbitmq, Task


def test_behavior():
    def func1():
        return 1

    async def func2():
        return 2

    task1 = Task(func1)
    task2 = Task(func2)

    assert func1() == 1
    assert func1() == task1()

    assert not inspect.iscoroutine(func1)
    assert not inspect.iscoroutine(task1)

    assert inspect.iscoroutine(func2())
    assert inspect.iscoroutine(task2())

    assert asyncio.run(func2()) == 2
    assert asyncio.run(task2()) == 2

    assert task1.__name__ == "func1"
    assert task2.__name__ == "func2"

    assert task1.delay
    assert task2.delay


def test_decorator():
    rabbitmq = Rabbitmq(url="rabbitmq")
    consumer = rabbitmq.consumer(queue_name="test_mock_queue")

    result = None

    @consumer.task
    def func(msg: str):
        nonlocal result
        result = msg

    async def main():
        co = queue()
