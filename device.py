import math
from packet import DataPacket
from packet import AckPacket

aws = 10

class Device:
    def __init__(self, ip):
        self.ip = ip
        self.links = []

    def add_link(self, link):
        self.links.append(link)


class Router(Device):
    def __init__(self, ip, routing_table):
        Device.__init__(self, ip)
        self.routing_table = routing_table

class Host(Device):
    def __init__(self, ip):
        Device.__init__(self, ip)
        self.flow_reactivate = {}
        self.unacknowledged_packets = {}
        self.window_size = {}
        self.slow_start = {}
        self.last_acknowledged = {}

        self.received = {}

    def send_data(self, packet, destination, env):
        env.process(self.links[0].send_packet(packet=packet, destination=destination, env=env))

    def start_flow(self, data, destination, env):
        self.window_size[destination] = 1
        self.unacknowledged_packets[destination] = 0
        self.flow_reactivate[destination] = env.event()
        self.slow_start[destination] = (True, aws)
        self.last_acknowledged[destination] = (-1, 0)
        next_packet_id = 0

        curr_data = data
        while curr_data > 0:
            floored_window = math.floor(self.window_size[destination])
            curr_size = floored_window - self.unacknowledged_packets[destination]
            self.unacknowledged_packets[destination] = floored_window
            curr_data -= curr_size * DataPacket.size
            for _ in range(0, curr_size):
                new_packet = DataPacket(p_id=next_packet_id, source=self.ip, destination=destination)
                self.send_data(new_packet, destination, env)
                next_packet_id += 1
            yield self.flow_reactivate[destination]

    def send_ack(self, packet, env):
        env.process(self.links[0].send_packet(AckPacket(packet.id, self.ip, packet.source), packet.source, env))

    def receive_data(self, packet, env):
        packet_id = packet.id
        packet_source = packet.source
        print('Received data packet: ', packet_id, ' at ', env.now)
        if packet_source not in self.received:
            self.received[packet_source] = [packet_id]
        else:
            if packet_id not in self.received[packet_source]:
                self.received[packet_source].append(packet_id)
                self.received[packet_source].sort()
                self.send_ack(packet, env)

    def receive_ack(self, packet, env):
        packed_id = packet.id
        print('Received ack packet: ', packed_id, ' at ', env.now)
        destination = packet.source
        last_recieved = self.last_acknowledged[destination][0]
        last_received_count = self.last_acknowledged[destination][1]
        if last_recieved >= packed_id:
            if last_received_count == 3:
                print('Packet Loss Detected. Retransmitting and starting Slow Start Procedure')
                missing_packet = DataPacket(p_id=packed_id, source=self.ip, destination=destination)
                env.process(self.send_data(missing_packet, destination, env))
                self.slow_start[destination] = (True, aws)
                self.window_size[destination] = 1
            self.last_acknowledged[destination] = (last_recieved, last_received_count + 1)
        else:
            self.last_acknowledged[destination] = (packed_id, 1)
            if self.slow_start[destination][0]:
                self.window_size[destination] += 1
                if self.window_size[destination] > self.slow_start[destination][1]:
                    print('Entering Congestion Control')
                    self.slow_start[destination] = (False, aws)
            else:
                self.window_size[destination] += 1 / 8 + 1 / self.window_size[destination]
            self.unacknowledged_packets[destination] -= 1
            if self.unacknowledged_packets[destination] < self.window_size[destination]:
                self.flow_reactivate[destination].succeed()
                self.flow_reactivate[destination] = env.event()
