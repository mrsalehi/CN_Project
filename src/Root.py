from Peer import Peer
from Stream import Stream
from Packet import Packet
from UserInterface import UserInterface
from tools.SemiNode import SemiNode
from tools.NetworkGraph import NetworkGraph, GraphNode
import time
import threading
from config import verbosity


class Root(Peer):
    def __init__(self, server_ip, server_port, user_interface=None, is_root=False, root_address=None):
        """
        The Peer object constructor.

        Code design suggestions:
            1. Initialise a Stream object for our Peer.
            2. Initialise a PacketFactory object.
            3. Initialise our UserInterface for interaction with user commandline.
            4. Initialise a Thread for handling reunion daemon.

        Warnings:
            1. For root Peer, we need a NetworkGraph object.
            2. In root Peer, start reunion daemon as soon as possible.

        :param server_ip: Server IP address for this Peer that should be pass to Stream.
        :param server_port: Server Port address for this Peer that should be pass to Stream.
        :param is_root: Specify that is this Peer root or not.
        :param root_address: Root IP/Port address if we are a client.

        :type server_ip: str
        :type server_port: int
        :type is_root: bool
        :type root_address: tuple
        """
        super(Root, self).__init__(server_ip=server_ip, server_port=server_port, user_interface=user_interface)
        self.start_user_interface()
        self.last_reunion_times = {}
        self.graph = NetworkGraph(GraphNode(self.server_address))
        self.t_run = threading.Thread(target=self.run, args=())
        self.t_run.start()
        self.t_run_reunion_daemon = threading.Thread(target=self.run_reunion_daemon, args=())
        self.t_run_reunion_daemon.start()

    def handle_user_interface_buffer(self):
        """
        In every interval, we should parse user command that buffered from our UserInterface.
        All of the valid commands are listed below:
            1. Register:  With this command, the client send a Register Request packet to the root of the network.
            2. Advertise: Send an Advertise Request to the root of the network for finding first hope.
            3. SendMessage: The following string will be added to a new Message packet and broadcast through the network.
        :return:
        """
        buff = self.user_interface.buffer
        for msg in buff:
            msg_split = msg.split()
            if msg_split[0] == 'send':
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
        while True:
            in_buff = self.stream.read_in_buf()
            self.handle_user_interface_buffer()
            packets = self.packet_factory.parse_buffer(in_buff)
            for packet in packets:
                self.handle_packet(packet)
            self.stream.send_out_buf_messages()
            self.stream.clear_in_buff()
            time.sleep(2)

    def run_reunion_daemon(self):
        """
        In this function, we will handle all Reunion actions.
        Code design suggestions:
            2. If it's the root Peer, in every interval check the latest Reunion packet arrival time from every node;
               If time is over for the node turn it off (Maybe you need to remove it from our NetworkGraph).
            3. If it's a non-root peer split the actions by considering whether we are waiting for Reunion Hello Back
               Packet or it's the time to send new Reunion Hello packet.
        Warnings:
            1. If we are the root of the network in the situation that we want to turn a node off, make sure that you will not
               advertise the nodes sub-tree in our GraphNode.
            3. For choosing time intervals you should wait until Reunion Hello or Reunion Hello Back arrival,
               pay attention that our NetworkGraph depth will not be bigger than 8. (Do not forget main loop sleep time)

        :return:
        """
        turn_off_time = 16
        remove_time = 60
        while True:
            t = time.time()
            for node_address, last_reunion_time in self.last_reunion_times.copy().items():
                if t - last_reunion_time > remove_time:
                    print('removing node {}'.format(node_address))
                    self.graph.remove_node(node_address)
                    del self.last_reunion_times[node_address]
                    node = self.stream.get_node_by_server(node_address[0], node_address[1], True)
                    self.stream.remove_node(node)
                    # TODO: remove node ??
                elif turn_off_time < t - last_reunion_time < remove_time:
                    graph_node = self.graph.find_node(node_address[0], node_address[1])
                    if graph_node.alive:
                        print('turning off node {}'.format(node_address))
                    graph_node.alive = False
            time.sleep(2)

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

    def __check_registered(self, source_address):
        """
        If the Peer is the root of the network we need to find that is a node registered or not.

        :param source_address: Unknown IP/Port address.
        :type source_address: tuple

        :return:
        """
        for node in self.stream.nodes:
            if source_address == node.get_server_address() and node.is_register:
                return True
        return False

    def _handle_advertise_packet(self, packet):
        """
        For advertising peers in the network, It is peer discovery message.

        Request:
            We should act as the root of the network and reply with a neighbour address in a new Advertise Response packet.

        Warnings:
            2. The addresses which still haven't registered to the network can not request any peer discovery message.
            3. Maybe it's not the first time that the source of the packet sends Advertise Request message. This will happen
               in rare situations like Reunion Failure. Pay attention, don't advertise the address to the packet sender
               sub-tree.

        :param packet: Arrived register packet

        :type packet Packet

        :return:
        """
        t = time.time()
        if packet.is_request():
            source_ip, source_port = packet.get_source_server_ip(), packet.get_source_server_port()
            print('\t Recvd Adv Packet from ', source_ip, source_port)
            if self.__check_registered((source_ip, source_port)):
                parent_ip, parent_port = self._get_neighbour(sender=(source_ip, source_port))
                # print('parent ip and port: ', parent_ip, parent_port)
                adv_res_pack = self.packet_factory.new_advertise_packet('RES', self.server_address,
                                                                        neighbour=(parent_ip, parent_port))
                try:
                    self.stream.add_message_to_out_buff((source_ip, source_port), adv_res_pack.get_buf(), True)
                except Exception:
                    print('Oops! Seems that you are adding a message to nonexistent buffer!')
                graph_node = self.graph.find_node(source_ip, source_port)
                if graph_node is None:
                    self.graph.add_node(source_ip, source_port, (parent_ip, parent_port))
                else:
                    prev_parent = graph_node.parent
                    prev_parent_ip, prev_parent_port = prev_parent.address
                    print('prev_parent of ', source_ip, source_port, ' was: ', prev_parent_ip, prev_parent_port)
                    prev_parent.children.remove(graph_node)
                    print('new parent for ', source_ip, source_port, ': ', parent_ip, parent_port)
                    new_parent = self.graph.find_node(parent_ip, parent_port)
                    graph_node.parent = new_parent
                    new_parent.children.append(graph_node)
                    graph_node.alive = True
                self.last_reunion_times[(source_ip, source_port)] = t

    def _handle_register_packet(self, packet):
        """
        For registration a new node to the network at first we should make a Node with stream.add_node for'sender' and
        save it.

        Code design suggestion:
            1.For checking whether an address is registered since now or not you can use SemiNode object except Node.


        :param packet: Arrived register packet
        :type packet Packet
        :return:
        """
        if packet.is_request():
            address = (packet.get_source_server_ip(), packet.get_source_server_port())
            if not self.__check_registered(address):
                self.stream.add_node(address, set_register_connection=True)
                reg_res_pack = self.packet_factory.new_register_packet('RES', self.server_address)
                self.stream.add_message_to_out_buff(address, reg_res_pack.get_buf(), True)

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
        super(Root, self)._handle_message_packet(packet)

    def _handle_reunion_packet(self, packet):
        """
        In this function we should handle Reunion packet was just arrived.

        Reunion Hello:
            If you are root Peer you should answer with a new Reunion Hello Back packet.
            At first extract all addresses in the packet body and append them in descending order to the new packet.
            You should send the new packet to the first address in the arrived packet.
        Warnings:
            1. Every time adding or removing an address from packet don't forget to update Entity Number field.
            2. If you are the root, update last Reunion Hello arrival packet from the sender node and turn it on.

        :param packet: Arrived reunion packet
        :return:
        """
        # print('reunion packet recvd...')
        t = time.time()
        body = packet.get_body()
        type = body[:3]
        n_entries = int(body[3:5])
        entries = body[5:]
        length = len(entries)
        if type == 'REQ':
            nodes_array = [(entries[i:i + 15], int(entries[i + 15:i + 20])) for i in range(0, length, 20)]
            last_node = nodes_array[-1]
            sender = nodes_array[0]
            self.graph.turn_on_node(sender)
            nodes_array = list(reversed(nodes_array))
            self.last_reunion_times[sender] = t
            reunion_packet = self.packet_factory.new_reunion_packet('RES', self.server_address, nodes_array)
            self.stream.add_message_to_out_buff(last_node, message=reunion_packet.get_buf())

    def _handle_join_packet(self, packet):
        address = (packet.get_source_server_ip(), packet.get_source_server_port())
        self.stream.add_node(address)

    def _get_neighbour(self, sender):
        """
        Finds the best neighbour for the 'sender' from the network_nodes array.
        This function only will call when you are a root peer.

        Code design suggestion:
            1. Use your NetworkGraph find_live_node to find the best neighbour.

        :param sender: Sender of the packet
        :return: The specified neighbour for the sender; The format is like ('192.168.001.001', '05335').
        """
        parent = self.graph.find_live_node(sender)
        return parent.address
