class Device:	
    
    def __init__(self, ip):
        self.ip = ip
        self.links = []

    def add_link(self, link):
    	self.link.append = link;

    def send(self, data, destination):
        self.link.send(data, destination)

    def receive(self, data):
        self.link[link_id].receive(data)


class Host(Device):

    def __init__(self, ip, W):
        Device.__init__(self, ip)
        self.window_size = W

    def handle_ack(self, packet):
    	''' Handle processing the acknowledgement '''

class Router(Device):

    def __init__(self, ip):
        Device.__init__(self, ip)
        self.routing_table = None

    def handle_routing(self, packet):
    	''' Do MST and generate table '''
