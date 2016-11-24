import simpy
from device import Host
from device import Router
from link import Link

env = simpy.Environment()

# Simulates Host - Router - Host

data1 = 1024 * 4000
links = [Link(link_rate=(2.578 * 10 ** 11), link_delay=10, max_buffer_size=64000, env=env), Link(link_rate=(2.578 * 10 ** 11), link_delay=10, max_buffer_size=64000, env=env)]
devices = [Host(ip=0), Host(ip=1)]

routing_table = {}
routing_table[0] = links[0]
routing_table[1] = links[1]
devices.append(Router(ip=2,routing_table=routing_table))


devices[0].add_link(links[0]) # Host 1
devices[1].add_link(links[1]) # Host 2
devices[2].add_link(links[0]) # Router
devices[2].add_link(links[1])

links[0].add_device(devices[0])
links[0].add_device(devices[2])
links[1].add_device(devices[2])
links[1].add_device(devices[1])

def flow(data, start, source, destination, sim_env):
    yield sim_env.timeout(start)
    sim_env.process(devices[source].start_flow(data=data, destination=destination, env=sim_env))

p = env.process(flow(data1, 1000, 0, 1, env))
env.run()

for device in devices:
    device_name = "Device " + str(device.ip)
    device.graph_wsize.set_name(device_name)
    device.graph_wsize.plot()
    for l in range(0, len(device.links)):
        link = device.links[l]
        link.graph_buffocc.set_name(device_name + " " + "Link " + str(l))
        link.graph_buffocc.plot()
