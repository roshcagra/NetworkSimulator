from packet import DataPacket
from packet import AckPacket

class Device:
    def __init__(self, ip):
        self.ip = ip
        self.links = []

    def add_link(self, link):
        self.links.append = link

class Host(Device):
    def __init__(self, ip, W, env):
        Device.__init__(self, ip)
        self.window_size = W
        self.unacknowledged_packets = 0
        self.env = env
        self.send_data_reactivate = env.event()
        self.next_packet_id = 0

    def update_packet_id(self):
        self.next_packet_id += 1

    def generate_packets(self, destination):
        packets = []
        for _ in range(0, self.window_size):
            packets.append(DataPacket(self.next_packet_id, self, destination))
            self.update_packet_id()
        return packets

    def sendData(self, data, destination):
        currData = data
        while currData > 0:
            packets = self.generate_packets(destination)
            self.links[0].send(packets, destination)
            self.unacknowledged_packets += self.window_size
            currData -= self.window_size * DataPacket.size
            yield self.send_data_reactivate

    def sendAck(self, packet):
        self.links[0].send(AckPacket(packet.id, self, packet.source), packet.source)

    def receive(self, packet):
        if isinstance(packet, AckPacket):
            self.unacknowledged_packets -= 1
            if self.unacknowledged_packets < self.window_size:
                self.send_data_reactivate.succeed()
                self.send_data_reactivate = self.env.event()
        elif isinstance(packet, DataPacket):
            self.sendAck(packet)
