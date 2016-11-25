import simpy
from device import Host
from device import Router
from link import Link
from utils import flow
from utils import dynamic_routing
env = simpy.Environment()

data1 = 1024 * 5000
devices = [Host(ip=0), Host(ip=1),
Router(ip=2, routing_table={0:0, 1:1}),
Router(ip=3, routing_table={0:0, 1:1}),
Router(ip=4, routing_table={0:0, 1:1}),
Router(ip=5, routing_table={0:1, 1:2})]
links = [Link(link_rate=(1562500), link_delay=10, max_buffer_size=64000, env=env),
Link(link_rate=(1.25 * 10 ** 6), link_delay=10, max_buffer_size=64000, env=env),
Link(link_rate=(1.25 * 10 ** 6), link_delay=10, max_buffer_size=64000, env=env),
Link(link_rate=(1.25 * 10 ** 6), link_delay=10, max_buffer_size=64000, env=env),
Link(link_rate=(1.25 * 10 ** 6), link_delay=10, max_buffer_size=64000, env=env),
Link(link_rate=(1562500), link_delay=10, max_buffer_size=64000, env=env)
]

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

p = env.process(flow(data1, 500, devices[0], 1, env))
env.run()

for device in devices:
    device_name = "Device " + str(device.ip)
    device.graph_wsize.set_name(device_name)
    device.graph_wsize.plot()
    for l in range(0, len(device.links)):
        link = device.links[l]
        link.graph_buffocc.set_name(device_name + " " + "Link " + str(l))
        link.graph_buffocc.plot()