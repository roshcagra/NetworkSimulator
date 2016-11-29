from device import Router
import simpy

def flow(data, start, source, destination, sim_env):
    yield sim_env.timeout(start)
    sim_env.process(source.start_flow(data=data, destination=destination, env=sim_env))

def dynamic_routing(devices, interval, sim_env):
    while True:

        for _ in range(4):

            for device in devices:
                if isinstance(device, Router):
                    device.send_router(sim_env)
            yield sim_env.timeout(12)

        yield sim_env.timeout(interval)



        if all_events_processed(sim_env):
            print('All flows are dead. Simulation is over. Stop running routing algorithm. ')
            break

# Events is a list of simpy 'Events.' When the event is done (for example, if the event is a flow, the event
# is done when the flow is done sending packets), event.processed will be set to True
def all_events_processed(sim_env):
    return sim_env.peek() == simpy.core.Infinity


