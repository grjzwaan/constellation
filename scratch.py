# Implementation of fanout to multiple producers via queues
import asyncio
import aiostream
from aiostream import pipe

yq = asyncio.Queue()
zq = asyncio.Queue()


def to_queue(q: asyncio.Queue):
    async def qit(item):
        await q.put(item)

    return qit


async def from_queue(q):
    while True:  # Doesn't work if the producer is finite
        await asyncio.sleep(3)
        item = await q.get()
        yield item
        q.task_done()


# Example with a stream of messages that are handled through queues by multiple consumers, which each can be a pipe
xs = (
        aiostream.stream.count(interval=0.1)
        | pipe.take(10)
        | pipe.action(add_log)
        | pipe.action(to_queue(yq)) | pipe.action(to_queue(zq))
)

# Consumers
ys = aiostream.stream.iterate(from_queue(yq)) | pipe.map(lambda x: x + 10) | pipe.action(add_log)
zs = aiostream.stream.iterate(from_queue(zq)) | pipe.map(lambda x: x + 100) | pipe.action(add_log)

await asyncio.gather(xs, ys, zs)