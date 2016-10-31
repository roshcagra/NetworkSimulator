def generate_id():
    return 1

class Packet(object):
    def __init__(self, source, destination):
        self.id = generate_id()
        self.source = source
        self.destination = destination

class DataPacket(Packet):
	"""TODO: Data Packet"""
	size = 8192
	def __init__(self, id, source, destination):
		super(DataPacket, self).__init__(id=id, source=source, destination=destination)

class AcknowledgementPacket(Packet):
	"""TODO: Acknowledgement Packet"""
	size = 512
	def __init__(self, id, source, destination):
		super(AcknowledgementPacket, self).__init__(id=id, source=source, destination=destination)

class RouterPacket(Packet):
	"""TODO: Router Packet"""
	size = 512
	def __init__(self, id, source, destination):
		super(RouterPacket, self).__init__(source=source, destination=destination)