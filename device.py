import math
import simpy
from packet import DataPacket
from packet import AckPacket
from packet import RouterPacket

from graphing import Graph

aws = float('inf')

class Device:
    def __init__(self, ip):
        self.ip = ip
        self.links = []

    def add_link(self, link):
        self.links.append(link)


class Router(Device):
    def __init__(self, ip, routing_table=None):
        Device.__init__(self, ip)
        self.distance_table = {ip : 0} # destination ip -> distance/cost/time. Would be more accurate to call 'time_table' since the weight we are measuring here is time

        if routing_table != None: # routing table has been passed in
            self.routing_table = routing_table # destination ip -> link object (next hop)
        else:
            self.routing_table = {}

    # determines type of packet and calls correct recieving function
    def receive_packet(self, packet, env):
        if isinstance(packet, DataPacket) or isinstance(packet, AckPacket):
            self.route(packet, env)
        elif isinstance(packet, RouterPacket):
            self.recieve_router(packet, env)

    # Routes data and ack packets
    def route(self, packet, env):
        # print('Routing sending data packet: ', packet.id, 'at', env.now)
        if packet.destination not in self.routing_table:
            print('packet dropped by router', self.ip)
            return

        next_hop = self.routing_table[packet.destination]

        env.process(next_hop.send_packet(packet=packet, source=self.ip, env=env))

    def recieve_router(self, packet, env):
        edge_weight = packet.buffer_occ

        # print(self.ip, self.distance_table)

        for key in packet.distance_table:
            # print('me', self.ip)
            # print('d tbl', self.distance_table)
            # print('r tbl', self.routing_table)
            # print(key)
            # print('---------')

            if key not in self.distance_table: # a router we have never seen before
                self.distance_table[key] = packet.distance_table[key] + edge_weight
                self.routing_table[key] = packet.link
            elif packet.distance_table[key] + edge_weight < self.distance_table[key]: # this route offers a shorter path to 'key'
                self.distance_table[key] = packet.distance_table[key] + edge_weight
                self.routing_table[key] = packet.link
            elif packet.source == key: # 'key' is the origin of the packet
                if packet.link == self.routing_table[key]: # shortest path is directly from self.ip to key
                    if edge_weight != self.distance_table[key]: # edge weight has increased!!!
                        # self.distance_table[key] = packet.distance_table[key] + edge_weight
                        for k in self.routing_table:
                            if packet.link == self.routing_table[k]:
                                # all of the recorded path lenghts for paths through
                                # packet.link are now innacurate, since the edge_weight has changed
                                # set distance to inf, and next cycle the path will be recalculated
                                self.distance_table[k] = float('inf')

                        print('edge weight increase detected')




        # print(self.ip, 'routing table:')
        # print(self.routing_table)
        # print('------------------------------')

    def send_router(self, env):
        # p_id = (env.now + 1) * 100 + self.ip # unique ID, assumes ip is less than 100
        p_id = -1
        for link in self.links:
            # Todo, buffer_occ=(link.buffer.capacity - link.buffer.level) could be changed to buffer_occ=(link.buffer.capacity - link.buffer.level)/link.buffer.capacity. (percent occupancy rather than the raw number of bits; if different links have different buffer capacities)
            router_packet = RouterPacket(p_id=p_id, source=self.ip, distance_table=self.distance_table, buffer_occ=(link.buffer.capacity - link.buffer.level))
            router_packet.specify_link(link)
            env.process(link.send_packet(packet=router_packet, source=self.ip, env=env))


class Host(Device):
    def __init__(self, ip):
        Device.__init__(self, ip)
        self.flow_reactivate = {}
        self.unacknowledged_packets = {}
        self.window_size = {}
        self.ss_thresh = {}
        self.send_times = {}
        self.timeout_clock = {}
        self.timer = {}
        self.last_acknowledged = {}
        self.eof = {}
        self.graph_wsize = Graph("Window Size")

        self.received = {}

    def get_timeout(self, destination):
        if destination not in self.timeout_clock:
            return 100
        arrival_n = self.timeout_clock[destination][0]
        deviation_n = self.timeout_clock[destination][1]
        print('time', arrival_n + 4 * max(deviation_n, 1))
        return arrival_n + 4 * max(deviation_n, 1)

    def update_timeout_clock(self, send_time, arrival_time, destination):
        travel_time = arrival_time - send_time
        if destination not in self.timeout_clock:
            self.timeout_clock[destination] = (travel_time, travel_time / 2)
            return
        arrival_n = self.timeout_clock[destination][0]
        deviation_n = self.timeout_clock[destination][1]
        a = 1 / 8
        b = 1 / 4

        deviation_n1 = (1 - b) * deviation_n + b * abs(travel_time - arrival_n)
        arrival_n1 = (1 - a) * arrival_n + a * travel_time
        self.timeout_clock[destination] = (arrival_n1, deviation_n1)

    def retransmit(self, destination, env):
        p_id = self.last_acknowledged[destination][0]
        self.send_data(p_id, destination, True, env)

    def reset_timer(self, destination, try_number, env):
        try:
            yield env.timeout(self.get_timeout(destination) * try_number)
            print('Time', env.now, 'Timeout occurred. Sending last unacknowledged packet and reseting timer.')
            self.ss_thresh[destination] = self.window_size[destination] / 2
            self.window_size[destination] = 1
            self.retransmit(destination, env)
            self.timer[destination] = env.process(self.reset_timer(destination, try_number + 1, env))
        except simpy.Interrupt as message:
            if message.cause == 'reset':
                self.timer[destination] = env.process(self.reset_timer(destination, 1, env))
            elif message.cause == 'end':
                pass

    def send_data(self, p_id, destination, is_retransmit, env):
        if not is_retransmit:
            self.send_times[destination][p_id] = env.now
        else:
            self.send_times[destination].pop(p_id, None)
        packet = DataPacket(p_id=p_id, source=self.ip, destination=destination)
        env.process(self.links[0].send_packet(packet=packet, source=self.ip, env=env))

    def start_flow(self, data, destination, env):
        self.window_size[destination] = 1
        self.unacknowledged_packets[destination] = 0
        self.flow_reactivate[destination] = env.event()
        self.ss_thresh[destination] = float('inf')
        self.last_acknowledged[destination] = (0, 0)
        self.send_times[destination] = {}
        self.eof[destination] = math.ceil(data / DataPacket.size)
        self.timer[destination] = env.process(self.reset_timer(destination, 1, env))
        next_packet_id = 0

        curr_data = data
        while curr_data > 0:
            floored_window = math.floor(self.window_size[destination])
            curr_packets = math.ceil(curr_data / DataPacket.size)
            curr_size = int(min(floored_window - self.unacknowledged_packets[destination], curr_packets))
            self.unacknowledged_packets[destination] = self.unacknowledged_packets[destination] + curr_size
            curr_data -= curr_size * DataPacket.size
            for p_id in range(next_packet_id, next_packet_id + curr_size):
                self.send_data(p_id, destination, False, env)
            next_packet_id += curr_size
            yield self.flow_reactivate[destination]

    def end_flow(self, destination, env):
        self.timer[destination].interrupt('end')

    def send_ack(self, packet_id, source, env):
        env.process(self.links[0].send_packet(AckPacket(packet_id, self.ip, source), self.ip, env))

    def get_next_ack(self, packet_source):
        received = self.received[packet_source]
        expected = 0
        for i in received:
            if i != expected:
                return expected
            expected += 1
        return expected

    def receive_data(self, packet, env):
        packet_id = packet.id
        packet_source = packet.source
        print('Received data packet: ', packet_id, ' at ', env.now)

        if packet_source not in self.received:
            self.received[packet_source] = [packet_id]
        elif packet_id in self.received[packet_source]:
            return
        else:
            self.received[packet_source].append(packet_id)
            self.received[packet_source].sort()

        self.send_ack(self.get_next_ack(packet_source), packet_source, env)

    def receive_ack(self, packet, env):
        packet_id = packet.id
        destination = packet.source
        print('Received ack packet: ', packet_id, ' at ', env.now)
        if packet_id == self.eof[destination]:
            self.end_flow(destination, env)
            return

        if (self.last_acknowledged[destination][0] == packet_id - 1) and (packet_id - 1) in self.send_times[destination]:
            self.update_timeout_clock(self.send_times[destination][packet_id - 1], env.now, destination)

        self.timer[destination].interrupt('reset')
        if self.last_acknowledged[destination][0] < packet_id:
            if self.last_acknowledged[destination][1] >= 4:
                print('resetting', self.window_size[destination], self.ss_thresh[destination])
                self.window_size[destination] = self.ss_thresh[destination]
            self.unacknowledged_packets[destination] -= packet_id - self.last_acknowledged[destination][0]
            self.last_acknowledged[destination] = (packet_id, 1)
            if self.window_size[destination] < self.ss_thresh[destination]:
                self.window_size[destination] += 1
            else:
                self.window_size[destination] += (1 / self.window_size[destination])
        elif self.last_acknowledged[destination][0] == packet_id:
            self.last_acknowledged[destination] = (packet_id, self.last_acknowledged[destination][1] + 1)

        if self.last_acknowledged[destination][1] == 4:
            self.ss_thresh[destination] = self.window_size[destination] / 2
            self.window_size[destination] = self.window_size[destination] / 2 + 3
            print('Duplicate acks received. Fast Retransmitting.')
            self.retransmit(destination, env)
        elif self.last_acknowledged[destination][1] > 4:
            self.window_size[destination] += 1

        self.graph_wsize.add_point(env.now, self.window_size[destination])

        print(self.unacknowledged_packets[destination], self.window_size[destination])

        if self.unacknowledged_packets[destination] < math.floor(self.window_size[destination]):
            self.flow_reactivate[destination].succeed()
            self.flow_reactivate[destination] = env.event()

    def receive_packet(self, packet, env):
        if isinstance(packet, DataPacket):
            self.receive_data(packet, env)
        elif isinstance(packet, AckPacket):
            self.receive_ack(packet, env)
        elif isinstance(packet, RouterPacket):
            pass
