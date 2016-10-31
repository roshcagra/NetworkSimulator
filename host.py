class Host:
    def __init__(self, link, ip):
        self.link = link
        self.ip = ip

    def send(self, packet):
        self.link.send(packet)
