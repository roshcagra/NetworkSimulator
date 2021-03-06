from device import Router
from device import Host
import simpy


def flow(data, start, source, destination, sim_env, tcp_type, gamma=0.5, alpha=15):
    yield sim_env.timeout(0)
    sim_env.process(source.start_flow(start=start, data=data, destination=destination, env=sim_env, tcp_type=tcp_type, gamma=gamma, alpha=alpha))

def dynamic_routing(devices, interval, sim_env):
    while True:
        for device in devices:
            if isinstance(device, Router):
                device.send_router(sim_env)
        yield sim_env.timeout(interval)

        if all_events_processed(devices, sim_env):
            print('All flows are dead. Simulation is over. Stop running routing algorithm. ')
            break

# Events is a list of simpy 'Events.' When the event is done (for example, if the event is a flow, the event
# is done when the flow is done sending packets), event.processed will be set to True
def all_events_processed(devices, sim_env):
    for device in devices:
        if isinstance(device, Host):
            if device.num_flows != 0:
                return False
    return True

    # return sim_env.peek() == simpy.core.Infinity

def graph_live(devices, links, env, hosts_to_graph='all', links_to_graph='all'):
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(20, 10))
    fig.set_tight_layout(True)
    plt.ion()

    axes = {}
    axes["wsize"] = fig.add_subplot(6,1,5)
    axes["wsize"].set_ylabel('Window Size\n (Packets)')
    axes["flowrate"] = fig.add_subplot(6,1,4)
    axes["flowrate"].set_ylabel('Flow Rate\n (Mbps)')
    axes["buffocc"] = fig.add_subplot(6,1,2)
    axes["buffocc"].set_ylabel('Buffer Occupancy\n (Bytes)')
    axes["delay"] = fig.add_subplot(6,1,6)
    axes["delay"].set_ylabel('Packet Delay\n (ms)')
    axes["linkrate"] = fig.add_subplot(6,1,1)
    axes["linkrate"].set_ylabel('Link Rate\n (Mbps)')
    axes["dropped"] = fig.add_subplot(6,1,3)
    axes["dropped"].set_ylabel('Packet Loss\n (Packets)')


    colors = ["blue", "red", "green", "black", "brown", "orange", "purple"]

    while True:
        if env.peek() == simpy.core.Infinity:
            print('GRAPHING DONE!')
            break
        yield env.timeout(1000)
        wsize_legend = []
        flowrate_legend = []
        delay_legend = []
        max_delay = 0
        for device in devices:
            if hosts_to_graph != 'all' and device.ip not in hosts_to_graph:
                continue
            if isinstance(device, Host):
                for destination in device.graph_wsize:
                    curr_wsize_graph = device.graph_wsize[destination]
                    axes["wsize"].plot(curr_wsize_graph.times, curr_wsize_graph.vals, color=colors[device.ip%len(colors)])
                    wsize_legend.append(curr_wsize_graph.title)
                for destination in device.graph_delay:
                    curr_delay_graph = device.graph_delay[destination]
                    axes["delay"].plot(curr_delay_graph.times, curr_delay_graph.vals, color=colors[device.ip%len(colors)])
                    if len(curr_delay_graph.vals) > 0:
                        max_delay = max(max_delay, max(curr_delay_graph.vals))
                    delay_legend.append(curr_delay_graph.title)
                for source in device.graph_flowrate:
                    curr_flowrate_graph = device.graph_flowrate[source]
                    axes["flowrate"].plot(curr_flowrate_graph.times, curr_flowrate_graph.vals, color=colors[device.ip%len(colors)])
                    flowrate_legend.append(curr_flowrate_graph.title)

        axes["wsize"].legend(wsize_legend)
        axes["flowrate"].legend(flowrate_legend)
        axes["delay"].legend(delay_legend)
        axes["delay"].set_ylim(0, max(max_delay, 1) + 5)

        buffocc_legend = []
        dropped_legend = []
        linkrate_legend = []
        for link in links:
            if links_to_graph != 'all' and link.id not in links_to_graph:
                continue
            curr_graph = link.graph_buffocc
            axes["buffocc"].plot(curr_graph.times, curr_graph.vals, color=colors[link.id%len(colors)])
            buffocc_legend.append(curr_graph.title)

            curr_graph = link.graph_linkrate
            axes["linkrate"].plot(curr_graph.times, curr_graph.vals, color=colors[link.id%len(colors)])
            linkrate_legend.append(curr_graph.title)

            curr_graph = link.graph_dropped
            axes["dropped"].plot(curr_graph.times, curr_graph.vals, color=colors[link.id%len(colors)])
            dropped_legend.append(curr_graph.title)

        axes["buffocc"].legend(buffocc_legend)
        axes["linkrate"].legend(linkrate_legend)
        axes["dropped"].legend(dropped_legend)

        plt.draw()
        plt.pause(0.01)

    plt.ioff()
    plt.show()
