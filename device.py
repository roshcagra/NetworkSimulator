import math
import simpy
from packet import DataPacket
from packet import AckPacket
from packet import RouterPacket

from graphing import Graph

debug_state = True

aws = float('inf')

class Device:
    def __init__(self, ip):
        self.ip = ip
        self.links = []

        self.graph_flowrate = Graph("Flow Rate", "flowrate")
        self.graph_wsize = Graph("Window Size", "wsize")

    def add_link(self, link):
        self.links.append(link)


class Router(Device):
    def __init__(self, ip, routing_table=None):
        Device.__init__(self, ip)
        self.distance_table = {ip : 0} # destination ip -> distance/cost/time. Would be more accurate to call 'time_table' since the weight we are measuring here is time
        self.type = "router"

        if routing_table != None: # routing table has been passed in
            self.routing_table = routing_table # destination ip -> link object (next hop)
        else:
            self.routing_table = {}

    # determines type of packet and calls correct receiveving function
    def receive_packet(self, packet, env):
        if isinstance(packet, DataPacket) or isinstance(packet, AckPacket):
            self.route(packet, env)
        elif isinstance(packet, RouterPacket):
            self.receive_router(packet, env)

    # Routes data and ack packets
    def route(self, packet, env):
        # print('Routing sending data packet: ', packet.id, 'at', env.now)
        if packet.destination not in self.routing_table:
            if debug_state:
                print('packet dropped by router', self.ip)
            return

        next_hop = self.routing_table[packet.destination]

        env.process(next_hop.send_packet(packet=packet, source=self.ip, env=env))

    def receive_router(self, packet, env):
        edge_weight = packet.buffer_occ

        # print('Router', self.ip, 'received routing packet', packet.distance_table)
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
                        if debug_state:
                            print('edge weight increase detected')




        # print(self.ip, 'routing table:')
        # print(self.routing_table)
        # print('------------------------------')

    def send_router(self, env):
        # p_id = (env.now + 1) * 100 + self.ip # unique ID, assumes ip is less than 100
        p_id = -1
        for link in self.links:
            # Todo, buffer_occ=(link.buffer.capacity - link.buffer.level) could be changed to buffer_occ=(link.buffer.capacity - link.buffer.level)/link.buffer.capacity.
            # (percent occupancy rather than the raw number of bits; if different links have different buffer capacities)
            router_packet = RouterPacket(p_id=p_id, source=self.ip, distance_table=self.distance_table, buffer_occ=(link.buffer.capacity - link.buffer.level))
            router_packet.specify_link(link)
            env.process(link.send_packet(packet=router_packet, source=self.ip, env=env))


class Host(Device):
    def __init__(self, ip):
        Device.__init__(self, ip)
        self.flow_reactivate = {}
        self.window = {}
        self.window_size = {}
        self.send_times = {}
        self.last_acknowledged = {}
        self.eof = {}
        self.tcp_type = {}
        self.timer = {}

        # TCP Reno
        self.ss_thresh = {}
        self.timeout_clock = {}
        # FAST TCP
        self.fast_RTT = {}

        self.received = {}
        self.num_received = 0
        self.num_sent = 0
        self.type = "host"

    def get_curr_window_length(self, destination):
        return self.window[destination][1] - self.window[destination][0]

    def send_data(self, p_id, destination, is_retransmit, env):
        if not is_retransmit:
            self.send_times[destination][p_id] = env.now
        else:
            self.num_sent += 1
            self.send_times[destination].pop(p_id, None)
        if debug_state:
            print('Sending DataPacket', p_id, 'at', env.now)
        packet = DataPacket(p_id=p_id, source=self.ip, destination=destination)
        env.process(self.links[0].send_packet(packet=packet, source=self.ip, env=env))

    def start_flow(self, data, destination, env, tcp_type='Reno'):
        if tcp_type == 'Reno':
            self.tcp_type[destination] = 'Reno'
            env.process(self.start_reno_flow(data, destination, env))
        elif tcp_type == 'FAST':
            self.tcp_type[destination] = 'FAST'
            env.process(self.start_fast_flow(data, destination, env))

    def start_reno_flow(self, data, destination, env):
        self.window[destination] = (0, 0)
        self.window_size[destination] = 1
        self.flow_reactivate[destination] = env.event()
        self.ss_thresh[destination] = float('inf')
        self.last_acknowledged[destination] = (0, 0)
        self.send_times[destination] = {}
        self.eof[destination] = math.ceil(data / DataPacket.size) + 1
        self.timer[destination] = env.process(self.reset_timer(destination, 1, env))

        while not self.window[destination][1] >= self.eof[destination]:
            max_batch_size = int(math.floor(self.window_size[destination]) - self.get_curr_window_length(destination))
            window_end_id = min(self.window[destination][1] + max_batch_size, self.eof[destination])
            for p_id in range(self.window[destination][1], window_end_id):
                self.send_data(p_id, destination, False, env)
            self.window[destination] = (self.window[destination][0], window_end_id)
            yield self.flow_reactivate[destination]

    def start_fast_flow(self, data, destination, env):
        self.window[destination] = (0, 0)
        self.window_size[destination] = 1
        self.flow_reactivate[destination] = env.event()
        self.last_acknowledged[destination] = (0, 0)
        self.send_times[destination] = {}
        self.eof[destination] = math.ceil(data / DataPacket.size) + 1
        self.fast_RTT[destination] = (float('inf'), float('inf'))
        self.timer[destination] = env.process(self.update_window(destination, env))

        while not self.window[destination][1] >= self.eof[destination]:
            max_batch_size = int(math.floor(self.window_size[destination]) - self.get_curr_window_length(destination))
            window_end_id = min(self.window[destination][1] + max_batch_size, self.eof[destination])
            for p_id in range(self.window[destination][1], window_end_id):
                self.send_data(p_id, destination, False, env)
            self.window[destination] = (self.window[destination][0], window_end_id)
            yield self.flow_reactivate[destination]

    def end_flow(self, destination, env):
        if self.timer[destination].is_alive:
            self.timer[destination].interrupt('end')

    def retransmit(self, destination, env):
        p_id = self.last_acknowledged[destination][0]
        self.send_data(p_id, destination, True, env)

    def get_timeout(self, destination):
        if destination not in self.timeout_clock:
            return 100
        arrival_n = self.timeout_clock[destination][0]
        deviation_n = self.timeout_clock[destination][1]
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

    def reset_timer(self, destination, try_number, env):
        try:
            yield env.timeout(self.get_timeout(destination) * try_number)
            if debug_state:
                print('Time', env.now, 'Timeout occurred. Sending last unacknowledged packet and reseting timer.')
            self.ss_thresh[destination] = math.floor(self.window_size[destination] / 2)
            self.graph_wsize.add_point(env.now, self.window_size[destination])
            self.retransmit(destination, env)
            self.window_size[destination] = 1
            self.window[destination] = (self.window[destination][0], self.window[destination][0] + 1)
            self.timer[destination] = env.process(self.reset_timer(destination, try_number + 1, env))
            self.graph_wsize.add_point(env.now, self.window_size[destination])
        except simpy.Interrupt as message:
            if message.cause == 'reset':
                self.timer[destination] = env.process(self.reset_timer(destination, 1, env))
            elif message.cause == 'end':
                pass

    def receive_reno_ack(self, packet, env):
        packet_id = packet.id
        destination = packet.source
        if packet_id == self.eof[destination]:
            self.end_flow(destination, env)
            return

        self.graph_wsize.add_point(env.now, self.window_size[destination])

        if (self.last_acknowledged[destination][0] == packet_id - 1) and (packet_id - 1) in self.send_times[destination]:
            self.update_timeout_clock(self.send_times[destination][packet_id - 1], env.now, destination)

        if self.last_acknowledged[destination][0] < packet_id:
            self.timer[destination].interrupt('reset')
            self.window[destination] = (packet_id, max(self.window[destination][1], packet_id))
            if self.last_acknowledged[destination][1] >= 4:
                if debug_state:
                    print('Stopping Fast Recovery', self.window_size[destination], self.ss_thresh[destination])
                self.window_size[destination] = self.ss_thresh[destination]
                self.window_size[destination] += (1 / self.window_size[destination])
            self.last_acknowledged[destination] = (packet_id, 1)
            if self.window_size[destination] < self.ss_thresh[destination]:
                self.window_size[destination] += 1
            else:
                self.window_size[destination] += (1 / math.floor(self.window_size[destination]))
        elif self.last_acknowledged[destination][0] == packet_id:
            self.last_acknowledged[destination] = (packet_id, self.last_acknowledged[destination][1] + 1)
            if self.last_acknowledged[destination][1] < 4:
                if self.window_size[destination] < self.ss_thresh[destination]:
                    self.window_size[destination] += 1
                else:
                    self.window_size[destination] += (1 / math.floor(self.window_size[destination]))
            if self.last_acknowledged[destination][1] == 4:
                if debug_state:
                    print('Duplicate acks received. Fast Retransmitting.')
                self.ss_thresh[destination] = math.floor(self.window_size[destination] / 2)
                self.window_size[destination] = self.ss_thresh[destination] + 3
                self.retransmit(destination, env)
                self.timer[destination].interrupt('reset')
            elif self.last_acknowledged[destination][1] > 4:
                self.window_size[destination] += 1

        self.graph_wsize.add_point(env.now, self.window_size[destination])

        print('Window Size:', self.window_size[destination])

        if self.get_curr_window_length(destination) < math.floor(self.window_size[destination]):
            self.flow_reactivate[destination].succeed()
            self.flow_reactivate[destination] = env.event()

    def update_window(self, destination, env):
        try:
            while True:
                yield env.timeout(20)
                if self.last_acknowledged[destination][0] > 0:
                    (base_rtt, last_rtt) = self.fast_RTT[destination]
                    curr_wsize = self.window_size[destination]
                    g = 0.05
                    a = 10
                    self.window_size[destination] = min(2 * curr_wsize, (1 - g) * curr_wsize + g * ((base_rtt / last_rtt) * curr_wsize + a))
        except simpy.Interrupt:
            return

    def update_rtt(self, send_time, arrival_time, destination):
        new_RTT = arrival_time - send_time
        new_base_RTT = min(self.fast_RTT[destination][0], new_RTT)
        self.fast_RTT[destination] = (new_base_RTT, new_RTT)

    def receive_fast_ack(self, packet, env):
        packet_id = packet.id
        destination = packet.source
        if packet_id == self.eof[destination]:
            self.end_flow(destination, env)
            return

        self.graph_wsize.add_point(env.now, self.window_size[destination])

        if (self.last_acknowledged[destination][0] == packet_id - 1) and (packet_id - 1) in self.send_times[destination]:
            self.update_rtt(self.send_times[destination][packet_id - 1], env.now, destination)

        if self.last_acknowledged[destination][0] < packet_id:
            self.window[destination] = (packet_id, max(self.window[destination][1], packet_id))
            self.last_acknowledged[destination] = (packet_id, 1)
        elif self.last_acknowledged[destination][0] == packet_id:
            self.last_acknowledged[destination] = (packet_id, self.last_acknowledged[destination][1] + 1)
            if self.last_acknowledged[destination][1] == 4:
                if debug_state:
                    print('Duplicate acks received. Resetting.')
                self.window_size[destination] = 1
                self.window[destination] = (packet_id, packet_id + 1)
                self.retransmit(destination, env)

        self.graph_wsize.add_point(env.now, self.window_size[destination])

        if self.get_curr_window_length(destination) < math.floor(self.window_size[destination]):
            self.flow_reactivate[destination].succeed()
            self.flow_reactivate[destination] = env.event()

    def receive_ack(self, packet, env):
        destination = packet.source
        if self.tcp_type[destination] == 'Reno':
            self.receive_reno_ack(packet, env)
        elif self.tcp_type[destination] == 'FAST':
            self.receive_fast_ack(packet, env)

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

        if packet_source not in self.received:
            self.received[packet_source] = [packet_id]
        elif packet_id in self.received[packet_source]:
            return
        else:
            self.received[packet_source].append(packet_id)
            self.received[packet_source].sort()

        self.send_ack(self.get_next_ack(packet_source), packet_source, env)

    def receive_packet(self, packet, env):
        if debug_state and not isinstance(packet, RouterPacket):
            print('Time', env.now, 'Host received', packet.__class__.__name__, packet.id, 'from Device', packet.source)
        self.num_received += 1
        if self.num_sent > 0:
            self.graph_flowrate.add_point(env.now, self.num_received/self.num_sent)
        if isinstance(packet, DataPacket):
            self.receive_data(packet, env)
        elif isinstance(packet, AckPacket):
            self.receive_ack(packet, env)
        elif isinstance(packet, RouterPacket):
            pass
