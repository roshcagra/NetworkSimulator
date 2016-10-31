import simpy
from host import Host
from packet import DataPacket
from link import Link

data = 1.6 * (10 ** 8)
devices = [Host(0), Host(1)]
links = [Link(0, 1)]

def flow(env, data, start, source, destination):
    yield env.timeout(start)
    devices[source].send(data, destination)

env = simpy.Environment()
p = env.process(flow(env, data, 1, 0, 1))
env.run()
