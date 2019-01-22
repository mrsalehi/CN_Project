import collections
import time


class GraphNode:
    def __init__(self, address):
        """

        :param address: (ip, port)
        :type address: tuple

        """
        self.address = address
        self.parent = None
        self.alive = True
        self.children = []

    def set_parent(self, parent):
        self.parent = parent

    def set_address(self, new_address):
        self.address = new_address

    def __reset(self):
        self.address = None
        self.parent = None

    def add_child(self, child):
        self.children.append(child)


class NetworkGraph:
    def __init__(self, root):
        self.root = root
        root.alive = True
        self.nodes = [root]

    def find_live_node(self, sender):
        """
        Here we should find a neighbour for the sender.
        Best neighbour is the node who is nearest the root and has not more than one child.

        Code design suggestion:
            1. Do a BFS algorithm to find the target.

        Warnings:
            1. Check whether there is sender node in our NetworkGraph or not; if exist do not return sender node or
               any other nodes in it's sub-tree.

        :param sender: The node address we want to find best neighbour for it.
        :type sender: tuple

        :return: Best neighbour for sender.
        :rtype: GraphNode
        """
        visited, queue = set(), collections.deque([self.root])
        visited.add(self.root)
        while queue:
            v = queue.popleft()
            if v.address != sender:
                for u in v.children:
                    if u not in visited and u.alive:
                        if len(u.children) < 2:
                            return u
                        visited.add(u)
                        queue.append(u)

        return None

    def find_node(self, ip, port):
        for node in self.nodes:
            if node.address == (ip, port):
                return node

    def turn_on_node(self, node_address):
        ip, port = node_address
        node = self.find_node(ip, port)
        node.alive = True

    def turn_off_node(self, node_address):
        ip, port = node_address
        node = self.find_node(ip, port)
        node.alive = False

    def remove_node(self, node_address):
        ip, port = node_address
        node = self.find_node(ip, port)
        visited, queue = set(), collections.deque([node])
        visited.add(node)
        while queue:
            v = queue.popleft()
            for u in v.children:
                if u not in visited and u.alive:
                    u.alive = False
                    visited.add(u)
                    queue.append(u)

    def add_node(self, ip, port, father_address):
        """
        Add a new node with node_address if it does not exist in our NetworkGraph and set its father.

        Warnings:
            1. Don't forget to set the new node as one of the father_address children.
            2. Before using this function make sure that there is a node which has father_address.

        :param ip: IP address of the new node.
        :param port: Port of the new node.
        :param father_address: Father address of the new node

        :type ip: str
        :type port: int
        :type father_address: tuple


        :return:
        """
        node = GraphNode((ip, port))
        ip, port = father_address
        parent = self.find_node(ip, port)
        node.set_parent(parent)
        parent.add_child(node)
        self.nodes.append(node)
