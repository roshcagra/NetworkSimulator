import simpy
from graphing import Graph
from packet import RouterPacket

debug_state = False

class Link:
    def __init__(self, link_rate, link_delay, max_buffer_size, env):
        self.env = env
        self.devices = {} # ip -> device object
        self.link_rate = link_rate # aka capacity/transmission delay
        self.link_delay = link_delay # propogation delay
        self.send = {}
        self.buffer = simpy.Container(env, init=max_buffer_size, capacity=max_buffer_size)
        self.router_occ_size = 0
        self.last_dest = (-1, 0)
        self.max_priority = 1
        self.graph_buffocc = Graph("Buffer Occupancy", "buffocc")
        self.graph_delay = Graph("Packet Delay", "delay")
        self.graph_linkrate = Graph("Link Rate", "linkrate")
        self.graph_dropped = Graph("Packet Loss", "dropped")
        self.current_dropped = 0 # number of packets dropped at this time
        self.last_dropped_time = 0
        self.sum_queued = 0     # number of packets that have ever been queued
        self.sum_queuetime = 0  # sum of all queue wait times
        self.sum_packets = 0 # sum of sizes of all sent packets

    def add_device(self, device):
        self.devices[device.ip] = device
        self.send[device.ip] = simpy.Resource(self.env, capacity=1)

    def getOtherDevice(self, my_ip):
        for ip in self.devices:
            if ip != my_ip:
                return self.devices[ip]

    def __repr__(self):
        return 'Link from' + str(list(self.devices.keys())[0]) + 'to' + str(list(self.devices.keys())[1])

    def __str__(self):
        return 'Link from' + str(list(self.devices.keys())[0]) + 'to' + str(list(self.devices.keys())[1])

    def insert_into_buffer(self, packet, packet_size, env):
        # Plot "prev"
        self.graph_buffocc.add_point(env.now, self.buffer.capacity - self.buffer.level)
        if packet_size <= self.buffer.level:
            self.buffer.get(packet_size)
            # Buffer++
            self.graph_buffocc.add_point(env.now, self.buffer.capacity - self.buffer.level)
            self.sum_packets += packet.size

            packet.t_enterbuff = env.now
            if isinstance(packet, RouterPacket):
                self.router_occ_size += RouterPacket.size
            return True
        else:
            return False

    def remove_from_buffer(self, packet, packet_size, env):
        self.buffer.put(packet_size)
        self.sum_queued += 1
        self.sum_queuetime += env.now - packet.t_enterqueue
        if isinstance(packet, RouterPacket):
            self.router_occ_size -= RouterPacket.size

    def send_packet(self, packet, source, env):
        destination = -1
        for ip in self.devices:
            if ip != source:
                destination = ip


        if self.insert_into_buffer(packet, packet.size, env):
            time_enter_queue = env.now
            # # Buffer++
            # self.graph_buffocc.add_point(env.now, self.buffer.capacity - self.buffer.level)
            # self.sum_packets += packet.size

            self.graph_dropped.add_point(env.now, self.current_dropped)
            self.current_dropped = 0
            self.graph_dropped.add_point(env.now, self.current_dropped)

            if env.now > 0:
                self.graph_linkrate.add_point(env.now, self.sum_packets/env.now)

            # if debug_state and (source == 5 and destination == 1) or (source == 1 and destination == 5):
            #     print('Time', env.now, 'Link received', packet.__class__.__name__, packet.id)

            with self.send[destination].request() as req:  # Generate a request event
                yield req
                while self.last_dest[0] != destination and env.now < self.last_dest[1]:
                    # print('Time', env.now, packet.__class__.__name__, packet.id, 'Waiting at', self, 'until', self.last_dest[1])
                    yield env.timeout(self.last_dest[1] - env.now)
                    # print('Time', env.now, 'Waited until now')

                # print('Time', env.now, 'Link sending', packet.__class__.__name__, packet.id, 'from', source, 'to', destination)
                self.last_dest = (destination, env.now + (packet.size/self.link_rate * 1000) + self.link_delay)
                yield env.timeout(packet.size/self.link_rate * 1000)
                # "Prev" buffer
                if packet.__class__.__name__ == "DataPacket":
                    self.graph_buffocc.add_point(env.now, self.buffer.capacity - self.buffer.level)

                self.remove_from_buffer(packet, packet.size, env)

                # Buffer--
                if packet.__class__.__name__ == "DataPacket":
                    self.graph_buffocc.add_point(env.now, self.buffer.capacity - self.buffer.level)
            yield env.timeout(self.link_delay)
            self.graph_delay.add_point(env.now, env.now - time_enter_queue)
            self.devices[destination].receive_packet(packet, env)
        else:
            # Dropped packet
            if env.now == self.last_dropped_time:
                # It's part of a chunk of packets dropped at the same time
                self.current_dropped += 1
            else:
                # It's the start of a new series of dropped packets
                self.last_dropped_time = env.now
                self.current_dropped = 1

            if debug_state:
                print('Time', env.now, 'Link dropped', packet.__class__.__name__, packet.id, 'from Device', source, 'to Device', destination)
