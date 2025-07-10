from asyncio import create_task, gather, Queue
from typing import Any, Awaitable


async def worker(queue: Queue, results):
    while True:
        task = await queue.get()

        if task is None:
            queue.task_done()
            break

        try:
            result = await task
            results.append(result)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            print(ex)
        finally:
            queue.task_done()


async def batch_operation(
    workers: int, quantity: int, method: list[Awaitable[Any]], **kwargs
):
    queue: Queue = Queue()
    results = []
    worker_tasks = [create_task(worker(queue, results)) for _ in range(workers)]

    for _ in range(quantity):
        task = method(**kwargs)
        queue.put_nowait(task)

    await queue.join()

    for _ in range(workers):
        queue.put_nowait(None)

    await gather(*worker_tasks)

    return results
