import asyncio
from random import random
from fastapi import Depends
from asy_rabbitmq import Rabbitmq

rabbitmq = Rabbitmq(host="rabbitmq")
consume = rabbitmq.consumer(queue_name="default")


async def enqueu_job_every_seconds():
    while True:
        print_value.delay(value=random())
        await asyncio.sleep(1)


def get_template():
    return "hello!!!!"


def get_message(msg=Depends(get_template)):
    yield msg


@consume.task
async def print_value(value, msg=Depends(get_message)):
    print(f"{msg} {value}")
    return value
