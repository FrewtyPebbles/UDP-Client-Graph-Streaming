import pytest_asyncio
import asyncio
from udp_graph.client import Client, ClientConnection
from collections.abc import AsyncGenerator
from aio_benchmark import aio_benchmark
from network_fixtures import GraphFixtureValue, mesh_network_graph, mesh_network_linked_list
from udp_graph.protocol import InfoPacket

def _template_test_mesh_network_info(mesh_network:GraphFixtureValue, aio_benchmark):
    origin_client, reciever_client, connection_set = mesh_network

    async def get_info(client_id):
        return await origin_client.get_info(client_id, 1)

    info:InfoPacket = aio_benchmark(get_info, client_id=reciever_client.client_id, rounds=1500, iterations=1)

    assert info is not None

    assert {con.to_tuple() for con in info.connections.values()} == connection_set

def test_get_info_graph(mesh_network_graph:GraphFixtureValue, aio_benchmark):
    _template_test_mesh_network_info(mesh_network_graph, aio_benchmark)

def test_get_info_linked_list(mesh_network_linked_list:GraphFixtureValue, aio_benchmark):
    _template_test_mesh_network_info(mesh_network_linked_list, aio_benchmark)
