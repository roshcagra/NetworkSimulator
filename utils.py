from device import Router

def flow(data, start, source, destination, sim_env):
    yield sim_env.timeout(start)
    sim_env.process(source.start_flow(data=data, destination=destination, env=sim_env))

def dynamic_routing(devices, sim_env):
	for i in range(100):
	    for device in devices:
	        if isinstance(device, Router):
	            device.send_router(sim_env)
	    yield sim_env.timeout(1000)
