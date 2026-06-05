import asyncio

import pytest_asyncio
from udp_graph.client import Client, ClientConnection
from collections.abc import AsyncGenerator
from aio_benchmark import aio_benchmark

GraphFixtureValue = tuple[Client, Client, set[tuple[str,int]]]

@pytest_asyncio.fixture
async def mesh_network_graph() -> AsyncGenerator[GraphFixtureValue, None]:
    c1 = Client("c1", "0.0.0.0", 1234, 2000)
    c2 = Client("c2", "0.0.0.0", 4321, 2000)
    c3 = Client("c3", "0.0.0.0", 4111, 2000)
    c4 = Client("c4", "0.0.0.0", 4131, 2000)
    c5 = Client("c5", "0.0.0.0", 4134, 2000)

    try:
        await c1.start_listening()

        c2.connect(ClientConnection("c1", "127.0.0.1", 1234))
        c1.connect(ClientConnection("c2", "127.0.0.1", 4321))

        await c2.start_listening()


        c2.connect(ClientConnection("c3", "127.0.0.1", 4111))
        c3.connect(ClientConnection("c2", "127.0.0.1", 4321))

        await c3.start_listening()
        

        c3.connect(ClientConnection("c4", "127.0.0.1", 4131))
        c4.connect(ClientConnection("c3", "127.0.0.1", 4111))

        await c4.start_listening()


        c5.connect(ClientConnection("c4", "127.0.0.1", 4131))
        c4.connect(ClientConnection("c5", "127.0.0.1", 4134))
        c5.connect(ClientConnection("c2", "127.0.0.1", 4321))
        c2.connect(ClientConnection("c5", "127.0.0.1", 4134))

        await c5.start_listening()

        yield c1, c4, {con.to_tuple() for con in c4.connections.values()}
    finally:
        await asyncio.gather(
            c1.stop_listening(1),
            c2.stop_listening(1),
            c3.stop_listening(1),
            c4.stop_listening(1),
            c5.stop_listening(1),
            return_exceptions=True,
        )


@pytest_asyncio.fixture
async def mesh_network_linked_list() -> AsyncGenerator[GraphFixtureValue, None]:
    c1 = Client("c1", "0.0.0.0", 1234, 2000)
    c2 = Client("c2", "0.0.0.0", 4321, 2000)
    c3 = Client("c3", "0.0.0.0", 4111, 2000)
    c4 = Client("c4", "0.0.0.0", 4131, 2000)
    c5 = Client("c5", "0.0.0.0", 4134, 2000)
    c6 = Client("c6", "0.0.0.0", 1111, 2000)

    try:
        await c1.start_listening()

        c2.connect(ClientConnection("c1", "127.0.0.1", 1234))
        c1.connect(ClientConnection("c2", "127.0.0.1", 4321))

        await c2.start_listening()


        c2.connect(ClientConnection("c3", "127.0.0.1", 4111))
        c3.connect(ClientConnection("c2", "127.0.0.1", 4321))

        await c3.start_listening()
        

        c3.connect(ClientConnection("c4", "127.0.0.1", 4131))
        c4.connect(ClientConnection("c3", "127.0.0.1", 4111))

        await c4.start_listening()


        c5.connect(ClientConnection("c4", "127.0.0.1", 4131))
        c4.connect(ClientConnection("c5", "127.0.0.1", 4134))

        await c5.start_listening()


        c6.connect(ClientConnection("c5", "127.0.0.1", 4134))
        c5.connect(ClientConnection("c6", "127.0.0.1", 1111))

        await c6.start_listening()

        yield c1, c6, {con.to_tuple() for con in c6.connections.values()}

    finally:

        await asyncio.gather(
            c1.stop_listening(1),
            c2.stop_listening(1),
            c3.stop_listening(1),
            c4.stop_listening(1),
            c5.stop_listening(1),
            c6.stop_listening(1),
            return_exceptions=True,
        )