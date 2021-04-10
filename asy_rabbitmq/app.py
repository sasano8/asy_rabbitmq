from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from json import dumps
from typing import Callable, TypeVar

import asy
import pika
from fastapi.encoders import jsonable_encoder
from pika import exceptions
from pika.adapters.blocking_connection import BlockingChannel
from pydantic import BaseModel, Field
from .utils import is_coroutine_callable
from .func import FuncMimicry


F = TypeVar("F", bound=Callable)


class Rabbitmq(pika.ConnectionParameters):
    def consumer(
        self,
        queue_name: str,  # キューのオプション
        durable: bool = True,  # キューのオプション
        # passive: bool = ...,  # キューのオプション
        # exclusive: bool = ...,  # キューのオプション
        # auto_delete: bool = ...,  # キューのオプション
        # arguments=...,  # キューのオプション
        auto_ack: bool = False,  # consumerのオプション
    ) -> Consumer:
        consumer = Consumer(queue_name=queue_name, durable=durable, auto_ack=auto_ack)
        connector = Connector(self)
        consumer.depends_on(connector)
        return consumer

    def create_connection(self):
        return pika.BlockingConnection(self)


class Connector:
    def __init__(self, params: Rabbitmq):
        self.params = params
        self.create_connection = params.create_connection
        self.clear()

    def clear(self):
        self.conn = None
        self.is_cancelled = False

    def __del__(self):
        conn = self.conn
        self.clear()

        if conn is None:
            return

        if conn.is_open:
            conn.close()

    async def get_conn(self):
        if self.conn and self.conn.is_open:
            return self.conn

        self.clear()
        self.conn = self.create_connection()
        return self.conn

    def get_connection(self):
        if self.conn and self.conn.is_open:
            return self.conn

        self.clear()
        self.conn = self.create_connection()
        return self.conn

    def release_conn(self):
        self.__del__()

    # async def __call__(self, token: asy.PCancelToken):
    #     """キャンセルされるまでコネクションを自動で確立する"""
    #     while not token.is_cancelled:
    #         try:
    #             self.establish_conn()
    #             await asyncio.sleep(10)
    #         except exceptions.AMQPError as e:
    #             import traceback

    #             print(traceback.format_exc())
    #             await asyncio.sleep(1)

    #     self.release_conn()


@dataclass
class Consumer:
    """コルーチンを実行すると自動的にチャンネルの確立と自動回復を行う。
    チャンネル確立時に、キューを自動的に定義する。
    RabbitMQからメッセージを受信し、メッセージに対応する処理を実行する。
    """

    queue_name: str  # キューのオプション
    durable: bool = True  # キューのオプション  RabbitMQ停止時にメッセージを永続化する
    # passive: bool = ...,  # キューのオプション
    # exclusive: bool = ...,  # キューのオプション
    # auto_delete: bool = ...,  # キューのオプション
    # arguments=...,  # キューのオプション
    auto_ack: bool = False  # consumerのオプション  メッセージ受信時に自動でメッセージを削除する。
    # inactivity_timeout: int = 1  # consume時のキュー受信後の非活動時間を設定。現在は、getで行っているので不要。
    # timeout_when_connection_close: int = 10  # 使用していない。不要。

    is_cancelled: bool = field(default=False, init=False)

    def __post_init__(self):
        self.channel: BlockingChannel = None
        self.functions = {}
        self.logger = logging.getLogger(__name__)
        self.connector = None

    def depends_on(self, connector: Rabbitmq):
        self.connector = connector

    async def get_channel(self):
        if self.channel and self.channel.is_open:
            return self.channel
        try:
            conn = await asyncio.wait_for(self.connector.get_conn(), timeout=5)
        except asyncio.exceptions.TimeoutError as e:
            raise exceptions.AMQPConnectionError(
                "Timed out because the connection could not be established"
            )

        self.channel = conn.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=self.durable)
        return self.channel

    def _add_task(self, task: Task):
        if task.__name__ in self.functions:
            raise KeyError(f"duplicate function name: {task.__name__}")
        self.functions[task.__name__] = task

    def task(self, func):
        new_func = Task(func)
        new_func.depends_on(self)
        self._add_task(new_func)
        return new_func

    def basic_publish(self, body: CallInfo, *, exchange="") -> None:
        if not self.channel:
            self.channel = self.connector.get_connection().channel()

        if self.channel.is_closed:
            self.channel = self.connector.get_connection().channel()

        channel = self.channel
        channel.queue_declare(queue=self.queue_name, durable=self.durable)

        # if (self.channel and self.channel.is_open) == False:
        #     raise exceptions.AMQPChannelError("Channel is not open.")
        json_str = body.encode()

        channel.basic_publish(
            exchange=exchange, routing_key=self.queue_name, body=json_str
        )

    async def __call__(self, token: asy.PCancelToken):
        assert not token.is_cancelled

        # while not token.is_cancelled:
        #     await asyncio.sleep(0)

        params = dict(queue=self.queue_name, auto_ack=self.auto_ack)

        while not token.is_cancelled:
            try:
                await asyncio.sleep(0)
                channel = await self.get_channel()
                msg = channel.basic_get(**params)

                # キューが空の場合はNone
                if not any(msg):
                    await asyncio.sleep(1)
                    continue

                method, properties, body = msg
                body = json.loads(body)
                body = CallInfo(**body)

                result = await self.execute(channel, method, properties, body)
            except Exception as e:
                import traceback

                print(traceback.format_exc())
                await asyncio.sleep(1)
                continue

    async def execute(
        self,
        channel: BlockingChannel,
        method,
        properties,
        body: CallInfo,
    ):
        func = self.functions[body.func]

        if not is_coroutine_callable(func):
            raise Exception(f"{func.__name__} is not coroutine function.")

        func_name = body.func
        file = func.__code__.co_filename
        line = func.__code__.co_firstlineno

        try:
            await func(*body.args, **body.kwargs)
            self.logger.info(
                f"[SUCCESS]{file} {line} {func_name}({body.args!r}, {body.kwargs!r})"
            )
        except Exception as e:
            self.logger.warning(
                f"[FAILED]{file} {line} {func_name}({body.args!r}, {body.kwargs!r})"
            )

            # TODO: 処理が数回失敗した場合は、デッドレターキューに格納する（現在はとりあえず削除）
            # channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)  # メッセージを破棄する
            # channel.basic_reject(delivery_tag=method.delivery_tag, requeue=True)  # メッセージを再度キューイングする。実行順序は、多分最後になる
            # channel.close()  # コネクションやチャンネル開放時、未応答のキューは再度キューイングされる。順序はそのままらしいので、エラーが発生し続け、他の処理を妨害する恐れがある

        if not self.auto_ack:
            channel.basic_ack(delivery_tag=method.delivery_tag)


class Task(FuncMimicry[F]):
    def depends_on(self, consumer: Consumer) -> None:
        self.consumer = consumer

    @property
    def delay(self) -> F:
        return self._delay  # type: ignore

    def _delay(self, *args, **kwargs) -> None:
        task = CallInfo(func=self.__name__, args=args, kwargs=kwargs)
        self.consumer.basic_publish(task)


class CallInfo(BaseModel):
    func: str = Field(description="実行する関数")
    args: tuple = Field(description="実行する関数に渡す位置引数")
    kwargs: dict = Field(description="実行する関数に渡すキーワード引数")

    def encode(self) -> str:
        dic = jsonable_encoder(self)
        return dumps(dic, ensure_ascii=False)
