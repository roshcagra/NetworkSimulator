import simpy
from device import Host
from device import Router
from link import Link

env = simpy.Environment()

# Simulates Host - Router - Host

data1 = 1024 * 1000
links = [Link(link_rate=(2.578 * 10 ** 11), link_delay=10, max_buffer_size=64000, env=env), \
		Link(link_rate=(2.578 * 10 ** 11), link_delay=10, max_buffer_size=64000, env=env), \
		Link(link_rate=(2.578 * 10 ** 11), link_delay=10, max_buffer_size=64000, env=env), \
		Link(link_rate=(2.578 * 10 ** 11), link_delay=10, max_buffer_size=64000, env=env)]

devices = [Router(ip=0), Router(ip=1), Router(ip=2), Router(ip=3)]



devices[0].add_link(links[0]) # Host 1
devices[1].add_link(links[1]) # Host 2
devices[2].add_link(links[0]) # Router
devices[2].add_link(links[1])

links[0].add_device(devices[0])
links[0].add_device(devices[2])
links[1].add_device(devices[2])
links[1].add_device(devices[1])

# def flow(data, start, source, destination, sim_env):
#     yield sim_env.timeout(start)
#     sim_env.process(devices[source].start_flow(data=data, destination=destination, env=sim_env))

# p = env.process(flow(data1, 1000, 0, 1, env))

def bell_it_up(env):
	for i in range(20): # run 20 iterations 
		for router in devices:
			router.send_router(env)


p = env.process(bell_it_up(env))
env.run()
