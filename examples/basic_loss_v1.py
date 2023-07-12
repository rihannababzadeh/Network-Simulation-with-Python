"""
A basic example that connects two packet generators to a network wire with
a propagation delay distribution, and then to a packet sink.
The loss is created based on good and bad periods created in the wire class
"""
from functools import partial
import random
from random import expovariate

import simpy
from ns.packet.dist_generator import DistPacketGenerator
from ns.packet.sink import PacketSink
from ns.port.wire import Wire
from ns.port.port import Port

def arrival_1():
    """ Packets arrive with a constant interval of 1.5 seconds. """
    return 1.5


def arrival_2():
    """ Packets arrive with a constant interval of 2.0 seconds. """
    return 2.0


def delay_dist():
    return 0.1


def packet_size():
    return int(expovariate(0.01))

# def loss_dist(packet_id):
#     """ a function that takes one optional parameter, which is the packet ID, and
#             returns the loss rate.
#         Args:
#             packet_id
#     """ 
#     return 0.1  

def loss_dist(packet_id):
    """A function that takes one optional parameter, which is the packet ID, and
    returns the loss rate. This modified version introduces bursty loss behavior.

    Args:
        packet_id: The ID of the packet.

    Returns:
        float: The loss rate for the packet.
    """
    return 0.01

# Return the loss rate (e.g., 0.2 for 20% packet loss)
# the drop will show in logs as: At time t, packet x from "flow_y" was dropped on wire #z.
rate = 10**6
#printing the content of each packet
print("start!")
env = simpy.Environment()
print("environment activated!")
port1 = Port(env, rate)
print(port1)
ps = PacketSink(env, rec_flow_ids=False, debug=True)
print("packet sink set!")

pg1 = DistPacketGenerator(env, "flow_1", arrival_1, packet_size, flow_id=0)
print("flow 1 packet generator set!")

# pg2 = DistPacketGenerator(env, "flow_2", arrival_2, packet_size, flow_id=1)
# print("flow 2 packet generator set!")

wire1 = Wire(env, partial(random.gauss, 0.1, 0.02), loss_dist=loss_dist, wire_id=1, debug=True)
print("wire 1 with loss set!")

# print("delay dist for wire2:", delay_dist())
# wire2 = Wire(env, delay_dist, wire_id=2, debug=True)
# print("wire 2 set!")

# pg1.out = wire1
# print("pg1 packets are sent to wire 1!")
pg1.out = port1
print("pg1 packets are sent to port 1!")
port1.out = wire1

# pg2.out = wire2
# print("pg2 packets are sent to wire 2!")

wire1.out = ps
print("output of wire 1 is sink!")

# wire2.out = ps
# print("output of wire 2 is sink!")

print("starts the simulation and runs it until the simulation time reaches or exceeds 100")
env.run(until=100)
print("Done with running the simulation")

print("Flow 1 packet delays: " +
      ", ".join(["{:.2f}".format(x) for x in ps.waits['flow_1']]))
print("Flow 2 packet delays: " +
      ", ".join(["{:.2f}".format(x) for x in ps.waits['flow_2']]))

print("Packet arrival times in flow 1: " +
      ", ".join(["{:.2f}".format(x) for x in ps.arrivals['flow_1']]))

print("Packet arrival times in flow 2: " +
      ", ".join(["{:.2f}".format(x) for x in ps.arrivals['flow_2']]))
