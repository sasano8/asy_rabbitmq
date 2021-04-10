import asyncio
from random import random

from asy_rabbitmq import Rabbitmq

param = Rabbitmq(host="rabbitmq")
consume = param.consumer(queue_name="default")


async def enqueu_job_every_seconds():
    while True:
        print_value.delay(random())
        await asyncio.sleep(1)


@consume.task
async def print_value(value):
    print("get: " + str(value))
