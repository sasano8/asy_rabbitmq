from asy_rabbitmq import Rabbitmq


def test_manage_delay_task():
    ...
    rabbitmq = Rabbitmq(url="rabbitmq", is_mock=True)
    test_queue = rabbitmq.consumer(queue_name="test_queue")

    @test_queue.task
    def func(msg: str):
        return msg

    # assert func.delay  # type: ignore
    # func.delay()
