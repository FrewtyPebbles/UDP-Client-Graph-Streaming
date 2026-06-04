import time

from udp_graph.client import Client, ClientConnection

if __name__ == "__main__":
    c1 = Client("c1", "0.0.0.0", 1234)

    c1.connect(ClientConnection("c2", "127.0.0.1", 4321))

    c1.start_listening()

    i = 0
    ascii_anim = [
        b"apple \r",
        b"bottom\r",
        b"jeans \r",
        b"boots \r",
        b"with  \r",
        b"the   \r",
        b"furr  \r",
    ]
    while c1.is_listening:
        time.sleep(1)
        c1.send_message("c4", ascii_anim[i % len(ascii_anim)])
        i += 1