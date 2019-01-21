from .Stream import Stream
from .Packet import Packet, PacketFactory
from .UserInterface import UserInterface
from .tools.SemiNode import SemiNode
from .tools.NetworkGraph import NetworkGraph, GraphNode
import time
import threading

"""
    Peer is our main object in this project.
    In this network Peers will connect together to make a tree graph.
    This network is not completely decentralised but will show you some real-world challenges in Peer to Peer networks.
    
"""


class Peer:
    def __init__(self, server_ip, server_port, is_root=False, root_address=None):
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
        self.server_address = (server_ip, server_port)
        self.stream = Stream(server_ip, server_port)
        self.packet_factory = PacketFactory()
        self.root_address = root_address
        self.is_root = is_root
        self.parent = None  # address of the parent node which will be a tuple
        self._last_reunion_time = None  # last time a reunion hello packet was sent
        self._reunion_mode = None  # either 'pending' or 'accepted'

        if is_root:
            root = GraphNode((server_ip, server_port))
            self.graph = NetworkGraph(root)
            pass
        else:
            self._register()

        self.user_interface = None
        self.start_user_interface()
        self.t_run = threading.Thread(target=self.run, args=())  # TODO: Not sure about this
        self.t_run.run()
        self.t_run_reunion_daemon = threading.Thread(target=self.run_reunion_daemon, args=())
        self.t_run_reunion_daemon.run()

    def _register(self):
        self.stream.add_node(self.root_address, set_register_connection=True)
        reg_pack = self.packet_factory.new_register_packet()  # TODO: fill-in the parameters.
        self.stream.add_message_to_out_buff(self.root_address, reg_pack)
        self.stream.send_out_buf_messages()

        # TODO: inaro pak kon
        time.sleep(0.5)  # TODO: check this out!
        in_buff = self.stream.read_in_buf()
        reg_response_pack = self.packet_factory.parse_buffer(in_buff)  # TODO: check if the response is valid
        # advertise
        adv_pack = self.packet_factory.new_advertise_packet() # TODO
        self.stream.add_message_to_out_buff(self.root_address, adv_pack)
        self.stream.send_out_buf_messages()
        self.mode = True  # TODO: Not sure about this!!

    def start_user_interface(self):
        """
        For starting UserInterface thread.

        :return:
        """
        self.user_interface = UserInterface()

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
        pass

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
            if self.mode:
                in_buff = self.stream.read_in_buf()
                packet = self.packet_factory.parse_buffer(in_buff)
                self.handle_packet(packet)
                self.stream.send_out_buf_messages()
                time.sleep(2)
            else:
                pass

    def run_reunion_daemon(self):
        """

        In this function, we will handle all Reunion actions.

        Code design suggestions:
            1. Check if we are the network root or not; The actions are identical.
            2. If it's the root Peer, in every interval check the latest Reunion packet arrival time from every node;
               If time is over for the node turn it off (Maybe you need to remove it from our NetworkGraph).
            3. If it's a non-root peer split the actions by considering whether we are waiting for Reunion Hello Back
               Packet or it's the time to send new Reunion Hello packet.

        Warnings:
            1. If we are the root of the network in the situation that we want to turn a node off, make sure that you will not
               advertise the nodes sub-tree in our GraphNode.
            2. If we are a non-root Peer, save the time when you have sent your last Reunion Hello packet; You need this
               time for checking whether the Reunion was failed or not.
            3. For choosing time intervals you should wait until Reunion Hello or Reunion Hello Back arrival,
               pay attention that our NetworkGraph depth will not be bigger than 8. (Do not forget main loop sleep time)
            4. Suppose that you are a non-root Peer and Reunion was failed, In this time you should make a new Advertise
               Request packet and send it through your register_connection to the root; Don't forget to send this packet
               here, because in the Reunion Failure mode our main loop will not work properly and everything will be got stock!

        :return:
        """
        while True:
            time.sleep(4)
            if self.is_root:
                pass
            else:
                reunion_packet = self.packet_factory.new_reunion_packet()  # TODO: Not sure about this
                self.stream.add_message_to_out_buff(self.parent, reunion_packet)
                self.last_reunion_time = time.time()
                self._reunion_mode = 'pending'

    def send_broadcast_packet(self, broadcast_packet):
        """

        For setting broadcast packets buffer into Nodes out_buff.

        Warnings:
            1. Don't send Message packets through register_connections.

        :param broadcast_packet: The packet that should be broadcast through the network.
        :type broadcast_packet: Packet

        :return:
        """
        msg = Packet
        for node in self.stream.nodes:
            self.stream.add_message_to_out_buff(node.get_server_address(), message=broadcast_packet)

    def handle_packet(self, packet):
        """

        This function act as a wrapper for other handle_###_packet methods to handle the packet.

        Code design suggestion:
            1. It's better to check packet validation right now; For example Validation of the packet length.

        :param packet: The arrived packet that should be handled.

        :type packet Packet

        """
        type = packet.get_type()
        if type is 'Register':
            self.__handle_register_packet(packet)
        elif type is 'Advertise':
            self.__handle_advertise_packet(packet)
        elif type is 'Join':
            self.__handle_join_packet(packet)
        elif type is 'Message':
            self.__handle_message_packet(packet)
        elif type is 'Reunion':
            self.__handle_reunion_packet(packet)
        else:
            raise NotImplemented

    def __check_registered(self, source_address):
        """
        If the Peer is the root of the network we need to find that is a node registered or not.

        :param source_address: Unknown IP/Port address.
        :type source_address: tuple

        :return:
        """
        if self.is_root:
            for node in self.stream.nodes:
                if source_address == node.get_server_address():
                    return True
        return False

    def __handle_advertise_packet(self, packet):
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
        if self.is_root:
            if packet.is_request():
                source_ip, source_port = packet.get_source_server_ip(), int(packet.get_source_server_port())
                address = (source_ip, source_port)
                parent_ip, parent_port = self.__get_neighbour(sender=address)
                adv_res_pack = self.packet_factory.new_advertise_packet()  # TODO: fill-in the parameters
                self.stream.add_message_to_out_buff(address, adv_res_pack)
                self.graph.add_node(source_ip, source_port, (parent_ip, parent_port))
            else:
                pass
        else:
            if not packet.is_request():
                body = packet.get_body()
                parent_ip = body[3: 18]
                parent_port = body[-5:]
                join_pack = self.packet_factory.new_join_packet()  # TODO: fill-in the parameters
                address = (parent_ip, parent_port)
                self.stream.add_node(address)
                self.stream.add_message_to_out_buff(address, join_pack)
            else:
                pass
        pass

    def __handle_register_packet(self, packet):
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
        if not self.is_root:
            if packet.is_request():
                pass
            else:
                # TODO: check register response packet
                adv_pack = self.packet_factory.new_advertise_packet()  # TODO
                self.stream.add_message_to_out_buff(self.root_address, adv_pack)
        else:
            if not packet.is_request():
                pass
            else:
                address = (packet.get_source_server_ip(), packet.get_source_server_port())
                self.stream.add_node(address, set_register_connection=True)
                register_response_packet = self.packet_factory.new_register_packet()  # TODO: fill-in the parameters
                self.stream.add_message_to_out_buff(address, register_response_packet)

    def __check_neighbour(self, address):
        """
        It checks is the address in our neighbours array or not.

        :param address: Unknown address

        :type address: tuple

        :return: Whether is address in our neighbours or not.
        :rtype: bool
        """
        for node in self.stream.nodes:
            if node.get_server_address() == address:
                return True
        return False

    def __handle_message_packet(self, packet):
        """
        Only broadcast message to the other nodes.

        Warnings:
            1. Do not forget to ignore messages from unknown sources.
            2. Make sure that you are not sending a message to a register_connection.

        :param packet: Arrived message packet

        :type packet Packet

        :return:
        """
        address = (packet.get_source_server_ip(), packet.get_source_server_port())
        brdcast_packet = self.packet_factory.new_message_packet()  # TODO: fill-in the parameters
        if address in self.stream.nodes.keys():
            for node in self.stream.nodes:
                node_address = node.get_server_address()
                if node_address != address:
                    self.stream.add_message_to_out_buff(address=node_address, message=brdcast_packet)
        else:
            pass  # TODO: Raise an error if there is no node with given address

    def __handle_reunion_packet(self, packet):
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
        address = (packet.get_source_server_ip(), packet.get_source_server_port())
        if self.is_root:
            reunion_back_packet = self.packet_factory.new_reunion_packet()  # make reunion hello back
            for node in self.stream.nodes:
                self.stream.add_message_to_out_buff(node.get_server_address(), reunion_back_packet)
        else:
            body = packet.get_body()
            str = body[:3]
            body = packet.get_body()
            n_entries = body[3:5]  # TODO: Make sure if it is the number of ip,port pairs in the msg.
            entries = body[5:]
            l = len(entries)

            if str == 'REQ':
                reunion_packet = self.packet_factory.new_reunion_packet()  # TODO: fill-in the parameters
                # TODO: append the peer's address to the end of message
                msg = None # TODO: Convert the packet to byte message
                self.stream.add_message_to_out_buff(self.parent, message=msg)
            elif str == 'RES':
                if l == 20:  # we are the end node!
                    self._reunion_mode = 'acceptance'
                else:  # we are not the end node! forward the packet!
                    entries = entries[20:]
                    nodes_array = [(entries[i:i+15], entries[i+15:i+20]) for i in range(n_entries)]
                    next_node_addr = nodes_array[0]
                    reunion_packet = self.packet_factory.\
                        new_reunion_packet('RES', self.server_address, nodes_array)  ## TODO: fill-in the parameters

                    msg = None # TODO: Convert the packet to byte message
                    self.stream.add_message_to_out_buff(next_node_addr, message=msg)
            else:
                pass  # TODO: Raise an error in this case

    def __handle_join_packet(self, packet):
        """
        When a Join packet received we should add a new node to our nodes array.
        In reality, there is a security level that forbids joining every node to our network.

        :param packet: Arrived register packet.


        :type packet Packet

        :return:
        """
        address = (packet.get_source_server_ip(), packet.get_source_server_port())
        self.stream.add_node(address)
        pass

    def __get_neighbour(self, sender):
        """
        Finds the best neighbour for the 'sender' from the network_nodes array.
        This function only will call when you are a root peer.

        Code design suggestion:
            1. Use your NetworkGraph find_live_node to find the best neighbour.

        :param sender: Sender of the packet
        :return: The specified neighbour for the sender; The format is like ('192.168.001.001', '05335').
        """
        if self.is_root:
            return None
        # The node is the root in this case
        parent = self.graph.find_live_node(sender)
        return parent.address
