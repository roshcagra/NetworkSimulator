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

    def receive_data(self, packet, env):
        self.route(packet, env)

    def receive_ack(self, packet, env):
        self.receive_data(packet, env)

    def route(self, packet, env):
        # print('Routing sending data packet: ', packet.id, 'at', env.now)
        env.process(self.routing_table[packet.destination].send_packet(packet=packet, source=self.ip, env=env))
        # self.routing_table[packet.destination].send_packet(packet=packet,source=self.ip, env=env)

    def recieve_router(self, packet, env):
        edge_weight = env.now - packet.time_sent

        for key in packet.distance_table:
            if key not in self.distance_table: # a router we have never seen before
                self.distance_table[key] = packet.distance_table[key] + edge_weight
                self.routing_table[key] = packet.link
            elif packet.distance_table[key] + edge_weight < self.distance_table[key]: # this route offers a shorter path to 'key'
                self.distance_table[key] = packet.distance_table[key] + edge_weight
                self.routing_table[key] = packet.link
            elif packet.distance_table[key] == 0: # 'key' is the origin of the packet
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
        p_id = (env.now + 1) * 100 + self.ip # unique ID, assumes ip is less than 100
        for link in self.links:
            router_packet = RouterPacket(p_id=p_id, source=self.ip, distance_table=self.distance_table, time_sent=env.now)
            router_packet.specify_link(link)
            env.process(link.send_packet(packet=router_packet, source=self.ip, env=env))


class Host(Device):
    def __init__(self, ip):
        Device.__init__(self, ip)
        self.flow_reactivate = {}
        self.unacknowledged_packets = {}
        self.window_size = {}
        self.slow_start = {}
        self.graph_wsize = Graph("Window Size")
        self.timer = {}
        self.retransmit_queue = {}

        self.received = {}

    def get_timeout(self, destination):
        if destination not in self.timer:
            return float("inf")
        arrival_n = self.timer[destination][0]
        deviation_n = self.timer[destination][1]
        return arrival_n + 4 * deviation_n

    def update_timer(self, send_time, arrival_time, destination):
        travel_time = arrival_time - send_time
        if destination not in self.timer:
            self.timer[destination] = (travel_time, travel_time)
            return
        arrival_n = self.timer[destination][0]
        deviation_n = self.timer[destination][1]
        b = 0.5

        arrival_n1 = (1 - b) * arrival_n + b * travel_time
        deviation_n1 = (1 - b) * deviation_n + b * abs(travel_time - arrival_n1)
        self.timer[destination] = (arrival_n1, deviation_n1)

    def timeout(self, packet_id, destination, is_retransmit, env):
        send_time = env.now
        try:
            yield env.timeout(self.get_timeout(destination))
            print('Timer timed out for packet ', packet_id, 'Resending packet and restarting timer.')
            self.slow_start[destination] = (True, self.window_size[destination] / 2)
            self.window_size[destination] = 1
            self.send_data(packet_id, destination, True, env)
        except simpy.Interrupt:
            if not is_retransmit:
                self.update_timer(send_time, env.now, destination)

    def send_data(self, p_id, destination, is_retransmit, env):
        self.retransmit_queue[destination][p_id] = env.process(self.timeout(p_id, destination, is_retransmit, env))
        packet = DataPacket(p_id=p_id, source=self.ip, destination=destination)
        env.process(self.links[0].send_packet(packet=packet, source=self.ip, env=env))

    def start_flow(self, data, destination, env):
        self.window_size[destination] = 1
        self.unacknowledged_packets[destination] = 0
        self.flow_reactivate[destination] = env.event()
        self.slow_start[destination] = (True, aws)
        self.retransmit_queue[destination] = {}
        next_packet_id = 0

        curr_data = data
        while curr_data > 0:
            floored_window = math.floor(self.window_size[destination])
            floored_window = int(floored_window) # todo remove before push
            curr_size = floored_window - self.unacknowledged_packets[destination]
            self.unacknowledged_packets[destination] = floored_window
            curr_data -= curr_size * DataPacket.size
            for _ in range(0, curr_size):
                self.send_data(next_packet_id, destination, False, env)
                next_packet_id += 1
            yield self.flow_reactivate[destination]

    def send_ack(self, packet_id, source, env):
        env.process(self.links[0].send_packet(AckPacket(packet_id, self.ip, source), self.ip, env))

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

        self.send_ack(packet_id, packet_source, env)

    def receive_ack(self, packet, env):
        packet_id = packet.id
        destination = packet.source
        self.retransmit_queue[destination][packet_id].interrupt()
        print('Received ack packet: ', packet_id, ' at ', env.now)
        if self.slow_start[destination][0]:
            self.window_size[destination] += 1
            if self.window_size[destination] > self.slow_start[destination][1]:
                print('Entering Congestion Control')
                self.slow_start[destination] = (False, aws)
        else:
            self.window_size[destination] += 1 / 8 + 1 / self.window_size[destination]
        self.graph_wsize.add_point(env.now, self.window_size[destination])

        self.unacknowledged_packets[destination] -= 1
        if self.unacknowledged_packets[destination] < self.window_size[destination]:
            self.flow_reactivate[destination].succeed()
            self.flow_reactivate[destination] = env.event()
