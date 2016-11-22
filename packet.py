class Packet(object):
    def __init__(self, p_id, source, destination):
        self.id = p_id
        self.source = source # ip
        self.destination = destination # ip

class DataPacket(Packet):
    """TODO: Data Packet"""
    size = 1024
    def __init__(self, p_id, source, destination, time):
        super(DataPacket, self).__init__(p_id=p_id, source=source, destination=destination)
        self.time = time

class AckPacket(Packet):
    """TODO: Acknowledgement Packet"""
    size = 64
    def __init__(self, p_id, source, destination, data):
        super(AckPacket, self).__init__(p_id=p_id, source=source, destination=destination)
        self.data = data

class RouterPacket(Packet):
    """TODO: Router Packet"""
    size = 64
    def __init__(self, p_id, source, distance_table, time_sent):
        super(RouterPacket, self).__init__(source=source)
        self.distance_table = distance_table
        self.time_sent = time_sent