from copy import deepcopy
from random import random
from typing import Any, Dict, List, Tuple

import pika
from pika import exceptions
from pika.adapters.blocking_connection import BlockingChannel


class Dummy:
    pass


class MockBlockingConnection:
    """Mock of pika.BlockingConnection"""

    queue: Dict[str, List[Tuple[Any, Any, Any]]] = {}

    def __init__(self, parameters: pika.ConnectionParameters = None) -> None:
        self.is_open = True
        self.is_closed = False
        # self.queue: Dict[str, List[Tuple[Any, Any, Any]]] = {}

    def close(self):
        if self.is_closed:
            raise exceptions.ConnectionWrongStateError("called on closed connection")

        self.is_open = False
        self.is_closed = True
        self.queue = {}

    def channel(self) -> BlockingChannel:
        return MockBlockingChannel(self)

    def __enter__(self):
        # Prepare `with` context
        return self

    def __exit__(self, exc_type, value, traceback):
        # Close connection after `with` context
        if self.is_open:
            self.close()


class MockBlockingChannel:
    def __init__(self, conn: MockBlockingConnection) -> None:
        self.conn = conn
        self.queue = conn.queue
        self.no_ack_queue = {}

        self.is_open = True
        self.is_closed = False

    def close(self):
        if self.is_closed:
            raise exceptions.ConnectionWrongStateError("called on closed connection")

        self.is_open = False
        self.is_closed = True

        for queue in self.no_ack_queue:
            orign_queue = self.queue[queue]
            for v in self.no_ack_queue[queue]:
                orign_queue.append(v)

    def queue_declare(
        self,
        queue,
        passive=False,
        durable=False,
        exclusive=False,
        auto_delete=False,
        arguments=None,
    ) -> Any:
        if not queue in self.queue:
            self.queue[queue] = []

    def queue_delete(self, queue, if_unused=False, if_empty=False):
        if queue in self.queue:
            del self.queue[queue]

    def basic_publish(
        self, exchange, routing_key, body, properties=None, mandatory=False
    ) -> None:

        method_frame = Dummy()
        method_frame.delivery_tag = random()

        arr = self.queue[routing_key]
        arr.append((method_frame, "something", body.encode()))

    def basic_get(self, queue, auto_ack=False):
        if queue in self.queue:
            if len(self.queue[queue]):
                val = self.queue[queue].pop()

                if not auto_ack:
                    self.no_ack_queue.setdefault(queue, []).append(deepcopy(val))

                return val

        return None, None, None

    def basic_ack(self, delivery_tag=0, multiple=False):
        for queue in self.no_ack_queue:
            arr = self.no_ack_queue[queue]
            for index, value in enumerate(arr):
                method_frame, header_frame, body = value
                if method_frame.delivery_tag == delivery_tag:
                    del arr[index]
                    return

        raise KeyError(f"{delivery_tag=}")
