import math
from packet import DataPacket
from packet import AckPacket

class Device:
    def __init__(self, ip):
        self.ip = ip
        self.links = []

    def add_link(self, link):
        self.links.append(link)


class Router(Device):
    def __init__(self, ip, routing_table):
        Device.__init__(self, ip)
        self.routing_table = routing_table # Maps destination ip -> link object

    def receive_data(self, packet, env):
        self.route(packet, env)

    def receive_ack(self, packet, env):
        self.receive_data(packet, env)

    def route(self, packet, env):
        # print('Routing sending data packet: ', packet.id, 'at', env.now)
        env.process(self.routing_table[packet.destination].send_packet(packet=packet,source=self.ip, env=env))



class Host(Device):
    def __init__(self, ip):
        Device.__init__(self, ip)
        self.flow_reactivate = {}
        self.unacknowledged_packets = {}
        self.window_size = {}
        self.timeout = {}
        self.slow_start = {}

    def send_data(self, packet, destination, env):
        env.process(self.links[0].send_packet(packet=packet, source=self.ip, env=env))

    def start_flow(self, data, destination, env):
        self.window_size[destination] = 1
        self.unacknowledged_packets[destination] = 0
        self.flow_reactivate[destination] = env.event()
        self.timeout[destination] = None
        self.slow_start[destination] = (True, float("inf"))
        next_packet_id = 0

        curr_data = data
        while curr_data > 0:
            floored_window = math.floor(self.window_size[destination])
            floored_window = int(floored_window) # todo remove before push
            curr_size = floored_window - self.unacknowledged_packets[destination]
            self.unacknowledged_packets[destination] = floored_window
            curr_data -= curr_size * DataPacket.size
            for _ in range(0, curr_size):
                new_packet = DataPacket(p_id=next_packet_id, source=self.ip, destination=destination, time=env.now)
                self.send_data(new_packet, destination, env)
                next_packet_id += 1
            yield self.flow_reactivate[destination]

    def send_ack(self, packet, env):
        env.process(self.links[0].send_packet(AckPacket(packet.id, self.ip, packet.source, packet), self.ip, env))

    def receive_data(self, packet, env):
        print('Received data packet: ', packet.id, ' at ', env.now)
        self.send_ack(packet, env)

    def handle_timeout(self, data_packet, arrival_time, destination):
        travel_time = arrival_time - data_packet.time
        if self.timeout[destination] is None:
            self.timeout[destination] = (travel_time, travel_time)
            return False
        arrival_n = self.timeout[destination][0]
        deviation_n = self.timeout[destination][1]
        b = 0.5

        arrival_n1 = (1 - b) * arrival_n + b * travel_time
        deviation_n1 = (1 - b) * deviation_n + b * abs(travel_time - arrival_n1)
        self.timeout[destination] = (arrival_n1, deviation_n1)

        curr_timeout = arrival_n + 4 * deviation_n
        return travel_time > curr_timeout

    def receive_ack(self, packet, env):
        print('Received ack packet: ', packet.id, ' at ', env.now)
        data_packet = packet.data
        destination = data_packet.destination
        if self.slow_start[destination][0]:
            if self.handle_timeout(data_packet, env.now, destination):
                print('Timeout during Slow Start, resetting')
                self.slow_start[destination] = (True, self.window_size[destination] / 2)
                self.window_size[destination] = 1
            elif self.window_size[destination] > self.slow_start[destination][1]:
                print('Entering Congestion Control')
                self.slow_start[destination] = (False, float("inf"))
                self.window_size[destination] += 1 / 8 + 1 / self.window_size[destination]
            else:
                self.window_size[destination] += 1
        else:
            if self.handle_timeout(data_packet, env.now, destination):
                print('Timeout during Congestion Control, beginning Slow Start')
                self.slow_start[destination] = (True, self.window_size[destination] / 2)
                self.window_size[destination] = 1
            else:
                self.window_size[destination] += 1 / 8 + 1 / self.window_size[destination]
        self.unacknowledged_packets[destination] -= 1
        if self.unacknowledged_packets[destination] < self.window_size[destination]:
            self.flow_reactivate[destination].succeed()
            self.flow_reactivate[destination] = env.event()
