from packet import DataPacket
from packet import AckPacket

class Device:
    def __init__(self, ip):
        self.ip = ip
        self.links = []

    def add_link(self, link):
        self.links.append(link)

class Host(Device):
    def __init__(self, ip, W, env):
        Device.__init__(self, ip)
        self.window_size = W
        self.unacknowledged_packets = 0
        self.send_data_reactivate = env.event()
        self.next_packet_id = 0

    def update_packet_id(self):
        self.next_packet_id += 1

    def generate_packets(self, destination):
        packets = []
        for _ in range(0, self.window_size):
            packets.append(DataPacket(self.next_packet_id, self.ip, destination))
            self.update_packet_id()
        return (self.window_size, packets)

    def sendData(self, data, destination, env):
        currData = data
        while currData > 0:
            packet_tuple = self.generate_packets(destination)
            self.unacknowledged_packets += self.window_size
            currData -= self.window_size * DataPacket.size
            env.process(self.links[0].send_data(packet_tuple=packet_tuple, destination=destination, env=env))
            yield self.send_data_reactivate

    def sendAck(self, packet, env):
        env.process(self.links[0].send_ack(AckPacket(packet.id, self, packet.source), packet.source, env))

    def receive_data(self, packet, env):
        print('Received data packet: ', packet.id, ' at ', env.now)
        self.sendAck(packet, env)

    def receive_ack(self, packet, env):
        print('Received ack packet: ', packet.id, ' at ', env.now)
        self.unacknowledged_packets -= 1
        if self.unacknowledged_packets < self.window_size:
            self.send_data_reactivate.succeed()
            self.send_data_reactivate = env.event()
