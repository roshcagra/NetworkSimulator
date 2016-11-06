import simpy

class Link:
    def __init__(self, left, right, link_rate, link_delay, max_buffer_size, env):
        self.devices = {}
        self.devices[left] = None
        self.devices[right] = None
        self.env = env
        self.buffer = [] # the buffer of packets. holds LinkPacket objects. a queue
        self.link_rate = link_rate # aka capacity/transmission delay
        self.link_delay = link_delay # propogation delay
        self.max_buffer_size = max_buffer_size
        self.send = simpy.Resource(env, capacity=1)

    def add_device(self, device):
        self.devices[device.ip] = device

    # Loops through queue and sums up packet sizes
    def send_data(self, packets, destination):
        with self.send.request() as req:  # Generate a request event
            yield req
            for packet in packets:
                self.env.timeout(packet.size/self.link_rate)
                self.devices[destination].receive(packet, self.env)

    def send_ack(self, packet, destination):
        with self.send.request() as req:  # Generate a request event
            yield req
            self.devices[destination].receive(packet, self.env)
