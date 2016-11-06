import simpy
from device import Host
from link import Link

env = simpy.Environment()

data1 = 1.6 * (10 ** 8)
devices = [Host(env=env, ip=0, W=10), Host(env=env, ip=1, W=10)]
links = [Link(0, 1, 10 ** 7, .01, 64000, env)]

devices[0].add_link(links[0])
devices[1].add_link(links[0])

links[0].add_device(devices[0])
links[0].add_device(devices[1])

def flow(data, start, source, destination):
    yield env.timeout(start)
    env.process(devices[source].sendData(data=data, destination=destination, env=env))

p = env.process(flow(data1, 1, 0, 1))
env.run()
