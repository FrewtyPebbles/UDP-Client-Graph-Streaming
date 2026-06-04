import pytest
from udp_graph.client import Client, ClientConnection

@pytest.fixture
def mesh_network_graph():
    c1 = Client("c1", "0.0.0.0", 1234)

    c1.start_listening()

    c2 = Client("c2", "0.0.0.0", 4321)

    c2.connect(ClientConnection("c1", "127.0.0.1", 1234))
    c1.connect(ClientConnection("c2", "127.0.0.1", 4321))

    c2.start_listening()

    c3 = Client("c3", "0.0.0.0", 4111)

    c2.connect(ClientConnection("c3", "127.0.0.1", 4111))
    c3.connect(ClientConnection("c2", "127.0.0.1", 4321))

    c3.start_listening()
    
    c4 = Client("c4", "0.0.0.0", 4131)

    c3.connect(ClientConnection("c4", "127.0.0.1", 4131))
    c4.connect(ClientConnection("c3", "127.0.0.1", 4111))

    c4.start_listening()

    c5 = Client("c5", "0.0.0.0", 4134)

    c5.connect(ClientConnection("c4", "127.0.0.1", 4131))
    c4.connect(ClientConnection("c5", "127.0.0.1", 4134))
    c5.connect(ClientConnection("c2", "127.0.0.1", 4321))
    c2.connect(ClientConnection("c5", "127.0.0.1", 4134))

    c5.start_listening()

    yield c1, c4

    c1.stop_listening()
    c2.stop_listening()
    c3.stop_listening()
    c4.stop_listening()
    c5.stop_listening()

@pytest.fixture
def mesh_network_linked_list():
    c1 = Client("c1", "0.0.0.0", 1234)

    c1.start_listening()

    c2 = Client("c2", "0.0.0.0", 4321)

    c2.connect(ClientConnection("c1", "127.0.0.1", 1234))
    c1.connect(ClientConnection("c2", "127.0.0.1", 4321))

    c2.start_listening()

    c3 = Client("c3", "0.0.0.0", 4111)

    c2.connect(ClientConnection("c3", "127.0.0.1", 4111))
    c3.connect(ClientConnection("c2", "127.0.0.1", 4321))

    c3.start_listening()
    
    c4 = Client("c4", "0.0.0.0", 4131)

    c3.connect(ClientConnection("c4", "127.0.0.1", 4131))
    c4.connect(ClientConnection("c3", "127.0.0.1", 4111))

    c4.start_listening()

    c5 = Client("c5", "0.0.0.0", 4134)

    c5.connect(ClientConnection("c4", "127.0.0.1", 4131))
    c4.connect(ClientConnection("c5", "127.0.0.1", 4134))

    c5.start_listening()

    c6 = Client("c6", "0.0.0.0", 1111)

    c6.connect(ClientConnection("c5", "127.0.0.1", 4134))
    c5.connect(ClientConnection("c6", "127.0.0.1", 1111))

    c6.start_listening()

    yield c1, c6

    c1.stop_listening()
    c2.stop_listening()
    c3.stop_listening()
    c4.stop_listening()
    c5.stop_listening()

def _template_test_mesh_network(mesh_network:tuple[Client, Client]):
    origin_client, reciever_client = mesh_network

    origin_client.send_message(reciever_client.client_id, b"Test")
    message_packet = reciever_client.listen_for_message(timeout=1)

    assert message_packet is not None

    assert message_packet.message == b"Test"

def test_send_message_graph(mesh_network_graph:tuple[Client, Client]):
    _template_test_mesh_network(mesh_network_graph)

def test_send_message_linked_list(mesh_network_linked_list:tuple[Client, Client]):
    _template_test_mesh_network(mesh_network_linked_list)
