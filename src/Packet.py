"""

    This is the format of packets in our network:



                                                **  NEW Packet Format  **
     __________________________________________________________________________________________________________________
    |           Version(2 Bytes)         |         Type(2 Bytes)         |           Length(Long int/4 Bytes)          |
    |------------------------------------------------------------------------------------------------------------------|
    |                                            Source Server IP(8 Bytes)                                             |
    |------------------------------------------------------------------------------------------------------------------|
    |                                           Source Server Port(4 Bytes)                                            |
    |------------------------------------------------------------------------------------------------------------------|
    |                                                    ..........                                                    |
    |                                                       BODY                                                       |
    |                                                    ..........                                                    |
    |__________________________________________________________________________________________________________________|

    Version:
        For now version is 1

    Type:
        1: Register
        2: Advertise
        3: Join
        4: Message
        5: Reunion
                e.g: type = '2' => Advertise packet.
    Length:
        This field shows the character numbers for Body of the packet.

    Server IP/Port:
        We need this field for response packet in non-blocking mode.



    ***** For example: ******

    version = 1                 b'\x00\x01'
    type = 4                    b'\x00\x04'
    length = 12                 b'\x00\x00\x00\x0c'
    ip = '192.168.001.001'      b'\x00\xc0\x00\xa8\x00\x01\x00\x01'
    port = '65000'              b'\x00\x00\xfd\xe8'
    Body = 'Hello World!'       b'Hello World!'

    Bytes = b'\x00\x01\x00\x04\x00\x00\x00\x0c\x00\xc0\x00\xa8\x00\x01\x00\x01\x00\x00\xfd\xe8Hello World!'




    Packet descriptions:

        Register:
            Request:

                                 ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |                  IP (15 Chars)                 |
                |------------------------------------------------|
                |                 Port (5 Chars)                 |
                |________________________________________________|

                For sending IP/Port of the current node to the root to ask if it can register to network or not.

            Response:

                                 ** Body Format **
                 _________________________________________________
                |                  RES (3 Chars)                  |
                |-------------------------------------------------|
                |                  ACK (3 Chars)                  |
                |_________________________________________________|

                For now only should just send an 'ACK' from the root to inform a node that it
                has been registered in the root if the 'Register Request' was successful.

        Advertise:
            Request:

                                ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |________________________________________________|

                Nodes for finding the IP/Port of their neighbour peer must send this packet to the root.

            Response:

                                ** Packet Format **
                 ________________________________________________
                |                RES(3 Chars)                    |
                |------------------------------------------------|
                |              Server IP (15 Chars)              |
                |------------------------------------------------|
                |             Server Port (5 Chars)              |
                |________________________________________________|

                Root will response Advertise Request packet with sending IP/Port of the requester peer in this packet.

        Join:

                                ** Body Format **
                 ________________________________________________
                |                 JOIN (4 Chars)                 |
                |________________________________________________|

            New node after getting Advertise Response from root must send this packet to the specified peer
            to tell him that they should connect together; When receiving this packet we should update our
            Client Dictionary in the Stream object.



        Message:
                                ** Body Format **
                 ________________________________________________
                |             Message (#Length Chars)            |
                |________________________________________________|

            The message that want to broadcast to hole network. Right now this type only includes a plain text.

        Reunion:
            Hello:

                                ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |           Number of Entries (2 Chars)          |
                |------------------------------------------------|
                |                 IP0 (15 Chars)                 |
                |------------------------------------------------|
                |                Port0 (5 Chars)                 |
                |------------------------------------------------|
                |                 IP1 (15 Chars)                 |
                |------------------------------------------------|
                |                Port1 (5 Chars)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IPN (15 Chars)                 |
                |------------------------------------------------|
                |                PortN (5 Chars)                 |
                |________________________________________________|

                In every interval (for now 20 seconds) peers must send this message to the root.
                Every other peer that received this packet should append their (IP, port) to
                the packet and update Length.

            Hello Back:

                                    ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |           Number of Entries (2 Chars)          |
                |------------------------------------------------|
                |                 IPN (15 Chars)                 |
                |------------------------------------------------|
                |                PortN (5 Chars)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IP1 (15 Chars)                 |
                |------------------------------------------------|
                |                Port1 (5 Chars)                 |
                |------------------------------------------------|
                |                 IP0 (15 Chars)                 |
                |------------------------------------------------|
                |                Port0 (5 Chars)                 |
                |________________________________________________|

                Root in an answer to the Reunion Hello message will send this packet to the target node.
                In this packet, all the nodes (IP, port) exist in order by path traversal to target.


"""
from struct import *


class Packet:
    def __init__(self, version, type, length, source_ip, source_port, body):
        '''

        :param header: bytes
        :param version: '1'
        :param type: an integer from 1 to 5
        :param length: length of the body
        :param source_ip:
        :param source_port:
        :param body:
        '''
        self.version = version
        self.type = type
        self.length = length
        self.type = type
        self.source_ip = source_ip
        self.source_port = source_port
        self.body = body

    def get_version(self):
        """

        :return: Packet Version
        :rtype: int
        """
        return self.version

    def get_type(self):
        """

        :return: Packet type
        :rtype: int
        """
        return self.type

    def get_length(self):
        """

        :return: Packet length
        :rtype: int
        """
        return self.length

    def get_body(self):
        """

        :return: Packet body
        :rtype: str
        """
        return self.body

    def get_buf(self):
        """
        In this function, we will make our final buffer that represents the Packet with the Struct class methods.

        :return The parsed packet to the network format.
        :rtype: bytes
        """
        buff = b''
        buff += self.version.to_bytes(length=2, byteorder='big')
        buff += self.type.to_bytes(length=2, byteorder='big')
        buff += self.length.to_bytes(length=4, byteorder='big')
        ip_tokens = [int(x) for x in self.source_ip.split(sep='.')]
        for token in ip_tokens:
            buff += token.to_bytes(length=2, byteorder='big')
        buff += self.source_port.to_bytes(length=4, byteorder='big')
        buff += bytes(self.body, 'utf-8')

        return buff

    def get_source_server_ip(self):
        """

        :return: Server IP address for the sender of the packet.
        :rtype: str
        """
        return self.source_ip

    def get_source_server_port(self):
        """

        :return: Server Port address for the sender of the packet.
        :rtype: int
        """
        return self.source_port

    def get_source_server_address(self):
        """

        :return: Server address; The format is like ('192.168.001.001', '05335').
        :rtype: tuple
        """
        return self.get_source_server_ip(), self.get_source_server_port()

    def is_request(self):
        if self.body[:3] == 'RES':
            return False
        else:
            return True


class PacketFactory:
    """
    This class is only for making Packet objects.
    """

    @staticmethod
    def new_header(type, length, source_ip, source_port, version=1):
        bf = b''
        #pack_into(">b", bf, 0, version)
        #pack_into(">b", bf, 2, type)
        #pack_into(">b", bf, 4, length)
        #pack_into(">b", bf, 8, source_ip)
        #pack_into(">b", bf, 16, source_port)
        return bf

    @staticmethod
    def new_register_packet(type, source_server_address, address=(None, None)):
        """
        :param type: Type of Register packet
        :param source_server_address: Server address of the packet sender.
        :param address: If 'type' is 'request' we need an address; The format is like ('192.168.001.001', '05335').

        :type type: str
        :type source_server_address: tuple
        :type address: tuple

        :return New Register packet.
        :rtype Packet

        """
        '''
        frame = PacketFactory.new_header(type=2, length=(23 if type == 'REQ' else 6), \
                                         source_ip=source_server_address[0], source_port=source_server_address[1])
        frame.extend(type.encode('utf8'))
        if type == 'REQ':
            frame.extend(address[0].encode('utf8'))
            frame.extend(address[1].encode('utf8'))
        elif type == 'RES':
            frame.extend('ACK'.encode('utf8'))
        '''
        source_ip, source_port = source_server_address
        if type == 'REQ':
            return Packet(type=1, version=1, length=23, source_ip=source_ip, source_port=source_port,
                          body=type + address[0] + str(address[1]).zfill(5))
        elif type == 'RES':
            return Packet(type=1, version=1, length=6, source_ip=source_ip, source_port=source_port,
                          body=type + 'ACK')


    @staticmethod
    def new_advertise_packet(type, source_server_address, neighbour=(None, None)):
        """
        :param type: Type of Advertise packet
        :param source_server_address Server address of the packet sender.
        :param neighbour: The neighbour for advertise response packet; The format is like ('192.168.001.001', '05335').

        :type type: str
        :type source_server_address: tuple
        :type neighbour: tuple

        :return New advertise packet.
        :rtype Packet

        """
        '''
        frame = PacketFactory.new_header(type=2, length=(23 if type == 'REQ' else 4),
                                         source_ip=source_server_address[0], source_port=source_server_address[1])
        frame.extend(type.encode('utf8'))
        if type == 'RES':
            frame.extend('ACK'.encode('utf8'))
            frame.extend(neighbour[0].encode('utf8'))
            frame.extend(neighbour[1].encode('utf8'))
        '''
        source_ip, source_port = source_server_address
        if type == 'REQ':
            return Packet(type=2, version=1, length=3, source_ip=source_ip, source_port=source_port,
                          body='REQ')
        elif type == 'RES':
            return Packet(type=2, version=1, length=23, source_ip=source_ip, source_port=source_port,
                          body='RES' + neighbour[0] + str(neighbour[1]).zfill(5))


    @staticmethod
    def new_join_packet(source_server_address):
        """
        :param source_server_address: Server address of the packet sender.

        :type source_server_address: tuple

        :return New join packet.
        :rtype Packet

        """
        '''
        frame = PacketFactory.new_header(type=3, length=4,
                                         source_ip=source_server_address[0], source_port=source_server_address[1])
        frame.extend('JOIN'.encode('utf8'))
        '''
        source_ip, source_port = source_server_address
        return Packet(type=3, version=1, length=4, source_ip=source_ip, source_port=source_port, body='JOIN')


    @staticmethod
    def new_message_packet(message, source_server_address):
        """
        Packet for sending a broadcast message to the whole network.

        :param message: Our message
        :param source_server_address: Server address of the packet sender.

        :type message: str
        :type source_server_address: tuple

        :return: New Message packet.
        :rtype: Packet
        """
        '''
        frame = PacketFactory.new_header(type=4, length=len(message),
                                         source_ip=source_server_address[0], source_port=source_server_address[1])
        frame.extend(message.encode('utf8'))
        '''
        source_ip , source_port = source_server_address
        return Packet(type=4, version=1, length=len(message), source_ip=source_ip, source_port=source_port,
                      body=message)


    @staticmethod
    def new_reunion_packet(type, source_address, nodes_array):
        """
        :param type: Reunion Hello (REQ) or Reunion Hello Back (RES)
        :param source_address: IP/Port address of the packet sender.
        :param nodes_array: [(ip0, port0), (ip1, port1), ...] It is the path to the 'destination'.

        :type type: str
        :type source_address: tuple
        :type nodes_array: list

        :return New reunion packet.
        :rtype Packet
        """
        '''
        frame = PacketFactory.new_header(type=2, length=(23 if type == 'REQ' else 4), \
                                         source_ip=source_address[0], source_port=source_address[1])
        frame.extend(type.encode('utf8'))
        frame.extend(len(nodes_array).encode('utf8'))
        for ip, port in nodes_array:
            frame.extend(ip.encode('utf8'))
            frame.extend(port.encode('utf8'))
        '''
        body = type
        body += str(len(nodes_array)).zfill(2)
        source_ip, source_port = source_address
        for (ip, port) in nodes_array:
            body = body + ip + str(port).zfill(5)
        return Packet(type=5, version=1, length=len(body), source_ip=source_ip, source_port=source_port,
                      body=body)

    @staticmethod
    def parse_buffer(buffer):
        """
        In this function we will make a new Packet from input buffer with struct class methods.

        :param buffer: The buffer that should be parse to a validate packet format

        :return new packet
        :rtype: list of Packet

        """
        packets = []
        for data in buffer:
            header = data[:20]
            version = int.from_bytes(header[:2], byteorder='big')
            type = int.from_bytes(header[2:4], byteorder='big')
            length = int.from_bytes(header[4:8], byteorder='big')
            ip_token = header[8:16]
            source_ip = '.'.join(
                [str(int.from_bytes(ip_token[i:i+2], byteorder='big')).zfill(3) for i in range(0, 8, 2)]
            )
            source_port = int.from_bytes(header[16:20], byteorder='big')
            body = data[20:20+length].decode('utf-8')
            packets.append(Packet(version, type, length, source_ip, source_port, body))

        return packets






