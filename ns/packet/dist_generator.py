"""
Implements a packet generator that simulates the sending of packets with a specified inter-
arrival time distribution and a packet size distribution. One can set an initial delay and
a finish time for packet generation. In addition, one can set the source id and flow ids for
the packets generated. The DistPacketGenerator's `out` member variable is used to connect the
generator to any network element with a `put()` member function.
"""
from ns.packet.packet import Packet
import csv # to read from a csv file and load data into packets

class DistPacketGenerator:
    """ Generates packets with a given inter-arrival time distribution.

        Parameters
        ----------
        env: simpy.Environment
            The simulation environment.
        element_id: str
            the ID of this element.
        arrival_dist: function
            A no-parameter function that returns the successive inter-arrival times of
            the packets.
        size_dist: function
            A no-parameter function that returns the successive sizes of the packets.
        initial_delay: number
            Starts generation after an initial delay. Defaults to 0.
        finish: number
            Stops generation at the finish time. Defaults to infinite.
        rec_flow: bool
            Are we recording the statistics of packets generated?
    """
    def __init__(self,
                 env,
                 element_id,
                 arrival_dist,
                 size_dist,
                 initial_delay=0,
                 finish=float("inf"),
                 flow_id=0,
                 rec_flow=False,
                 debug=False):
        self.element_id = element_id
        self.env = env
        self.arrival_dist = arrival_dist
        self.size_dist = size_dist
        self.initial_delay = initial_delay
        self.finish = finish
        self.out = None
        self.packets_sent = 0
        self.action = env.process(self.run())
        self.flow_id = flow_id

        self.rec_flow = rec_flow
        self.time_rec = []
        self.size_rec = []
        self.debug = debug

    def run(self):
        """The generator function used in simulations."""
        print("initial delay in dis generator: ",self.initial_delay)
        # the generator function pause for the specified initial_delay duration before continuing execution
        yield self.env.timeout(self.initial_delay)
        with open(r'C:\Users\reyha\Desktop\network-simulation\Network-Simulation-with-Python\data\data.csv', 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip the first line (header)
        # keeps the generator function running as long as the current simulation time
        # while self.env.now < self.finish:
            # wait for next transmission
            for row in csv_reader:
                yield self.env.timeout(self.arrival_dist())
                print("before packet sent delay in dis generator: ",self.arrival_dist)
                self.packets_sent += 1
                payload = row  # Example payload
                packet = Packet(self.env.now,
                                self.size_dist(),
                                self.packets_sent,
                                src=self.element_id,
                                flow_id=self.flow_id,
                                payload = payload)
                if self.rec_flow:
                    self.time_rec.append(packet.time)
                    self.size_rec.append(packet.size)

                # Assign row (list) as payload
                packet.payload = row  

                print(
                        f"*Sent packet {packet.packet_id} with flow_id {packet.flow_id} at "
                        f"time {self.env.now}. Payload: {packet.payload} from pg")
                
                if self.debug:
                    print(
                        f"Sent packet {packet.packet_id} with flow_id {packet.flow_id} at "
                        f"time {self.env.now}.")

                self.out.put(packet)
