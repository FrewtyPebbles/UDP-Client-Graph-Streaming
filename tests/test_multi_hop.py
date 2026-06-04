import pytest
import asyncio
from udp_graph.client import Client, ClientConnection
from collections.abc import AsyncGenerator

@pytest.fixture
async def mesh_network_graph() -> AsyncGenerator[tuple[Client, Client], None]:
    c1 = Client("c1", "0.0.0.0", 1234)
    c2 = Client("c2", "0.0.0.0", 4321)
    c3 = Client("c3", "0.0.0.0", 4111)
    c4 = Client("c4", "0.0.0.0", 4131)
    c5 = Client("c5", "0.0.0.0", 4134)

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

        yield c1, c4

    finally:

        await asyncio.gather(
            c1.stop_listening(),
            c2.stop_listening(),
            c3.stop_listening(),
            c4.stop_listening(),
            c5.stop_listening(),
            return_exceptions=True
        )


@pytest.fixture
async def mesh_network_linked_list() -> AsyncGenerator[tuple[Client, Client], None]:
    c1 = Client("c1", "0.0.0.0", 1234)
    c2 = Client("c2", "0.0.0.0", 4321)
    c3 = Client("c3", "0.0.0.0", 4111)
    c4 = Client("c4", "0.0.0.0", 4131)
    c5 = Client("c5", "0.0.0.0", 4134)
    c6 = Client("c6", "0.0.0.0", 1111)

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

        yield c1, c6

    finally:

        await c1.stop_listening()
        await c2.stop_listening()
        await c3.stop_listening()
        await c4.stop_listening()
        await c5.stop_listening()
        await c6.stop_listening()

async def _template_test_mesh_network(mesh_network:tuple[Client, Client]):
    origin_client, reciever_client = mesh_network

    await origin_client.send_message(reciever_client.client_id, b"Test")
    message_packet = await reciever_client.listen_for_message(timeout=1)

    assert message_packet is not None

    assert message_packet.message == b"Test"

async def test_send_message_graph(mesh_network_graph:tuple[Client, Client]):
    await _template_test_mesh_network(mesh_network_graph)

async def test_send_message_linked_list(mesh_network_linked_list:tuple[Client, Client]):
    await _template_test_mesh_network(mesh_network_linked_list)
