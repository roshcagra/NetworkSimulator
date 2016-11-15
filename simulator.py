import simpy
from device import Host
from link import Link

env = simpy.Environment()

data1 = 1024 * 1000
devices = [Host(ip=0), Host(ip=1)]
links = [Link(link_rate=(2.578 * 10 ** 11), link_delay=10, max_buffer_size=64000, env=env)]

devices[0].add_link(links[0])
devices[1].add_link(links[0])

links[0].add_device(devices[0])
links[0].add_device(devices[1])

def flow(data, start, source, destination, sim_env):
    yield sim_env.timeout(start)
    sim_env.process(devices[source].start_flow(data=data, destination=destination, env=sim_env))

p = env.process(flow(data1, 1000, 0, 1, env))
env.run()
