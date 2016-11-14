import simpy
from packet import DataPacket
from packet import AckPacket

class Link:
    def __init__(self, link_rate, link_delay, max_buffer_size, env):
        self.devices = {}
        self.buffer = [] # the buffer of packets. holds LinkPacket objects. a queue
        self.link_rate = link_rate # aka capacity/transmission delay
        self.link_delay = link_delay # propogation delay
        self.send = simpy.Resource(env, capacity=1)
        self.queue = simpy.Container(env, init=max_buffer_size, capacity=max_buffer_size)
        self.last_dest = (-1, 0)

    def add_device(self, device):
        self.devices[device.ip] = device

    def get_queue(self, packet_num, packet_size):
        amount = min(self.queue.level, packet_num * packet_size)
        num = amount // packet_size
        if num == 0:
            return num
        self.queue.get(amount)
        return num

    def send_data_packet(self, packet, destination, env):
        self.queue.put(DataPacket.size)
        yield env.timeout(self.link_delay)
        self.devices[destination].receive_data(packet, env)

    def send_ack_packet(self, packet, destination, env):
        self.queue.put(AckPacket.size)
        yield env.timeout(self.link_delay)
        self.devices[destination].receive_ack(packet, env)

    def send_data(self, packets, destination, env):
        packet_num = len(packets)
        num = self.get_queue(packet_num, DataPacket.size)
        with self.send.request() as req:  # Generate a request event
            yield req
            if self.last_dest[0] != destination and self.last_dest[0] != -1:
                next_time = self.last_dest[1]
                yield env.timeout(next_time - env.now)
            for i in range(0, num):
                packet = packets[i]
                print('Sending data packet: ', packet.id, ' at ', env.now)
                yield env.timeout(packet.size/self.link_rate * 1000)
                env.process(self.send_data_packet(packet, destination, env))
            self.last_dest = (destination, env.now + self.link_delay)

    def send_ack(self, packet, destination, env):
        num = self.get_queue(1, AckPacket.size)
        with self.send.request() as req:  # Generate a request event
            yield req
            if self.last_dest[0] != destination and self.last_dest[0] != -1:
                next_time = self.last_dest[1]
                yield env.timeout(next_time - env.now)
            for _ in range(0, num):
                print('Sending ack packet: ', packet.id, ' at ', env.now)
                yield env.timeout(packet.size/self.link_rate * 1000)
                env.process(self.send_ack_packet(packet, destination, env))
            self.last_dest = (destination, env.now + self.link_delay)
