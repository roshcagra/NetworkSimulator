import simpy
from device import Host
from device import Router
from link import Link
from utils import flow
from utils import dynamic_routing
from utils import graph_live
env = simpy.Environment()

data1 = 20 * 10 ** 6

# data1 = 1024 * 5000 * 0

# routing table maps to link object, not the idx in list
devices = [Host(ip=0), Host(ip=1),
Router(ip=2),
Router(ip=3),
Router(ip=4),
Router(ip=5)]
links = [
Link(l_id = 0, link_rate=(1562500), link_delay=10, max_buffer_size=64000, env=env),
Link(l_id = 1, link_rate=(1.25 * 10 ** 6), link_delay=10, max_buffer_size=64000, env=env),
Link(l_id = 2, link_rate=(1.25 * 10 ** 6), link_delay=10, max_buffer_size=64000, env=env),
Link(l_id = 3, link_rate=(1.25 * 10 ** 6), link_delay=10, max_buffer_size=64000, env=env),
Link(l_id = 4, link_rate=(1.25 * 10 ** 6), link_delay=10, max_buffer_size=64000, env=env),
Link(l_id = 5, link_rate=(1562500), link_delay=10, max_buffer_size=64000, env=env)
]


#L0
links[0].add_device(devices[0])
links[0].add_device(devices[2])

#L1
links[1].add_device(devices[2])
links[1].add_device(devices[3])

#L2
links[2].add_device(devices[2])
links[2].add_device(devices[4])

#L3
links[3].add_device(devices[3])
links[3].add_device(devices[5])

#L4
links[4].add_device(devices[4])
links[4].add_device(devices[5])

#L5
links[5].add_device(devices[5])
links[5].add_device(devices[1])

#H1
devices[0].add_link(links[0])

#H2
devices[1].add_link(links[5])

#R1
devices[2].add_link(links[0])
devices[2].add_link(links[1])
devices[2].add_link(links[2])

#R2
devices[3].add_link(links[1])
devices[3].add_link(links[3])

#R3
devices[4].add_link(links[2])
devices[4].add_link(links[4])

#R4
devices[5].add_link(links[3])
devices[5].add_link(links[4])
devices[5].add_link(links[5])


p = env.process(flow(data1, 500, devices[0], 1, env, 'FAST'))
r = env.process(dynamic_routing(devices=devices, interval=5000, sim_env=env))
p = env.process(graph_live(devices, links, env, [0, 1], [1, 2]))

# events is the list of other processes besides the routing process. once all the events have been processed
# the dynamic routing process knows to stop.


env.run()
