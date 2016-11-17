import simpy
import math
from packet import DataPacket
from packet import AckPacket

class Link:
    def __init__(self, link_rate, link_delay, max_buffer_size, env):
        self.devices = {} # ip -> device object
        self.link_rate = link_rate # aka capacity/transmission delay
        self.link_delay = link_delay # propogation delay
        self.send = simpy.Resource(env, capacity=1)
        self.queue = simpy.Container(env, init=max_buffer_size, capacity=max_buffer_size)
        self.last_dest = (-1, 0)

    def add_device(self, device):
        self.devices[device.ip] = device

    def get_queue(self, packet_size):
        if packet_size <= self.queue.level:
            self.queue.get(packet_size)
            return True
        else:
            return False

    def send_data_packet(self, packet, destination, env):
        self.queue.put(DataPacket.size)
        yield env.timeout(self.link_delay)
        self.devices[destination].receive_data(packet, env)

    def send_ack_packet(self, packet, destination, env):
        self.queue.put(AckPacket.size)
        yield env.timeout(self.link_delay)
        self.devices[destination].receive_ack(packet, env)

    def send_packet(self, packet, source, env):
        destination = -1
        for ip in self.devices:
            if ip != source:
                destination = ip

        if self.get_queue(packet.size):
            with self.send.request() as req:  # Generate a request event
                yield req
                if self.last_dest[0] != destination and self.last_dest[0] != -1:
                    next_time = self.last_dest[1]
                    yield env.timeout(max(0, next_time - env.now))
                if isinstance(packet, DataPacket):
                    print('Link sending data packet:', packet.id, 'from', source, 'to', destination, 'at', env.now)
                    yield env.timeout(packet.size/self.link_rate * 1000)
                    env.process(self.send_data_packet(packet, destination, env))
                elif isinstance(packet, AckPacket):
                    print('Link sending ack packet: ', packet.id, 'from', source, 'to', destination,' at ', env.now)
                    yield env.timeout(packet.size/self.link_rate * 1000)
                    env.process(self.send_ack_packet(packet, destination, env))
                self.last_dest = (destination, env.now + self.link_delay)
