from packet import DataPacket
from packet import AckPacket

class Device:
    def __init__(self, ip):
        self.ip = ip
        self.links = []

    def add_link(self, link):
        self.links.append(link)

class Host(Device):
    def __init__(self, ip):
        Device.__init__(self, ip)
        self.send_data_reactivate = {}
        self.unacknowledged_packets = {}
        self.window_size = {}

    def generate_packets(self, destination, window_size, first_packet_id):
        packets = []
        for i in range(first_packet_id, first_packet_id + window_size):
            packets.append(DataPacket(i, self.ip, destination))
        return packets

    def sendData(self, data, destination, env):
        self.window_size[destination] = 10
        self.unacknowledged_packets[destination] = 0
        self.send_data_reactivate[destination] = env.event()
        next_packet_id = 0

        currData = data
        while currData > 0:
            packets = self.generate_packets(destination, self.window_size[destination], next_packet_id)
            next_packet_id += self.window_size[destination]
            self.unacknowledged_packets[destination] += self.window_size[destination]
            currData -= self.window_size[destination] * DataPacket.size
            env.process(self.links[0].send_data(packets=packets, destination=destination, env=env))
            yield self.send_data_reactivate[destination]

    def sendAck(self, packet, env):
        env.process(self.links[0].send_ack(AckPacket(packet.id, self.ip, packet.source), packet.source, env))

    def receive_data(self, packet, env):
        print('Received data packet: ', packet.id, ' at ', env.now)
        self.sendAck(packet, env)

    def receive_ack(self, packet, env):
        print('Received ack packet: ', packet.id, ' at ', env.now)
        destination = packet.source
        self.unacknowledged_packets[destination] -= 1
        if self.unacknowledged_packets[destination] < self.window_size[destination]:
            self.send_data_reactivate[destination].succeed()
            self.send_data_reactivate[destination] = env.event()
