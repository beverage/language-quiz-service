from asyncio import create_task, gather, Queue, sleep
from typing import Any, Awaitable, Callable, List, TypeVar
import asyncio

T = TypeVar("T")


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


async def parallel_execute(
    tasks: List[Awaitable[T]],
    max_concurrent: int = 10,
    batch_delay: float = 0.5,
    error_handler: Callable[[Exception, int], None] = None,
) -> List[T]:
    """
    Execute a list of async tasks in parallel with batching and error handling.

    Args:
        tasks: List of coroutines to execute
        max_concurrent: Maximum number of concurrent tasks per batch
        batch_delay: Delay between batches in seconds
        error_handler: Optional function to handle exceptions (receives exception and task index)

    Returns:
        List of successful results
    """
    if not tasks:
        return []

    if len(tasks) == 1:
        # Single task - no need for parallel execution
        try:
            result = await tasks[0]
            return [result]
        except Exception as ex:
            if error_handler:
                error_handler(ex, 0)
            return []

    # Multiple tasks - use parallel execution
    max_concurrent = min(max_concurrent, len(tasks))
    results = []

    for i in range(0, len(tasks), max_concurrent):
        batch = tasks[i : i + max_concurrent]
        try:
            batch_results = await asyncio.gather(*batch, return_exceptions=True)

            # Filter out exceptions and collect successful results
            for idx, result in enumerate(batch_results):
                task_index = i + idx
                if isinstance(result, Exception):
                    if error_handler:
                        error_handler(result, task_index)
                else:
                    results.append(result)

            # Small delay between batches to avoid overwhelming the API
            if i + max_concurrent < len(tasks):
                await sleep(batch_delay)

        except Exception as ex:
            if error_handler:
                # Call error handler for all tasks in the failed batch
                for idx in range(len(batch)):
                    error_handler(ex, i + idx)

    return results
