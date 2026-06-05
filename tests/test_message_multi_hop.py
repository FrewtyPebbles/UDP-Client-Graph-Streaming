import pytest_asyncio
import asyncio
from udp_graph.client import Client, ClientConnection
from collections.abc import AsyncGenerator
from pytest_benchmark.fixture import BenchmarkFixture
from aio_benchmark import aio_benchmark
from udp_graph.protocol import MessagePacket
from network_fixtures import GraphFixtureValue, mesh_network_graph, mesh_network_linked_list
import time
import logging
logger = logging.getLogger(__name__)



def _template_test_mesh_network_message(mesh_network:GraphFixtureValue, aio_benchmark):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    origin_client, reciever_client, _ = mesh_network

    async def send_message(message):
        await origin_client.send_message(reciever_client.client_id, message)
        return await reciever_client.listen_for_message(timeout=1)
        
    # not cached
    start = time.perf_counter()
    message_packet:MessagePacket = loop.run_until_complete(send_message(b"test"))
    logger.info(f"Non cached message send benchmark(single test): {(time.perf_counter() - start) * 1000}ms")

    assert message_packet is not None

    assert message_packet.message == b"test"

    # cached
    message_packet:MessagePacket = aio_benchmark(send_message, message=b"test", rounds=1000, iterations=1)

    assert message_packet is not None

    assert message_packet.message == b"test"

def test_send_message_graph(mesh_network_graph:GraphFixtureValue, aio_benchmark):
    _template_test_mesh_network_message(mesh_network_graph, aio_benchmark)

def test_send_message_linked_list(mesh_network_linked_list:GraphFixtureValue, aio_benchmark):
    _template_test_mesh_network_message(mesh_network_linked_list, aio_benchmark)