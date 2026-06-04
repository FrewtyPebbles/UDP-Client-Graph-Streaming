# About

This is a UDP mesh network asynchronous client and protocol which can multi-hop stream packets over UDP.  It uses a binary protocol and BFS to multi-hop stream packets over the mesh.

# Binary Protocol v0

This details the byte schema of the binary protocol.

## Base Headers

Every packet will have at least these base headers. which are 5 bytes in length.

||Version|Packet Type|Packet Size|Rest of the packet|
|---|---|---|---|---|
|Description|This is the protocol standard for the incomming packet.| This is the packet type. AKA the request and response type.|This is the size of the rest of the packet in bytes. |This is the remaining data|
|Size|16 bit / 2 bytes| 8 bit / 1 byte | 16 bit / 2 bytes |???|

## Routing/Backtrace Packet

The routing and backtrace packet are used communicate optimal paths for routing from client to client in the mesh.

### Routing Packet

First, a route is found using routing packets.  This packet is sent out from the message source client and propagate through the network with a BFS until they find the most optimal path to the target client.

||Version|Packet Type|Packet Size| len(client id) | target client id | Forward Count | len(forward client id) | forward client id | ...repeat |visited count|len(visited client id)|visited client id| ...repeat | request type |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Value|0|ROUTING|???|1-255| "target client id" | 1-255| 1-255| "forward client id" | repeat schema from and including **len(forward client id)** for all of the forwarding clients |0-255|0-255|"visited client id"| repeat schema from and including **len(visited client id)** for all of the visited clients | This is the packet type to be returned, usually this is a backtrace packet. Some packet types include a backtrace though.|
|Size (bytes)|2|1|2|1|len(client id)|1|1|len(forward client id)||1|1|len(visited client id)||1|
|type|int|enum PacketType (int)|int|int|str|int|int|str||int|int|str||enum PacketType (int)|

### Backtrace Packet

Next, we backtrace through the network using just the forward part of the routing packet. This is so we can send the most optimal route back to the origin.

||Version|Packet Type|Packet Size| Forward Count | len(forward client id) | forward client id | ...repeat |
|---|---|---|---|---|---|---|---|
|Value|0|BACKTRACE|???| 1-255 | 1-255| "forward client id" | repeat schema from and including **len(forward client id)** for all of the forwarding clients |0-255|0-255|"visited client id"| repeat schema from and including **len(visited client id)** for all of the visited clients |
|Size (bytes)|2|1|2|1|1|len(forward client id)||1|1|len(visited client id)||
|type|int|int|int|int|int|str||int|int|str||

## Info Packet

This packet contains the connectivity info for the target client along with the routing path it will be sent back on.


||Version|Packet Type|Packet Size| Forward Count | len(forward client id) | forward client id | ...repeat | len(client id) | client id | ???.xxx.xxx.xxx | xxx.???.xxx.xxx | xxx.xxx.???.xxx | xxx.xxx.xxx.??? | port | ...repeat|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Value|0|INFO|???|0-255|1-255|"forward client id"|Repeat schema from and including **len(forward client id)** for each connection|1-255|"client id"|0-255|0-255|0-255|0-255|0-65535| Repeat schema from and including **len(client id)** for each connection
|Size (bytes)|2|1|2|1|1|len(forward client id)|| 8 bit / 1 byte | (8 bit or 1 byte) * len(client id) | 8 bit / 1 byte | 8 bit / 1 byte | 8 bit / 1 byte | 8 bit / 1 byte | 16 bit / 2 bytes ||
|type|int|int|int|int|int|str||int|str|int|int|int|int|int||

## Message Packet

This message packet contains a binary message along with the routing path it will be sent on.

||Version|Packet Type|Packet Size| len(client id) | client id | Forward Count | len(forward client id) | forward client id | ...repeat | $\text{Message Length}$ | Message |
|---|---|---|---|---|---|---|---|---|---|---|---|
|Value|0|MESSAGE|???|1-255| "client id" | 1-255| 1-255| "client id" | repeat schema from and including **Forward Count** for all of the forwarding clients | 0-1024 | "Message content" |
|Size (bytes)|2|1|2|1|len(client id)|1|1|len(forward client id)|| 2 | len(Message) |
|type|int|int|int|int|str|int|int|str||int|str|