from twisted.internet import threads
from twisted.internet.endpoints import TCP4ServerEndpoint

class Organization:
    def __init__(self, reactor):
        self.reactor = reactor
        self.nodes = []
        self.node_number = 0

    def port(self, number):
        return TCP4ServerEndpoint(self.reactor, number)

    def activate(self):
        self.nodes[1].listen()
        self.nodes[2].listen()

    def deactivate(self, agent):
        self.nodes[agent.node_number].stop()

    def start_loop(self, agents):
        """Start reactor thread main loop"""
        self.reactor.suggestThreadPoolSize(30)
        for agent in agents:
            agent.update_ams(agent.ams)
            agent.on_start()
            endpoint = TCP4ServerEndpoint(self.reactor, agent.aid.port)
            node = Node(endpoint, self.reactor, agent.agentInstance)
            node.listen()
            agent.ILP = node
            agent.node_number = self.node_number
            self.nodes.append(node)
            self.node_number += 1
        self.reactor.run()

    def start_single_agent(self, agent):
        agent.update_ams(agent.ams)
        agent.on_start()
        endpoint = TCP4ServerEndpoint(self.reactor, agent.aid.port)
        node = Node(endpoint, self.reactor, agent.agentInstance)
        node.listen()
        agent.ILP = node
        agent.node_number = self.node_number
        self.nodes.append(node)
        self.node_number += 1

    def stop_agent(self, agent):
        agent.cancle_ams(agent.ams)
        agent.ILP.stop()


class Node:
    def __init__(self, endpoint, clock, fact, stop=None):
        self.Factory = fact
        self._endpoint = endpoint
        self._listenStarting = None
        self._listeningPort = None
        self.activeTransports = []
        if stop is not None:
            print("Scheduling stop.", stop)
            clock.callLater(stop, self.stop)

    def listen(self):
        self._listenStarting = self._endpoint.listen(self.Factory)

        def setPort(port):
            self._listeningPort = port
            # print(port)

        def clear(whatever):
            self._listenStarting = None
            return whatever

        self._listenStarting.addCallback(setPort).addBoth(clear)

    def stop(self):
        if self._listenStarting is not None:
            self._listenStarting.cancel()
        if self._listeningPort is not None:
            self._listeningPort.stopListening()
        for transport in self.activeTransports[:]:
            transport.abortConnection()