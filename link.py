import simpy
from graphing import Graph
from packet import RouterPacket

debug_state = False

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
        self.graph_buffocc = Graph("Buffer Occupancy", "buffocc",self.id)
        self.graph_delay = Graph("Packet Delay", "delay",self.id)
        self.graph_linkrate = Graph("Link Rate", "linkrate",self.id)
        self.graph_dropped = Graph("Packet Loss", "dropped",self.id)
        self.current_dropped = 0 # number of packets dropped at this time
        self.last_dropped_time = 0
        self.sum_queued = 0     # number of packets that have ever been queued
        self.sum_queuetime = 0  # sum of all queue wait times

        self.linkrate_interval = 100 # running avg window
        self.linkrate_start = 0 # abs start time of avg window
        self.linkrate_count = 0 # total Mb sent in this interval
        self.linkrate_sum = 0

        self.buffocc_interval = 100 # running avg window
        self.buffocc_start = 0 # abs start time of avg window
        self.buffocc_count = 0 # total Mb sent in this interval
        self.buffocc_sum = 0

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

    def insert_into_buffer(self, packet, packet_size, env):
        # Plot "prev"
        #self.graph_buffocc.add_point(env.now, self.buffer.capacity - self.buffer.level)
        self.buffocc_sum += self.buffer.capacity - self.buffer.level
        self.buffocc_count += 1

        if packet_size <= self.buffer.level:
            self.buffer.get(packet_size)
            # Buffer++
            #self.graph_buffocc.add_point(env.now, self.buffer.capacity - self.buffer.level)
            self.buffocc_sum += self.buffer.capacity - self.buffer.level
            self.buffocc_count += 1
            
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

        # Link rate: graph it once we hit interval
        if self.linkrate_start + self.linkrate_interval <= env.now:
            # Passed end of window: plot avg and reset
            self.graph_linkrate.add_point(env.now,
                (1.0 * self.linkrate_sum)/max(1.0, self.linkrate_count))
            self.linkrate_count = 0
            self.linkrate_sum = 0
            self.linkrate_start = env.now

        # Buffocc: graph it once we hit interval
        if self.buffocc_start + self.buffocc_interval <= env.now:
            # Passed end of window: plot avg and reset
            self.graph_buffocc.add_point(env.now,
                (1.0 * self.buffocc_sum)/max(1.0, self.buffocc_count))
            self.buffocc_count = 0
            self.buffocc_sum = 0
            self.buffocc_start = env.now


        if self.insert_into_buffer(packet, packet.size, env):
            time_enter_queue = env.now
            # Buffer ++

            self.graph_dropped.add_point(env.now, self.current_dropped)
            self.current_dropped = 0
            self.graph_dropped.add_point(env.now, self.current_dropped)

            # A packet is succesfully put onto link
            # if self.linkrate_start + self.linkrate_interval > env.now:
            #     # Still in window: collect data
            #     self.linkrate_count += packet.size
            # else:
            #     # End of window: plot avg and reset
            #     self.graph_linkrate.add_point(env.now,
            #         self.linkrate_count/self.linkrate_interval)
            #     self.linkrate_count = 0
            #     self.linkrate_start = env.now

            self.linkrate_count += 1 # This many packets travelled on link
            getonlink = env.now # Time it got onto link

            with self.send.request() as req:  # Generate a request event
                yield req
                if self.last_dest[0] != destination and self.last_dest[0] != -1:
                    next_time = self.last_dest[1]
                    yield env.timeout(max(0, next_time - env.now))
                yield env.timeout(packet.size/self.link_rate * 1000)
                # "Prev" buffer
                if packet.__class__.__name__ == "DataPacket":
                    #self.graph_buffocc.add_point(env.now, self.buffer.capacity - self.buffer.level)
                    self.buffocc_sum += self.buffer.capacity - self.buffer.level
                    self.buffocc_count += 1

                self.remove_from_buffer(packet, packet.size, env)

                # Buffer--
                if packet.__class__.__name__ == "DataPacket":
                    #self.graph_buffocc.add_point(env.now, self.buffer.capacity - self.buffer.level)
                    self.buffocc_sum += self.buffer.capacity - self.buffer.level
                    self.buffocc_count += 1

                self.last_dest = (destination, env.now + self.link_delay)
            yield env.timeout(self.link_delay)

            self.graph_delay.add_point(env.now, env.now - time_enter_queue)

            # Link rate
            getofflink = env.now # Time it got off link
            traveltime = getofflink - getonlink
            self.linkrate_sum += (1.0 * packet.size)/traveltime # Travel speed for one packet

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
