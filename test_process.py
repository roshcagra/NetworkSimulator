import simpy
from device import Host
from device import Router
from link import Link
from utils import print_bogus
from utils import end_when_other
env = simpy.Environment()

p1 = env.process(print_bogus('hi', env))
p2 = env.process(end_when_other('bye', env, p1))

print(p1.processed)

env.run()