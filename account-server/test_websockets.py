import os
import asyncio
import struct
import time
import websockets


class Server:
    def __init__(self):
        self.queues: list[asyncio.Queue] = []
        self.server = None

    # noinspection PyBroadException
    async def normal_ws_handler(self, ws_protocol, path):
        client_queue = asyncio.Queue()
        self.queues.append(client_queue)
        while True:
            msg = await client_queue.get()
            if msg is None:
                break
            await ws_protocol.send(msg)

    # noinspection PyBroadException
    async def merged_ws_handler(self, ws_protocol, path):
        client_queue = asyncio.Queue()
        self.queues.append(client_queue)

        while True:
            msg = await client_queue.get()
            if msg is None:
                break
            for _ in range(client_queue.qsize()):
                msg += client_queue.get_nowait()
            await ws_protocol.send(msg)

    async def run(self, merged: bool):
        self.server = await websockets.serve(
            host="localhost",
            port=63636,
            ws_handler=self.merged_ws_handler if merged else self.normal_ws_handler,
            compression=None)

    async def update_generator(self, messages: int, message_len: int, sleep: float):
        for _ in range(messages):
            random_bytes = os.urandom(message_len - 8)
            update_message = struct.pack("d", time.time()) + random_bytes
            for queue in self.queues:
                queue.put_nowait(update_message)
            await asyncio.sleep(sleep)

    async def finish_signal(self):
        for queue in self.queues:
            queue.put_nowait(None)


class Client:
    def __init__(self, messages_len: int):
        self.lat_sum = 0
        self.message_count = 0
        self.message_len = messages_len

    async def run_normal(self):
        async with websockets.connect(uri="ws://127.0.0.1:63636") as websocket:
            async for message in websocket:
                self.lat_sum += time.time() - struct.unpack("d", message[:8])[0]
                self.message_count += 1

    async def run_merged(self):
        async with websockets.connect(uri="ws://127.0.0.1:63636") as websocket:
            async for messages in websocket:
                index = 0
                msg = messages[index * self.message_len: (index + 1) * self.message_len]
                while msg:
                    self.lat_sum += time.time() - struct.unpack("d", msg[:8])[0]
                    self.message_count += 1
                    index += 1
                    msg = messages[index * self.message_len: (index + 1) * self.message_len]


async def run_benchmark(client_count: int,
                        messages: int,
                        update_generator_count: int,
                        message_len: int,
                        sleep: float, merged: bool):
    assert message_len >= 8, "Minimum possible length is 8 bytes"
    test_server = Server()
    await test_server.run(merged=merged)

    clients = []
    tasks = []
    for _ in range(client_count):
        test_client = Client(messages_len=message_len)
        clients.append(test_client)
        tasks.append(asyncio.create_task(test_client.run_merged() if merged else test_client.run_normal()))
        await asyncio.sleep(0.01)

    print("Wait for all clients to connect")
    while len(test_server.queues) != client_count:
        await asyncio.sleep(1)

    print("Generating updates")
    await asyncio.gather(
        *[test_server.update_generator(
            messages=messages,
            sleep=sleep,
            message_len=message_len) for _ in range(update_generator_count)]
    )

    await test_server.finish_signal()
    print("Waiting to finish")
    await asyncio.gather(*tasks)

    lat_sum = sum([cli.lat_sum for cli in clients])
    msg_count_sum = sum([cli.message_count for cli in clients])

    print("transmitted_messages =", msg_count_sum,
          "| sleep =", sleep,
          "| client_count =", client_count,
          "| update_generators =", update_generator_count,
          "| merged =", merged,
          "| message_len =", message_len, "bytes",
          "| latency_avg =", lat_sum / msg_count_sum)
    test_server.server.close()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run_benchmark(messages=10,
                                                              update_generator_count=3,
                                                              message_len=1000,
                                                              sleep=0.05,
                                                              client_count=1000,
                                                              merged=False))

    asyncio.get_event_loop().run_until_complete(run_benchmark(messages=10,
                                                              update_generator_count=3,
                                                              message_len=1000,
                                                              sleep=0.05,
                                                              client_count=1000,
                                                              merged=True))
