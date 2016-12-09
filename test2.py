import simpy
from device import Host
from device import Router
from link import Link
from utils import flow
from utils import dynamic_routing
from utils import graph_live
env = simpy.Environment()

# routing table maps to link object, not the idx in list
devices = [Host(ip=0), Host(ip=1), Host(ip=2), Host(ip=3), Host(ip=4), Host(ip=5),
Router(ip=6),
Router(ip=7),
Router(ip=8),
Router(ip=9),]

links = [
Link(l_id = 0, link_rate=(1562500), link_delay=10, max_buffer_size=128000, env=env),
Link(l_id = 1, link_rate=(1.25 * 10 ** 6), link_delay=10, max_buffer_size=128000, env=env),
Link(l_id = 3, link_rate=(1.25 * 10 ** 6), link_delay=10, max_buffer_size=128000, env=env),
Link(l_id = 4, link_rate=(1.25 * 10 ** 6), link_delay=10, max_buffer_size=128000, env=env),
Link(l_id = 5, link_rate=(1562500), link_delay=10, max_buffer_size=128000, env=env),
Link(l_id = 6, link_rate=(1562500), link_delay=10, max_buffer_size=128000, env=env),
Link(l_id = 7, link_rate=(1562500), link_delay=10, max_buffer_size=128000, env=env),
Link(l_id = 8, link_rate=(1562500), link_delay=10, max_buffer_size=128000, env=env),
Link(l_id = 9, link_rate=(1562500), link_delay=10, max_buffer_size=128000, env=env),
]


#L0
links[0].add_device(devices[2])
links[0].add_device(devices[6])

#L1
links[1].add_device(devices[6])
links[1].add_device(devices[7])

#L2
links[2].add_device(devices[7])
links[2].add_device(devices[8])

#L3
links[3].add_device(devices[8])
links[3].add_device(devices[9])

#L4
links[4].add_device(devices[6])
links[4].add_device(devices[0])

#L5
links[5].add_device(devices[3])
links[5].add_device(devices[7])

#L6
links[6].add_device(devices[4])
links[6].add_device(devices[8])

#L7
links[7].add_device(devices[1])
links[7].add_device(devices[9])

#L8
links[8].add_device(devices[9])
links[8].add_device(devices[5])

#H0
devices[0].add_link(links[4])

#H1
devices[1].add_link(links[7])

#H2
devices[2].add_link(links[0])

#H3
devices[3].add_link(links[5])

#H4
devices[4].add_link(links[6])

#H5
devices[5].add_link(links[8])

#R1
devices[6].add_link(links[0])
devices[6].add_link(links[1])
devices[6].add_link(links[4])

#R2
devices[7].add_link(links[1])
devices[7].add_link(links[5])
devices[7].add_link(links[2])

#R3
devices[8].add_link(links[2])
devices[8].add_link(links[6])
devices[8].add_link(links[3])

#R4
devices[9].add_link(links[3])
devices[9].add_link(links[7])
devices[9].add_link(links[8])

#F1
# data1 = 35 * 10 ** 6
data1 = 1024 * 2000
p = env.process(flow(data1, 500, devices[0], 1, env, 'Reno'))

#F2
# data2 = 15 * 10 ** 6
data2 = 1024 * 2000
p = env.process(flow(data2, 10000, devices[2], 3, env, 'Reno'))

#F3
# data2 = 30 * 10 ** 6
data3 = 1024 * 2000
p = env.process(flow(data2, 20000, devices[4], 5, env, 'Reno'))
r = env.process(dynamic_routing(devices=devices, interval=5000, sim_env=env))
g = env.process(graph_live(devices, links, [0, 1, 2, 3, 4, 5], [1, 2, 3], env))
# events is the list of other processes besides the routing process. once all the events have been processed
# the dynamic routing process knows to stop.


env.run()
