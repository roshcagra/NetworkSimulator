class Packet(object):
    def __init__(self, p_id, source, destination):
        self.id = p_id
        self.source = source # ip
        self.destination = destination # ip
        self.t_enterqueue = 0    # time it was put on queue

class DataPacket(Packet):
    size = 1024
    def __init__(self, p_id, source, destination):
        super(DataPacket, self).__init__(p_id=p_id, source=source, destination=destination)

class AckPacket(Packet):
    size = 64
    def __init__(self, p_id, source, destination):
        super(AckPacket, self).__init__(p_id=p_id, source=source, destination=destination)

class RouterPacket(Packet):
    size = 64
    def __init__(self, p_id, source, distance_table, buffer_occ):
        super(RouterPacket, self).__init__(p_id=p_id, source=source, destination=-1)
        self.distance_table = distance_table
        self.buffer_occ = buffer_occ
        self.link = None

    # The link that the routerPacket came in on
    def specify_link(self, link):
        self.link = link
