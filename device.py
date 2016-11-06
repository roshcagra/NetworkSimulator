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
        return packets

    def sendData(self, data, destination, env):
        currData = data
        while currData > 0:
            packets = self.generate_packets(destination)
            self.unacknowledged_packets += self.window_size
            currData -= self.window_size * DataPacket.size
            env.process(self.links[0].send_data(packets, destination))
            yield self.send_data_reactivate

    def sendAck(self, packet, env):
        env.process(self.links[0].send_ack(AckPacket(packet.id, self, packet.source), packet.source))

    def receive(self, packet, env):
        print('Received packet: ', packet)
        if isinstance(packet, AckPacket):
            self.unacknowledged_packets -= 1
            if self.unacknowledged_packets < self.window_size:
                self.send_data_reactivate.succeed()
                self.send_data_reactivate = env.event()
        elif isinstance(packet, DataPacket):
            self.sendAck(packet, env)
