import math
import simpy
from packet import DataPacket
from packet import AckPacket
from packet import RouterPacket

from graphing import Graph

debug_state = False

aws = float('inf')

update_interval = 100

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
        self.type = "router"

        if routing_table != None: # routing table has been passed in
            self.routing_table = routing_table # destination ip -> link object (next hop)
        else:
            self.routing_table = {}
    def add_link(self, link):
        super(Router, self).add_link(link)
        other = link.getOtherDevice(self.ip)
        if(isinstance(other, Host)):
            self.distance_table[other.ip] = 0
            self.routing_table[other.ip] = link

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

        change_detected = False
        for key in packet.distance_table:

            if key == self.ip:
                continue
            if key not in self.distance_table: # a router we have never seen before
                self.distance_table[key] = packet.distance_table[key] + edge_weight
                self.routing_table[key] = packet.link
                change_detected = True
            elif self.routing_table[key] == packet.link:
                self.distance_table[key] = packet.distance_table[key] + edge_weight
            elif packet.distance_table[key] + edge_weight < self.distance_table[key]: # this route offers a shorter path to 'key'
                self.distance_table[key] = packet.distance_table[key] + edge_weight
                self.routing_table[key] = packet.link
                change_detected = True

        if change_detected:
            self.send_router(env)

    def send_router(self, env):
        # p_id = (env.now + 1) * 100 + self.ip # unique ID, assumes ip is less than 100
        p_id = -1
        for link in self.links:
            # Todo, buffer_occ=(link.buffer.capacity - link.buffer.level) could be changed to buffer_occ=(link.buffer.capacity - link.buffer.level)/link.buffer.capacity.
            # (percent occupancy rather than the raw number of bits; if different links have different buffer capacities)
            router_packet = RouterPacket(p_id=p_id, source=self.ip, distance_table=self.distance_table, buffer_occ=(link.buffer.capacity - link.buffer.level + RouterPacket.size - link.router_occ_size))
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

        self.graph_wsize = {}
        self.graph_flowrate = {}
        self.last_flow_check = {}
        self.flow_count = {}

        self.received = {}

    def get_curr_window_length(self, destination):
        return self.window[destination][1] - self.window[destination][0]

    def send_data(self, p_id, destination, is_retransmit, env):
        if not is_retransmit:
            self.send_times[destination][p_id] = env.now
        else:
            self.send_times[destination].pop(p_id, None)
        if debug_state:
            print('Sending DataPacket', p_id, 'at', env.now)
        packet = DataPacket(p_id=p_id, source=self.ip, destination=destination)
        env.process(self.links[0].send_packet(packet=packet, source=self.ip, env=env))

    def start_flow(self, data, destination, env, tcp_type='Reno', gamma=0.5, alpha=15):
        self.graph_wsize[destination] = Graph("Device" + str(self.ip) + " to Device " + str(destination))

        if tcp_type == 'Reno':
            self.tcp_type[destination] = 'Reno'
            env.process(self.start_reno_flow(data, destination, env))
        elif tcp_type == 'FAST':
            self.tcp_type[destination] = 'FAST'
            env.process(self.start_fast_flow(data, destination, gamma, alpha, env))

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

    def start_fast_flow(self, data, destination, gamma, alpha, env):
        self.window[destination] = (0, 0)
        self.window_size[destination] = 1
        self.flow_reactivate[destination] = env.event()
        self.last_acknowledged[destination] = (0, 0)
        self.send_times[destination] = {}
        self.eof[destination] = math.ceil(data / DataPacket.size) + 1
        self.fast_RTT[destination] = (float('inf'), float('inf'))
        self.timer[destination] = env.process(self.update_window(destination, gamma, alpha, env))

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
            return 1000
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
            self.graph_wsize[destination].add_point(env.now, self.window_size[destination])
            self.retransmit(destination, env)
            self.window_size[destination] = 1
            self.window[destination] = (self.window[destination][0], self.window[destination][0] + 1)
            self.timer[destination] = env.process(self.reset_timer(destination, try_number + 1, env))
            self.graph_wsize[destination].add_point(env.now, self.window_size[destination])
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

        self.graph_wsize[destination].add_point(env.now, self.window_size[destination])

        if (self.last_acknowledged[destination][0] == packet_id - 1) and (packet_id - 1) in self.send_times[destination]:
            self.update_timeout_clock(self.send_times[destination][packet_id - 1], env.now, destination)

        if self.last_acknowledged[destination][0] < packet_id:
            self.timer[destination].interrupt('reset')
            self.window[destination] = (packet_id, max(self.window[destination][1], packet_id))
            if self.last_acknowledged[destination][1] >= 4:
                if debug_state:
                    print('Stopping Fast Recovery', self.window_size[destination], self.ss_thresh[destination])
                self.window_size[destination] = self.ss_thresh[destination]
                self.window_size[destination] += (1 / math.floor(self.window_size[destination]))
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

        self.graph_wsize[destination].add_point(env.now, self.window_size[destination])

        if debug_state:
            print('Window Size:', self.window_size[destination])

        if self.get_curr_window_length(destination) < math.floor(self.window_size[destination]):
            self.flow_reactivate[destination].succeed()
            self.flow_reactivate[destination] = env.event()

    def update_window(self, destination, gamma, alpha, env):
        try:
            while True:
                if self.fast_RTT[destination][0] < float('inf'):
                    yield env.timeout(self.fast_RTT[destination][0] + 1)
                else:
                    yield env.timeout(30)
                if self.last_acknowledged[destination][0] > 0:
                    self.graph_wsize[destination].add_point(env.now, self.window_size[destination])
                    (base_rtt, last_rtt) = self.fast_RTT[destination]
                    curr_wsize = self.window_size[destination]
                    self.window_size[destination] = min(2 * curr_wsize, (1 - gamma) * curr_wsize + gamma * ((base_rtt / last_rtt) * curr_wsize + alpha))
                    self.graph_wsize[destination].add_point(env.now, self.window_size[destination])
                if self.get_curr_window_length(destination) < math.floor(self.window_size[destination]):
                    self.flow_reactivate[destination].succeed()
                    self.flow_reactivate[destination] = env.event()
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

        if (self.last_acknowledged[destination][0] == packet_id - 1) and (packet_id - 1) in self.send_times[destination]:
            self.update_rtt(self.send_times[destination][packet_id - 1], env.now, destination)

        if self.last_acknowledged[destination][0] < packet_id:
            self.window[destination] = (packet_id, max(self.window[destination][1], packet_id))
            self.last_acknowledged[destination] = (packet_id, 1)

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
        if debug_state:
            print('Sending AckPacket', packet_id, 'at', env.now)
        env.process(self.links[0].send_packet(AckPacket(packet_id, self.ip, source), self.ip, env))

    def get_next_ack(self, packet_source):
        received = self.received[packet_source]
        expected = 0
        for i in received:
            if i != expected:
                return expected
            expected += 1
        return expected

    def update_flowrate(self, source, time):
        if self.last_flow_check[source] + update_interval < time:
            curr_count = self.flow_count[source]
            self.graph_flowrate[source].add_point(time, curr_count * 1024 * (8 * 10 ** (-6)) / ((time - self.last_flow_check[source]) / 1000))
            self.flow_count[source] = 0
            self.last_flow_check[source] = time

    def receive_data(self, packet, env):
        packet_id = packet.id
        packet_source = packet.source

        if packet_source not in self.graph_flowrate:
            self.graph_flowrate[packet_source] = Graph("Device " + str(packet_source) + " to Device " + str(self.ip))
            self.last_flow_check[packet_source] = env.now

        if packet_source not in self.received:
            self.received[packet_source] = [packet_id]
            self.flow_count[packet_source] = 1
        elif packet_id in self.received[packet_source]:
            return
        else:
            self.received[packet_source].append(packet_id)
            self.received[packet_source].sort()
            self.flow_count[packet_source] += 1

        self.update_flowrate(packet_source, env.now)

        self.send_ack(self.get_next_ack(packet_source), packet_source, env)

    def receive_packet(self, packet, env):
        if debug_state and not isinstance(packet, RouterPacket):
            print('Time', env.now, 'Host received', packet.__class__.__name__, packet.id, 'from Device', packet.source)


        if isinstance(packet, DataPacket):
            self.receive_data(packet, env)
        elif isinstance(packet, AckPacket):
            self.receive_ack(packet, env)
        elif isinstance(packet, RouterPacket):
            pass
