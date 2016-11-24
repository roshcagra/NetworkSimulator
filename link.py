import simpy
from graphing import Graph

class Link:
    def __init__(self, link_rate, link_delay, max_buffer_size, env):
        self.devices = {} # ip -> device object
        self.link_rate = link_rate # aka capacity/transmission delay
        self.link_delay = link_delay # propogation delay
        self.send = simpy.Resource(env, capacity=1)
        self.buffer = simpy.Container(env, init=max_buffer_size, capacity=max_buffer_size)
        self.last_dest = (-1, 0)
        self.graph_buffocc = Graph("Buffer Occupancy")

    def add_device(self, device):
        self.devices[device.ip] = device

    def insert_into_buffer(self, packet_size, env):
        if packet_size <= self.buffer.level:
            self.buffer.get(packet_size)
            self.graph_buffocc.add_point(env.now, self.buffer.capacity - self.buffer.level)
            return True
        else:
            return False

    def remove_from_buffer(self, packet_size, env):
        self.buffer.put(packet_size)
        self.graph_buffocc.add_point(env.now, self.buffer.capacity - self.buffer.level)

    def send_packet(self, packet, source, env):
        destination = -1
        for ip in self.devices:
            if ip != source:
                destination = ip

        if self.insert_into_buffer(packet.size, env):
            with self.send.request() as req:  # Generate a request event
                yield req
                if self.last_dest[0] != destination and self.last_dest[0] != -1:
                    next_time = self.last_dest[1]
                    yield env.timeout(max(0, next_time - env.now))
                print('Time', env.now, 'Link sending', packet.__class__.__name__, packet.id, 'from Device', source, 'to Device', destination)
                yield env.timeout(packet.size/self.link_rate * 1000)
                self.remove_from_buffer(packet.size, env)
                self.last_dest = (destination, env.now + self.link_delay)
            yield env.timeout(self.link_delay)
            self.devices[destination].receive_packet(packet, env)
