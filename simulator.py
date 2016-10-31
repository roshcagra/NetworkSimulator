import simpy
from device import Host
from link import Link

env = simpy.Environment()

data1 = 1.6 * (10 ** 8)
devices = [Host(env, 0, 10), Host(env, 1, 10)]
links = [Link(0, 1, 10 ** 7, .01, 64000)]

def flow(data, start, source, destination):
    yield env.timeout(start)
    env.process(devices[source].sendData(data, destination))

p = env.process(flow(data1, 1, 0, 1))
env.run()
