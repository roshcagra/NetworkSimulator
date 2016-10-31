class Link:
    def __init__(self, left, right, link_rate, link_delay, max_buffer_size):
        self.left = left # left device
        self.right = right # right device

        self.buffer = [] # the buffer of packets. holds LinkPacket objects. a queue
        self.link_rate = link_rate # aka capacity/transmission delay
        self.link_delay = link_delay # propogation delay
        self.max_buffer_size = max_buffer_size

        # todo check input types
        # assert that left and right are 'devices'
        # assert that capacity is a number
        # assert that


    # Loops through queue and sums up packet sizes
    def get_buffer_size():
        pass


    def send_packet():
        pass
    	# pops off top of buffer, sends to either left or right

    def recieve_packet():
        pass
