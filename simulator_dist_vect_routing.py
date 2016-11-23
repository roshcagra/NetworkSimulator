import simpy
from device import Host
from device import Router
from link import Link

env = simpy.Environment()

# Simulates 4 Routers
'''

				r0
			  -    -
		     -       -
		   r3         - r1
			-        -
			 -	   -
			   -r2


'''

data1 = 1024 * 1000
links = [Link(link_rate=(2.578 * 10 ** 11), link_delay=1, max_buffer_size=64000, env=env), \
		Link(link_rate=(2.578 * 10 ** 11), link_delay=1, max_buffer_size=64000, env=env), \
		Link(link_rate=(2.578 * 10 ** 11), link_delay=1, max_buffer_size=64000, env=env), \
		Link(link_rate=(2.578 * 10 ** 11), link_delay=1, max_buffer_size=64000, env=env)]

devices = [Router(ip=0), Router(ip=1), Router(ip=2), Router(ip=3)]



devices[0].add_link(links[0]) 
devices[0].add_link(links[3]) 
devices[1].add_link(links[0]) 
devices[1].add_link(links[1]) 
devices[2].add_link(links[1])
devices[2].add_link(links[2])
devices[3].add_link(links[3])
devices[3].add_link(links[2])

links[0].add_device(devices[0])
links[0].add_device(devices[1])
links[1].add_device(devices[1])
links[1].add_device(devices[2])
links[2].add_device(devices[2])
links[2].add_device(devices[3])
links[3].add_device(devices[3])
links[3].add_device(devices[0])

# def flow(data, start, source, destination, sim_env):
#     yield sim_env.timeout(start)
#     sim_env.process(devices[source].start_flow(data=data, destination=destination, env=sim_env))

# p = env.process(flow(data1, 1000, 0, 1, env))

def bell_it_up(env):
	for i in range(200): # run 20 iterations 
		for router in devices:
			router.send_router(env)
		yield env.timeout(100)


	def print_routing_table(router):
		print('-------------')
		print('router ' + str(router.ip))
		for ip in router.routing_table:
			print('destination: ' + str(ip) + ' link: ' + str(links.index(router.routing_table[ip])) + ' cost: ' +  str(router.distance_table[ip]))

	for router in devices:
		print_routing_table(router)

	print('LINK 0 COST INCREASE TO 20')
	links[0].link_delay = 20

	for i in range(200): # run 20 iterations 
		for router in devices:
			router.send_router(env)
		yield env.timeout(100)

	for router in devices:
		print_routing_table(router)

p = env.process(bell_it_up(env))
env.run()




