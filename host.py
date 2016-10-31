class Host:
    def __init__(self, link):
        self.link = link

    def send(self, packet):
        self.link.send(packet)
