class Packet(object):
    def __init__(self, p_id, source, destination):
        self.id = p_id
        self.source = source
        self.destination = destination

class DataPacket(Packet):
    """TODO: Data Packet"""
    size = 1024
    def __init__(self, p_id, source, destination, on_receive):
        super(DataPacket, self).__init__(p_id=p_id, source=source, destination=destination)
        self.on_receive = on_receive

class AckPacket(Packet):
    """TODO: Acknowledgement Packet"""
    size = 64
    def __init__(self, p_id, source, destination):
        super(AckPacket, self).__init__(p_id=p_id, source=source, destination=destination)

class RouterPacket(Packet):
    """TODO: Router Packet"""
    size = 64
    def __init__(self, p_id, source, destination):
        super(RouterPacket, self).__init__(source=source, destination=destination)
