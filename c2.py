from udp_graph.client import Client, ClientConnection

if __name__ == "__main__":
    c2 = Client("c2", "0.0.0.0", 4321)

    c2.connect(ClientConnection("c1", "127.0.0.1", 1234))

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

    while c4.is_listening:
        response = c4.listen_for_message(timeout=1)
        if response:
            print(response.message.decode())
            