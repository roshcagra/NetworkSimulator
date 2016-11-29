import simpy
from device import Host
from link import Link

from graphing import Graph
import matplotlib.pyplot as plt
import matplotlib.animation as animation

env = simpy.Environment()

data1 = 2 * 10 ** 7
devices = [Host(ip=0), Host(ip=1)]
links = [Link(link_rate=(2.578 * 10 ** 11), link_delay=10, max_buffer_size=64000, env=env)]

devices[0].add_link(links[0])
devices[1].add_link(links[0])

links[0].add_device(devices[0])
links[0].add_device(devices[1])

# For graphing
fig = plt.figure()
subplots = []

def flow(data, start, source, destination, sim_env):
    yield sim_env.timeout(start)
    sim_env.process(devices[source].start_flow(data=data, destination=destination, env=sim_env))
# def graph(data, start, source, destination, sim_env):
#     yield sim_env.timeout(start)
#     sim_env.process(devices[source].start_flow(data=data, destination=destination, env=sim_env))


p = env.process(flow(data1, 1000, 0, 1, env))
env.run()

for device in devices:
    device_name = "Device " + str(device.ip)
    device.graph_wsize.set_name(device_name + " " + device.graph_wsize.title)
    device.graph_wsize.plot()
    device.graph_dropped.set_name(device_name + " " + device.graph_dropped.title)
    device.graph_dropped.plot()

    for l in range(0, len(device.links)):
        link = device.links[l]
        link.graph_buffocc.set_name(device_name + " " + "Link " + str(l))
        link.graph_buffocc.plot()
