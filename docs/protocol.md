# Binary Protocol v0

This details the byte schema of the binary protocol.

## Base Headers

Every packet will have at least these base headers. which are 5 bytes in length.

||Version|Packet Type|Packet Size|Rest of the packet|
|---|---|---|---|---|
|Description|This is the protocol standard for the incomming packet.| This is the packet type. AKA the request and response type.|This is the size of the rest of the packet in bytes. |This is the remaining data|
|Size|16 bit / 2 bytes| 8 bit / 1 byte | 16 bit / 2 bytes |???|

## Info Packet

This packet requests and replies with connectivity info. So which clients a client is connected to.

### Request Info

||Version|Packet Type|Packet Size|
|---|---|---|---|
|Value|0|0|0|
|Size|16 bit / 2 bytes| 8 bit / 1 byte | 16 bit / 2 bytes |
|type|int|int|int|

### Info Response

||Version|Packet Type|Packet Size| len(client id) | client id | ???.xxx.xxx.xxx | xxx.???.xxx.xxx | xxx.xxx.???.xxx | xxx.xxx.xxx.??? | port | repeat|
|---|---|---|---|---|---|---|---|---|---|---|---|
|Value|0|0|???|1-255|"client id"|0-255|0-255|0-255|0-255|0-65535| Repeat schema from and including len(client id) for each connection
|Size|16 bit / 2 bytes| 8 bit / 1 byte | 16 bit / 2 bytes | 8 bit / 1 byte | (8 bit or 1 byte) * len(client id) | 8 bit / 1 byte | 8 bit / 1 byte | 8 bit / 1 byte | 8 bit / 1 byte | 16 bit / 2 bytes |
|type|int|int|int|int|str|int|int|int|int|int|

### Message

||Version|Packet Type|Packet Size| len(client id) | client id | $\text{Message Length}$ | Message |
|---|---|---|---|---|---|---|---|
|Value|0|0|???|1-255| "client id" | 0-510 | "Message content" |
|Size|16 bit / 2 bytes| 8 bit / 1 byte | 16 bit / 2 bytes | 8 bit / 1 byte | (8 bit or 1 byte) * len(client id) | 16 bit / 2 bytes | (8 bit or 1 byte) * len(Message) |
|type|int|int|int|int|str|int|str|