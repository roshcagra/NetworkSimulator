def generate_id():
    return 1

class Packet:
    def __init__(self, source, destination):
        self.id = generate_id()
        self.source = source
        self.destination = destination
