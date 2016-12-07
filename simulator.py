import simpy
from device import Host
from link import Link
from utils import flow

import matplotlib.pyplot as plt

env = simpy.Environment()

#data1 = 1024 * 10000
data1 = 1024 * 5000
#data1 = 2 * 10 ** 7
devices = [Host(ip=0), Host(ip=1)]
links = [Link(link_rate=(2.578 * 10 ** 11), link_delay=10, max_buffer_size=64000, env=env)]

devices[0].add_link(links[0])
devices[1].add_link(links[0])

links[0].add_device(devices[0])
links[0].add_device(devices[1])

# For graphing
fig = plt.figure()

# def graph(data, start, source, destination, sim_env):
#     yield sim_env.timeout(start)
#     sim_env.process(devices[source].start_flow(data=data, destination=destination, env=sim_env))


p = env.process(flow(data1, 1000, devices[0], 1, env, 'Reno'))
env.run()

for device in devices:
    device_name = "Device " + str(device.ip)
    device.graph_wsize.set_name(device_name)
    device.graph_wsize.plot()
    device.graph_flowrate.set_name(device_name)
    device.graph_flowrate.plot()

for i in range(0, len(links)):
    link = links[i]
    link.graph_dropped.set_name("Link " + str(i))
    link.graph_dropped.plot()
    link.graph_buffocc.set_name("Link " + str(i))
    link.graph_buffocc.plot()
    link.graph_buffocc.plot()
    link.graph_linkrate.set_name("Link " + str(i))
    link.graph_linkrate.plot()
    link.graph_delay.set_name("Link " + str(i))
    link.graph_delay.plot()
