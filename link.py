import simpy
from graphing import Graph
from packet import RouterPacket

debug_state = False
update_interval = 500

class Link:
    def __init__(self, l_id, link_rate, link_delay, max_buffer_size, env):
        self.devices = {} # ip -> device object
        self.id = l_id    # for graphing
        self.link_rate = link_rate # aka capacity/transmission delay
        self.link_delay = link_delay # propogation delay
        self.send = simpy.Resource(env, capacity=1)
        self.buffer = simpy.Container(env, init=max_buffer_size, capacity=max_buffer_size)
        self.router_occ_size = 0
        self.last_dest = (-1, 0)

        self.graph_buffocc = Graph("Link" + str(self.id))
        self.last_buff_occ_check = 0
        self.buffer_sizes = []

        self.graph_delay = Graph("Link" + str(self.id))
        self.last_delay_time_check = 0
        self.delay_times = []

        self.graph_dropped = Graph("Link" + str(self.id))
        self.current_dropped = 0 # number of packets dropped at this time
        self.last_dropped_time = 0

        self.graph_linkrate = Graph("Link" + str(self.id))
        self.last_linkrate_check = 0
        self.linkrate_count = 0

    def add_device(self, device):
        self.devices[device.ip] = device

    def getOtherDevice(self, my_ip):
        for ip in self.devices:
            if ip != my_ip:
                return self.devices[ip]

    def __repr__(self):
        return 'Link from' + str(list(self.devices.keys())[0]) + 'to' + str(list(self.devices.keys())[1])

    def __str__(self):
        return 'Link from' + str(list(self.devices.keys())[0]) + 'to' + str(list(self.devices.keys())[1])

    def update_buffocc(self, time):
        if self.last_buff_occ_check + update_interval < time:
            buffer_average = sum(self.buffer_sizes) / len(self.buffer_sizes)
            self.graph_buffocc.add_point(time, buffer_average)
            self.last_buff_occ_check = time
            self.buffer_sizes = []

    def update_delay_times(self, time):
        if self.last_delay_time_check + update_interval < time:
            delay_average = sum(self.delay_times) / len(self.delay_times)
            self.graph_delay.add_point(time, delay_average)
            self.last_delay_time_check = time
            self.delay_times = []

    def update_linkrate(self, time):
        if self.last_linkrate_check + update_interval < time:
            curr_count = self.linkrate_count
            self.graph_linkrate.add_point(time, curr_count / (time - self.last_linkrate_check))
            self.last_linkrate_check = time
            self.linkrate_count = 0

    def insert_into_buffer(self, packet, packet_size, env):
        self.buffer_sizes.append(self.buffer.capacity - self.buffer.level)
        self.update_buffocc(env.now)

        if packet_size <= self.buffer.level:
            self.buffer.get(packet_size)

            packet.t_enterbuff = env.now
            if isinstance(packet, RouterPacket):
                self.router_occ_size += RouterPacket.size
            return True
        else:
            return False

    def remove_from_buffer(self, packet, packet_size, env):
        self.buffer.put(packet_size)
        if isinstance(packet, RouterPacket):
            self.router_occ_size -= RouterPacket.size

    def send_packet(self, packet, source, env):
        destination = -1
        for ip in self.devices:
            if ip != source:
                destination = ip

        if self.insert_into_buffer(packet, packet.size, env):
            time_enter_queue = env.now

            self.graph_dropped.add_point(env.now, self.current_dropped)
            self.current_dropped = 0
            self.graph_dropped.add_point(env.now, self.current_dropped)

            with self.send.request() as req:  # Generate a request event
                yield req

                self.delay_times.append(env.now - time_enter_queue)
                self.update_delay_times(env.now)

                if self.last_dest[0] != destination and self.last_dest[0] != -1:
                    next_time = self.last_dest[1]
                    yield env.timeout(max(0, next_time - env.now))
                yield env.timeout(packet.size/self.link_rate * 1000)
                self.remove_from_buffer(packet, packet.size, env)
                self.last_dest = (destination, env.now + self.link_delay)
            yield env.timeout(self.link_delay)

            # Link rate
            self.linkrate_count += packet.size
            self.update_linkrate(env.now)

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
