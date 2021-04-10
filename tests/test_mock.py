import asyncio
import time

import pika
import pytest
from pika import exceptions

from asy_rabbitmq.mock import MockBlockingChannel, MockBlockingConnection


def get_connection() -> pika.BlockingConnection:
    param = pika.ConnectionParameters("rabbitmq")
    conn = MockBlockingConnection(param)
    # conn = pika.BlockingConnection(param)  # 実際にrabbitmqに接続する場合
    return conn


QUEUE_NAME = "test_mock_queue"


@pytest.fixture(scope="function")
def channel():
    conn = get_connection()
    ch = conn.channel()
    ch.queue_delete(queue=QUEUE_NAME)
    ch.queue_declare(queue=QUEUE_NAME)
    yield ch

    try:
        if ch.is_open:
            ch.close()
        if conn.is_open:
            conn.close()
    except:
        pass


def test_mock_connection():
    """pika.BlockingConnectionを簡単にエミュレートしたMockオブジェクトの挙動テストを行います。"""
    conn = get_connection()

    assert conn.is_open

    conn.close()
    assert not conn.is_open
    assert conn.is_closed

    with pytest.raises(
        exceptions.ConnectionWrongStateError, match="called on closed connection"
    ):
        conn.close()


def test_mock_publish(channel):
    method_frame, header_frame, body = channel.basic_get(QUEUE_NAME)

    # メッセージがない時はNoneが返る
    assert method_frame is None
    assert header_frame is None
    assert body is None

    # メッセージを投げる
    send_body = "send_body"
    channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=send_body)

    time.sleep(0.1)

    method_frame, header_frame, body = channel.basic_get(QUEUE_NAME, auto_ack=True)
    assert method_frame
    assert header_frame
    assert body.decode("utf-8") == send_body


def test_mock_ack(channel):
    channel.close()  # キューを初期化するだけ

    conn = get_connection()
    ch = conn.channel()

    # auto_ack=Falseでメッセージは自動削除されない
    ch.basic_publish(exchange="", routing_key=QUEUE_NAME, body="hello")
    method_frame, header_frame, body = ch.basic_get(QUEUE_NAME, auto_ack=False)
    assert method_frame

    # 同一コネクション内では、再受信することはできない
    method_frame, header_frame, body = ch.basic_get(QUEUE_NAME, auto_ack=False)
    assert method_frame is None

    ch.close()
    ch = conn.channel()

    # ackを返していないので、メッセージはキューに再登録されている
    method_frame, header_frame, body = ch.basic_get(QUEUE_NAME)
    assert method_frame

    # ackを返し、メッセージを削除する
    ch.basic_ack(delivery_tag=method_frame.delivery_tag)

    ch.close()
    ch = conn.channel()

    # メッセージは削除されている
    method_frame, header_frame, body = ch.basic_get(QUEUE_NAME)
    assert method_frame is None
