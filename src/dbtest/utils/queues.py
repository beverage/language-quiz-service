from asyncio import create_task, Queue

async def worker(queue: Queue, results):
    while True:
        task = await queue.get()
        try:
            result = await task
            results.append(result)
        except Exception as ex:
            print(ex)
        finally:
            queue.task_done()
            
async def batch_operation(workers: int, quantity: int, method: any, **kwargs):

    queue: Queue = Queue()
    results = []
    workers = [create_task(worker(queue, results)) for i in range(workers)]

    for i in range(quantity):
        queue.put_nowait(method(**kwargs))

    await queue.join()

    for w in workers:
        w.cancel()

    return results
