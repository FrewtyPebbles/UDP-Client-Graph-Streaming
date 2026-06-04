# About

This is a UDP mesh network client and protocol which can multi-hop stream packets over UDP.  It uses a binary protocol and BFS to multi-hop stream packets over the mesh.

# Binary Protocol v0

This details the byte schema of the binary protocol.

## Base Headers

Every packet will have at least these base headers. which are 5 bytes in length.

||Version|Packet Type|Packet Size|Rest of the packet|
|---|---|---|---|---|
|Description|This is the protocol standard for the incomming packet.| This is the packet type. AKA the request and response type.|This is the size of the rest of the packet in bytes. |This is the remaining data|
|Size|16 bit / 2 bytes| 8 bit / 1 byte | 16 bit / 2 bytes |???|

## Info Packet Request

This packet requests connectivity info including which clients a client is connected to.

||Version|Packet Type|Packet Size|
|---|---|---|---|
|Value|0|0|0|
|Size|16 bit / 2 bytes| 8 bit / 1 byte | 16 bit / 2 bytes |
|type|int|int|int|

## Info Packet Response

This packet responds with connectivity info including which clients a client is connected to.

||Version|Packet Type|Packet Size| len(client id) | client id | ???.xxx.xxx.xxx | xxx.???.xxx.xxx | xxx.xxx.???.xxx | xxx.xxx.xxx.??? | port | ...repeat|
|---|---|---|---|---|---|---|---|---|---|---|---|
|Value|0|0|???|1-255|"client id"|0-255|0-255|0-255|0-255|0-65535| Repeat schema from and including len(client id) for each connection
|Size|16 bit / 2 bytes| 8 bit / 1 byte | 16 bit / 2 bytes | 8 bit / 1 byte | (8 bit or 1 byte) * len(client id) | 8 bit / 1 byte | 8 bit / 1 byte | 8 bit / 1 byte | 8 bit / 1 byte | 16 bit / 2 bytes |
|type|int|int|int|int|str|int|int|int|int|int|

## Message

> This message is sent via a BFS graph traversal algorithm.

### Routing Packet

First, a route is found using routing packets.  This packet is sent out from the message source client and propagate through the network with a BFS until they find the most optimal path to the target client.

||Version|Packet Type|Packet Size| len(client id) | target client id | Forward Count | len(forward client id) | forward client id | ...repeat |visited count|len(visited client id)|visited client id| ...repeat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Value|0|0|???|1-255| "target client id" | 1-255| 1-255| "forward client id" | repeat schema from and including **len(forward client id)** for all of the forwarding clients |0-255|0-255|"visited client id"| repeat schema from and including **len(visited client id)** for all of the visited clients |
|Size (bytes)|2|1|2|1|len(client id)|1|1|len(forward client id)||1|1|len(visited client id)||
|type|int|int|int|int|str|int|int|str||int|int|str||

### Backtrace Packet

Next, we backtrace through the network using just the forward part of the routing packet. This is so we can send the most optimal route back to the origin.

||Version|Packet Type|Packet Size| Forward Count | len(forward client id) | forward client id | ...repeat |
|---|---|---|---|---|---|---|---|
|Value|0|0|???| 1-255 | 1-255| "forward client id" | repeat schema from and including **len(forward client id)** for all of the forwarding clients |0-255|0-255|"visited client id"| repeat schema from and including **len(visited client id)** for all of the visited clients |
|Size (bytes)|2|1|2|1|1|len(forward client id)||1|1|len(visited client id)||
|type|int|int|int|int|int|str||int|int|str||

### Message Packet

Then the message is sent using the route our Routing and backtrace packets mapped out.

||Version|Packet Type|Packet Size| len(client id) | client id | Forward Count | len(forward client id) | forward client id | ...repeat | $\text{Message Length}$ | Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
|Value|0|0|???|1-255| "client id" | 1-255| 1-255| "client id" | repeat schema from and including **Forward Count** for all of the forwarding clients | 0-1024 | "Message content" |
|Size (bytes)|2|1|2|1|len(client id)|1|1|len(forward client id)|| 2 | len(Message) |
|type|int|int|int|int|str|int|int|str||int|str|