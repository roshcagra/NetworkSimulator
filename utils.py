from device import Router
import simpy

def flow(data, start, source, destination, sim_env):
    yield sim_env.timeout(start)
    sim_env.process(source.start_flow(data=data, destination=destination, env=sim_env))

def dynamic_routing(devices, interval, sim_env):
    short_interval = 1
    while True:
        for zzzz in range(20):
            for device in devices:
                if isinstance(device, Router):
                    device.send_router(sim_env)
            yield sim_env.timeout(short_interval)

        yield sim_env.timeout(interval)


        if all_events_processed(sim_env):
            print('All flows are dead. Simulation is over. Stop running routing algorithm. ')
            break

# Events is a list of simpy 'Events.' When the event is done (for example, if the event is a flow, the event
# is done when the flow is done sending packets), event.processed will be set to True
def all_events_processed(sim_env):
    return sim_env.peek() == simpy.core.Infinity








# #####################################################
# TODO delete before presentation
# can read this if wanna know what i'm doing with the all_events_processed funcion
# def print_bogus(bogus, env):
#     for i in range(100):
#         print(bogus)
#         yield env.timeout(10)

# def end_when_other(bogus, env, p_to_end):
#     while True:
#         print(bogus)
#         yield env.timeout(10)
#         if p_to_end.processed == True:
#             print(str(p_to_end) + 'has finished  procesing!')
#             break
