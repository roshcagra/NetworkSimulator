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

    # Loops through queue and sums up packet sizes
    def send_data(self, packet_tuple, destination, env):
        packet_num = packet_tuple[0]
        packets = packet_tuple[1]
        num = self.get_queue(packet_num, DataPacket.size)
        with self.send.request() as req:  # Generate a request event
            yield req
            for i in range(0, num):
                packet = packets[i]
                yield env.timeout(packet.size/self.link_rate * 1000)
                env.process(self.send_data_packet(packet, destination, env))

    def send_ack(self, packet, destination, env):
        num = self.get_queue(1, AckPacket.size)
        with self.send.request() as req:  # Generate a request event
            yield req
            for _ in range(0, num):
                yield env.timeout(packet.size/self.link_rate * 1000)
                env.process(self.send_ack_packet(packet, destination, env))
