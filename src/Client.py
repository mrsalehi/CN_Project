from Peer import Peer
from Stream import Stream
from Packet import Packet, PacketFactory
from UserInterface import UserInterface
from tools.SemiNode import SemiNode
from tools.NetworkGraph import NetworkGraph, GraphNode
from config import verbosity
import time
import threading
import sys


class Client(Peer):
    def __init__(self, server_ip, server_port, is_root=False, root_address=None):
        """
        The Peer object constructor.

        Code design suggestions:
            1. Initialise a Stream object for our Peer.
            2. Initialise a PacketFactory object.
            3. Initialise our UserInterface for interaction with user commandline.
            4. Initialise a Thread for handling reunion daemon.

        Warnings:
            3. In client Peer, we need to connect to the root of the network, Don't forget to set this connection
               as a register_connection.


        :param server_ip: Server IP address for this Peer that should be pass to Stream.
        :param server_port: Server Port address for this Peer that should be pass to Stream.
        :param is_root: Specify that is this Peer root or not.
        :param root_address: Root IP/Port address if we are a client.

        :type server_ip: str
        :type server_port: int
        :type is_root: bool
        :type root_address: tuple
        """
        super(Client, self).__init__(server_ip, server_port, is_root, root_address)
        self.parent = None  # address of the parent node which will be a tuple
        self.last_reunion_time = 0  # last time a reunion hello packet was sent
        self._reunion_mode = None  # either 'pending' or 'acceptance' after registration
        self.__is_disconnected = False
        self.root_address = root_address
        self.valid_time = 32
        self.adv_sent = False
        self.t_run = threading.Thread(target=self.run, args=())
        self.t_run.start()
        self.t_reunion_daemon = threading.Thread(target=self.run_reunion_daemon, args=())
        self.is_registered = False
        self._register()
        self._advertise()
        self.t_run.join()
        self.t_reunion_daemon.join()

    def _register(self):
        self.stream.add_node(self.root_address, set_register_connection=True)
        reg_pack = self.packet_factory.new_register_packet('REQ', self.server_address, self.server_address)
        self.stream.add_message_to_out_buff(self.root_address, reg_pack.get_buf(), True)

    def _advertise(self):
        adv_pack = self.packet_factory.new_advertise_packet('REQ', self.server_address)
        self.stream.add_message_to_out_buff(self.root_address, adv_pack.get_buf(), True)

    def handle_user_interface_buffer(self):
        """
        In every interval, we should parse user command that buffered from our UserInterface.
        All of the valid commands are listed below:
            1. Register:  With this command, the client send a Register Request packet to the root of the network.
            2. Advertise: Send an Advertise Request to the root of the network for finding first hope.
            3. SendMessage: The following string will be added to a new Message packet and broadcast through the network.

        Warnings:
            1. Ignore irregular commands from the user.
            2. Don't forget to clear our UserInterface buffer.
        :return:
        """
        buff = self.user_interface.buffer
        for msg in buff:
            msg_split = msg.split()
            if msg_split[0] == 'Register':
                self._register()
            elif msg_split[0] == 'Advertise':
                self._advertise()
            elif msg_split[0] == 'send':
                brd_cast_packet = self.packet_factory.new_message_packet(msg_split[1],
                                                                         source_server_address=self.server_address)
                self.send_broadcast_packet(brd_cast_packet)

        self.user_interface.buffer.clear()

    def run(self):
        """
        The main loop of the program.

        Code design suggestions:
            1. Parse server in_buf of the stream.
            2. Handle all packets received from our Stream server.
            3. Parse user_interface_buffer to make message packets.
            4. Send packets stored in nodes buffer of our Stream object.
            5. ** sleep the current thread for 2 seconds **

        Warnings:
            1. At first check reunion daemon condition; Maybe we have a problem in this time
               and so we should hold any actions until Reunion acceptance.
            2. In every situation checkout Advertise Response packets; even is Reunion in failure mode or not

        :return:
        """
        self.start_user_interface()
        while True:
            if self.__is_disconnected:
                sys.exit()
            t = time.time()
            self.handle_user_interface_buffer()
            in_buff = self.stream.read_in_buf()
            packets = self.packet_factory.parse_buffer(in_buff)
            for packet in packets:
                type = packet.get_type()
                if self.is_registered:
                    if (t - self.last_reunion_time <= self.valid_time and self._reunion_mode == 'pending') or \
                    (type == 2) or (self._reunion_mode == 'acceptance'):
                        self.handle_packet(packet)
                else:
                    if packet.get_type() == 1:
                        self.handle_packet(packet)

            self.__send()
            self.stream.clear_in_buff()
            time.sleep(2)

    def run_reunion_daemon(self):
        """

        In this function, we will handle all Reunion actions.

        Code design suggestions:
            3. If it's a non-root peer split the actions by considering whether we are waiting for Reunion Hello Back
               Packet or it's the time to send new Reunion Hello packet.

        Warnings:
            2. If we are a non-root Peer, save the time when you have sent your last Reunion Hello packet; You need this
               time for checking whether the Reunion was failed or not.
            3. For choosing time intervals you should wait until Reunion Hello or Reunion Hello Back arrival,
               pay attention that our NetworkGraph depth will not be bigger than 8. (Do not forget main loop sleep time)
            4. Suppose that you are a non-root Peer and Reunion was failed, In this time you should make a new Advertise
               Request packet and send it through your register_connection to the root; Don't forget to send this packet
               here, because in the Reunion Failure mode our main loop will not work properly and everything will be got stock!

        :return:
        """
        self.last_reunion_time = time.time()
        while True:
            time.sleep(4)
            t = time.time()
            if self._reunion_mode == 'pending':
                #if not self.__is_disconneted:
                    #print('No response after {} seconds...'.format(t - self.last_reunion_time))
                if t - self.last_reunion_time > self.valid_time:
                    print('Elapsed time is more than {} sec. Trying to advertise again...'.format(self.valid_time))
                    adv_packet = self.packet_factory.new_advertise_packet('REQ', self.server_address)
                    try:
                        self.stream.add_message_to_out_buff(self.root_address, adv_packet.get_buf(), True)
                        try:
                            self.stream.send_messages_to_node(
                                self.stream.get_node_by_server(self.root_address[0], self.root_address[1], True))
                        except Exception:
                            print('Can not advertise to root!')
                            self.__is_disconnected = True
                            sys.exit()
                    except Exception:
                        print('Out buffer does not exist!')
                        sys.exit()

            else:
                reunion_packet = self.packet_factory.new_reunion_packet('REQ', source_address=self.server_address,
                                                                        nodes_array=[self.server_address])
                self.stream.add_message_to_out_buff(self.parent, reunion_packet.get_buf())
                #print('Sending reunion packet...')
                #print ('Elapsed time since last reunion: ', t - self.last_reunion_time)
                self.last_reunion_time = t
                self._reunion_mode = 'pending'

    def handle_packet(self, packet):
        """

        This function act as a wrapper for other handle_###_packet methods to handle the packet.

        Code design suggestion:
            1. It's better to check packet validation right now; For example Validation of the packet length.

        :param packet: The arrived packet that should be handled.

        :type packet Packet

        """
        type = packet.get_type()
        if verbosity == 1:
            if type != 5:
                print("Recvd packet body: ", packet.get_body())
                print('Recvd packet type: ', type)
        if type == 1:
            self._handle_register_packet(packet)
        elif type == 2:
            self._handle_advertise_packet(packet)
        elif type == 3:
            self._handle_join_packet(packet)
        elif type == 4:
            self._handle_message_packet(packet)
        elif type == 5:
            self._handle_reunion_packet(packet)
        else:
            raise NotImplemented

    def _handle_advertise_packet(self, packet):
        """
        For advertising peers in the network, It is peer discovery message.

        Request:
            We should act as the root of the network and reply with a neighbour address in a new Advertise Response packet.

        Response:
            When an Advertise Response packet type arrived we should update our parent peer and send a Join packet to the
            new parent.

        Code design suggestion:
            1. Start the Reunion daemon thread when the first Advertise Response packet received.
            2. When an Advertise Response message arrived, make a new Join packet immediately for the advertised address.

        Warnings:
            1. Don't forget to ignore Advertise Request packets when you are a non-root peer.
            2. The addresses which still haven't registered to the network can not request any peer discovery message.
            3. Maybe it's not the first time that the source of the packet sends Advertise Request message. This will happen
               in rare situations like Reunion Failure. Pay attention, don't advertise the address to the packet sender
               sub-tree.
            4. When an Advertise Response packet arrived update our Peer parent for sending Reunion Packets.

        :param packet: Arrived register packet

        :type packet Packet

        :return:
        """
        if not packet.is_request():
            body = packet.get_body()
            parent_ip = body[3: 18]
            parent_port = int(body[-5:])
            join_pack = self.packet_factory.new_join_packet(self.server_address)
            parent_address = (parent_ip, parent_port)
            print('parent address: ', parent_address)
            self.parent = parent_address
            self.stream.add_node(parent_address)
            self.stream.add_message_to_out_buff(parent_address, join_pack.get_buf())
            self._reunion_mode = 'acceptance'
            if not self.adv_sent:
                self.adv_sent = True
                self.t_reunion_daemon.start()

    def _handle_message_packet(self, packet):
        """
        Only broadcast message to the other nodes.

        Warnings:
            1. Do not forget to ignore messages from unknown sources.
            2. Make sure that you are not sending a message to a register_connection.

        :param packet: Arrived message packet

        :type packet Packet

        :return:
        """
        super(Client, self)._handle_message_packet(packet)

    def _handle_reunion_packet(self, packet):
        """
        In this function we should handle Reunion packet was just arrived.

        Reunion Hello:
            If you are root Peer you should answer with a new Reunion Hello Back packet.
            At first extract all addresses in the packet body and append them in descending order to the new packet.
            You should send the new packet to the first address in the arrived packet.
            If you are a non-root Peer append your IP/Port address to the end of the packet and send it to your parent.

        Reunion Hello Back:
            Check that you are the end node or not; If not only remove your IP/Port address and send the packet to the next
            address, otherwise you received your response from the root and everything is fine.

        Warnings:
            1. Every time adding or removing an address from packet don't forget to update Entity Number field.
            2. If you are the root, update last Reunion Hello arrival packet from the sender node and turn it on.
            3. If you are the end node, update your Reunion mode from pending to acceptance.


        :param packet: Arrived reunion packet
        :return:
        """
        body = packet.get_body()
        type = body[:3]  # either 'RES' or 'REQ'
        n_entries = body[3:5]
        entries = body[5:]
        length = len(entries)
        #print('reunion ' + type + ' ' +  entries)
        if type == 'REQ':
            nodes_array = [(entries[i:i + 15], int(entries[i + 15:i + 20])) for i in range(0, length, 20)]
            nodes_array.append(self.server_address)
            reunion_packet = self.packet_factory. \
                new_reunion_packet('REQ', self.server_address, nodes_array)
            self.stream.add_message_to_out_buff(self.parent, message=reunion_packet.get_buf())
        elif type == 'RES':
            if length == 20:  # we are the end node!
                self._reunion_mode = 'acceptance'
            else:  # we are not the end node! forward the packet!
                entries = entries[20:]
                length -= 20
                nodes_array = [(entries[i:i + 15], int(entries[i + 15:i + 20])) for i in range(0, length, 20)]
                next_node_addr = nodes_array[0]
                reunion_packet = self.packet_factory. \
                    new_reunion_packet('RES', self.server_address, nodes_array)
                self.stream.add_message_to_out_buff(next_node_addr, message=reunion_packet.get_buf())
        else:
            raise NotImplementedError

    def _handle_join_packet(self, packet):
        """
        When a Join packet received we should add a new node to our nodes array.
        In reality, there is a security level that forbids joining every node to our network.

        :param packet: Arrived register packet.


        :type packet Packet

        :return:
        """
        address = (packet.get_source_server_ip(), packet.get_source_server_port())
        self.stream.add_node(address)

    def _handle_register_packet(self, packet):
        """
        For registration a new node to the network at first we should make a Node with stream.add_node for'sender' and
        save it.

        Code design suggestion:
            1.For checking whether an address is registered since now or not you can use SemiNode object except Node.

        Warnings:
            1. Don't forget to ignore Register Request packets when you are a non-root peer.

        :param packet: Arrived register packet
        :type packet Packet
        :return:
        """
        if not packet.is_request():
            self.is_registered = True

    def __send(self):
        disconnected_nodes = self.stream.send_out_buf_messages()
        if self.parent in disconnected_nodes:
            adv_packet = self.packet_factory.new_advertise_packet('REQ', self.server_address)
            self.stream.add_message_to_out_buff(self.root_address, adv_packet.get_buf(), True)
            print('sending advertise to root...')
            try:
                self.stream.send_messages_to_node(
                    self.stream.get_node_by_server(self.root_address[0], self.root_address[1], True))
            except Exception:
                print('Can not advertise to root!')
                self.__is_disconnected = True

