# asy
[![Version](https://img.shields.io/pypi/v/asy)](https://pypi.org/project/asy)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`asy_rabbitmq`はasy上で利用できる非同期AMQPクライアント（pikaのラッパー）です。


# Requirement

- Python 3.8+

# Installation

``` shell
pip install asy_rabbitmq
```

# Getting started
``` Python
import asyncio
import asy

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

asy.supervise(consume, enqueu_job_every_seconds).run()
```

# 開発ガイド
CONTRIBUTING.mdを参照ください。

