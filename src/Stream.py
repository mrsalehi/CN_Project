from tools.simpletcp.tcpserver import TCPServer

from tools.Node import Node
import threading


class Stream:

    def __init__(self, ip, port):
        """
        The Stream object constructor.

        Code design suggestion:
            1. Make a separate Thread for your TCPServer and start immediately.


        :param ip: 15 characters
        :param port: 5 characters
        """
        def callback(address, queue, data):
            """
            The callback function will run when a new data received from server_buffer.

            :param address: Source address.
            :param queue: Response queue.
            :param data: The data received from the socket.
            :return:
            """
            queue.put(bytes('ACK', 'utf8'))
            self._server_in_buf.append(data)

        self.tcp_server = TCPServer(mode='localhost', port=port, read_callback=callback)
        self.t_tcp_server = threading.Thread(target=self.tcp_server.run, args=())
        self.t_tcp_server.start()
        #print('Inside stream after thread start')
        self.ip = Node.parse_ip(ip)
        self.port = Node.parse_port(port)
        self.nodes = []
        self._server_in_buf = []

    def get_server_address(self):
        """

        :return: Our TCPServer address
        :rtype: tuple
        """
        return self.ip, self.port

    def clear_in_buff(self):
        """
        Discard any data in TCPServer input buffer.

        :return:
        """
        self._server_in_buf.clear()

    def add_node(self, server_address, set_register_connection=False):
        """
        Will add new a node to our Stream.

        :param server_address: New node TCPServer address.
        :param set_register_connection: Shows that is this connection a register_connection or not.

        :type server_address: tuple
        :type set_register_connection: bool

        :return:
        """
        print("node ", server_address, set_register_connection, " added to stream nodes")
        server_ip, server_port = server_address
        server_ip = Node.parse_ip(server_ip)
        self.nodes.append(Node(server_address=(server_ip, server_port), set_register=set_register_connection))

    def remove_node(self, node):
        """
        Remove the node from our Stream.

        Warnings:
            1. Close the node after deletion.

        :param node: The node we want to remove.
        :type node: Node

        :return:
        """
        self.nodes.remove(node)
        node.close()

    def get_node_by_server(self, ip, port, is_register=False):
        """

        Will find the node that has IP/Port address of input.

        Warnings:
            1. Before comparing the address parse it to a standard format with Node.parse_### functions.

        :param ip: input address IP
        :param port: input address Port

        :return: The node that input address.
        :rtype: Node
        """
        # print('List of nodes in stream ', self.get_server_address())
        # for node in self.nodes:
        #     print(node.get_server_address(), node.is_register)
        node_address = (Node.parse_ip(ip), port)
        for node in self.nodes:
            if node.get_server_address() == node_address and node.is_register == is_register:
                return node
        return None

    def add_message_to_out_buff(self, address, message, is_register=False):
        """
        In this function, we will add the message to the output buffer of the node that has the input address.
        Later we should use send_out_buf_messages to send these buffers into their sockets.

        :param address: Node address that we want to send the message
        :param message: Message we want to send

        Warnings:
            1. Check whether the node address is in our nodes or not.

        :return:
        """
        ip, port = address
        node = self.get_node_by_server(ip, port, is_register)
        if node is not None:
            node.add_message_to_out_buff(message)
        else:
            raise Exception

    def read_in_buf(self):
        """
        Only returns the input buffer of our TCPServer.

        :return: TCPServer input buffer.
        :rtype: list
        """
        return self._server_in_buf

    def send_messages_to_node(self, node):
        """
        Send buffered messages to the 'node'

        Warnings:
            1. Insert an exception handler here; Maybe the node socket you want to send the message has turned off and
            you need to remove this node from stream nodes.

        :param node:
        :type node Node

        :return:
        """
        try:
            node.send_message()
        except Exception:
            print('Can not send to {} {}... Removing the node from stream'.
                  format(node.get_server_address(), node.is_register))
            self.nodes.remove(node)
            raise Exception

    def send_out_buf_messages(self, only_register=False):
        """
        In this function, we will send hole out buffers to their own clients.

        :return:
        """
        disconnected_nodes = []
        for node in self.nodes.copy():
            try:
                self.send_messages_to_node(node)
            except Exception:
                disconnected_nodes.append(node.get_server_address())
        return disconnected_nodes

