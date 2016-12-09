from device import Router
from device import Host
import simpy
import matplotlib.pyplot as plt

def flow(data, start, source, destination, sim_env, tcp_type, gamma=0.5, alpha=15):
    yield sim_env.timeout(start)
    source.start_flow(data=data, destination=destination, env=sim_env, tcp_type=tcp_type, gamma=gamma, alpha=alpha)

def dynamic_routing(devices, interval, sim_env):
    while True:
        for device in devices:
            if isinstance(device, Router):
                device.send_router(sim_env)
        yield sim_env.timeout(interval)

        if all_events_processed(sim_env):
            print('All flows are dead. Simulation is over. Stop running routing algorithm. ')
            break

# Events is a list of simpy 'Events.' When the event is done (for example, if the event is a flow, the event
# is done when the flow is done sending packets), event.processed will be set to True
def all_events_processed(sim_env):
    return sim_env.peek() == simpy.core.Infinity

def graph_live(devices, links, hosts_to_graph, links_to_graph, env):
    fig = plt.figure(figsize=(20, 10))
    fig.set_tight_layout(True)
    plt.ion()

    axes = {}
    axes["wsize"] = fig.add_subplot(6,1,1)
    axes["wsize"].set_ylabel('Window Size\n (Packets)')
    axes["flowrate"] = fig.add_subplot(6,1,2)
    axes["flowrate"].set_ylabel('Flow Rate\n (Mbps)')
    axes["buffocc"] = fig.add_subplot(6,1,6)
    axes["buffocc"].set_ylabel('Buffer Occupancy\n (Bytes)')
    axes["delay"] = fig.add_subplot(6,1,3)
    axes["delay"].set_ylabel('Packet Delay\n (ms)')
    axes["linkrate"] = fig.add_subplot(6,1,4)
    axes["linkrate"].set_ylabel('Link Rate\n (Mbps)')
    axes["dropped"] = fig.add_subplot(6,1,5)
    axes["dropped"].set_ylabel('Packets Dropped\n (Packets)')


    colors = ["blue", "red", "green", "black", "brown", "orange", "purple"]

    while True:
        yield env.timeout(1000)
        wsize_legend = []
        flowrate_legend = []
        for device in devices:
            if device.ip not in hosts_to_graph:
                continue
            if isinstance(device, Host):
                for destination in device.graph_wsize:
                    curr_wsize_graph = device.graph_wsize[destination]
                    axes["wsize"].plot(curr_wsize_graph.times, curr_wsize_graph.vals, color=colors[device.ip])
                    wsize_legend.append(curr_wsize_graph.title)
                for source in device.graph_flowrate:
                    curr_flowrate_graph = device.graph_flowrate[source]
                    axes["flowrate"].plot(curr_flowrate_graph.times, curr_flowrate_graph.vals, color=colors[device.ip])
                    flowrate_legend.append(curr_flowrate_graph.title)

        axes["wsize"].legend(wsize_legend)
        axes["flowrate"].legend(flowrate_legend)

        buffocc_legend = []
        delay_legend = []
        dropped_legend = []
        linkrate_legend = []
        for link in links:
            if link.id not in links_to_graph:
                continue
            curr_graph = link.graph_buffocc
            axes["buffocc"].plot(curr_graph.times, curr_graph.vals, color=colors[link.id])
            buffocc_legend.append(curr_graph.title)

            curr_graph = link.graph_delay
            axes["delay"].plot(curr_graph.times, curr_graph.vals, color=colors[link.id])
            delay_legend.append(curr_graph.title)

            curr_graph = link.graph_linkrate
            axes["linkrate"].plot(curr_graph.times, curr_graph.vals, color=colors[link.id])
            linkrate_legend.append(curr_graph.title)

            curr_graph = link.graph_dropped
            axes["dropped"].plot(curr_graph.times, curr_graph.vals, color=colors[link.id])
            dropped_legend.append(curr_graph.title)

        axes["buffocc"].legend(buffocc_legend)
        axes["delay"].legend(delay_legend)
        axes["linkrate"].legend(linkrate_legend)
        axes["dropped"].legend(dropped_legend)

        plt.draw()
        plt.pause(0.01)
