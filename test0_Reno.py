import simpy
from device import Host
from link import Link
from utils import flow
from utils import graph_live

env = simpy.Environment()

data1 = 20 * 10 ** 6
devices = [Host(ip=0), Host(ip=1)]
links = [
Link(l_id=0, link_rate=(2.578 * 10 ** 11), link_delay=10, max_buffer_size=64000, env=env)]

devices[0].add_link(links[0])
devices[1].add_link(links[0])

links[0].add_device(devices[0])
links[0].add_device(devices[1])

p = env.process(flow(data1, 1000, devices[0], 1, env, 'Reno'))
p = env.process(graph_live(devices, links, [0, 1], [0], env))

env.run()
