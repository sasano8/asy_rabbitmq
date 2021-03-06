from asy_rabbitmq.mock import MockRabbitmq


def test_manage_delay_task():
    rabbitmq = MockRabbitmq(host="rabbitmq")
    test_queue = rabbitmq.consumer(queue_name="test_queue")

    @test_queue.task
    def func(msg: str):
        return msg

    assert func.delay
    func.delay(msg="a")
