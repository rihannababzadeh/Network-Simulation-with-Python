"""
Implements a network wire (cable) with a propagation delay. There is no need
to model a limited network capacity on this network cable, since such a
capacity limit can be modeled using an upstream port or server element in
the network.
"""
import random
import numpy # to create loss periods
import simpy


class Wire:
    """ Implements a network wire (cable) that introduces a propagation delay.
        Set the "out" member variable to the entity to receive the packet.

        Parameters
        ----------
        env: simpy.Environment
            the simulation environment.
        delay_dist: function
            a no-parameter function that returns the successive propagation
            delays on this wire.
        loss_dist: function
            a function that takes one optional parameter, which is the packet ID, and
            returns the loss rate.
    """

    def __init__(self,
                 env,
                 delay_dist,
                 loss_dist=None,
                 wire_id=0,
                 debug=False):
        self.store = simpy.Store(env)
        self.delay_dist = delay_dist
        self.loss_dist = loss_dist
        self.env = env
        self.wire_id = wire_id
        self.out = None
        self.packets_rec = 0
        self.begin_transmissions = {}  # Dictionary to store begin_transmission times
        
        self.packets_dropped = 0

        self.debug = debug
        self.action = env.process(self.run())
        # Loss period generator configuration
        seed_b, seed_g = 1234, 4321  # Seeds for random number generators
        mean_b, mean_g = 10, 50     # Mean values for exponential distributions, duration of bad and good periods
        self.loss_period_generator = LossPeriodGenerator(seed_b, seed_g, mean_b, mean_g)


    def run(self):
        """The generator function used in simulations."""
        print("propagation delay is: ",self.delay_dist()) # check propagation delay
        while True:
            packet = yield self.store.get()
            begin_transmission = packet.begin_transmission
            packet_id = packet.packet_id
    
            if begin_transmission in self.begin_transmissions: 
                # Collision
                print(f"collision at {begin_transmission}!")
                self.begin_transmissions[begin_transmission].append(packet_id) #  Append the current packet's ID to the list of packet IDs associated with it
                self.packets_dropped += 1
                print("Dropped! because of collision on wire #{} at {:.3f}: {}".format(
                        self.wire_id, self.env.now, packet))
            else:
                self.begin_transmissions[begin_transmission] = [packet_id]
           
            # printing the list
            # for begin_time, packet_ids in self.begin_transmissions.items():
            #     print(f"Begin Transmission Time: {begin_time}, Packet IDs: {packet_ids}")

            print("good period?", self.loss_period_generator.is_good_period(packet.current_time, packet.begin_transmission))
            print("current time is: ", packet.current_time)
            # loss_dist can be removed
            if self.loss_dist is None or not self.loss_period_generator.is_good_period(packet.current_time, packet.begin_transmission):
                # Packet is dropped during bad periods
                self.packets_dropped += 1
                print("Dropped! on wire #{} at {:.3f}: {}".format(
                        self.wire_id, self.env.now, packet))
            else:
                print("Not dropped in good period!")
                # Packet is not dropped during good periods
                queued_time = self.env.now - packet.current_time
                print("queued_time", queued_time)
                delay = self.delay_dist()

                if queued_time < delay:
                    yield self.env.timeout(delay - queued_time)

                self.out.put(packet)

                print("Left wire #{} at {:.3f}: {}".format(
                        self.wire_id, self.env.now, packet))

            # Calculate the loss rate and print statistics
            if self.packets_rec > 0:
                loss_rate = (self.packets_dropped / self.packets_rec) * 100
            else:
                loss_rate = 0
            
            print("Packet Loss Rate for Wire #{}: {:.2f}%. {} packets in total and {} packets lost".format(
                self.wire_id, loss_rate, self.packets_rec, self.packets_dropped))

    def put(self, packet):
        """ Sends a packet to this element. """
        self.packets_rec += 1
        if self.debug:
            print(f"Entered wire #{self.wire_id} at {self.env.now}: {packet} ")

        packet.current_time = self.env.now
        return self.store.put(packet)

# trying to create losses

class LossPeriodGenerator:
    """
        Initializes the LossPeriodGenerator.

        Parameters
        ----------
        seed_b : int
            Seed for the random number generator for bad periods.
        seed_g : int
            Seed for the random number generator for good periods.
        mean_b : float
            Mean value for the exponential distribution of bad periods.
        mean_g : float
            Mean value for the exponential distribution of good periods. 
    """
    def __init__(self, seed_b, seed_g, mean_b, mean_g):
        self.rng_b = numpy.random.RandomState(seed_b)
        self.rng_g = numpy.random.RandomState(seed_g)
        self.mean_b = mean_b
        self.mean_g = mean_g
        self.good_low = 0 # Starting from 0
        self.good_high = self.good_low + self.rng_g.exponential(self.mean_g) # Upper bound of the current good period

    def is_good_period(self, timestamp, begin_transmission):
        """
        Determines if the given timestamp falls within a good or bad period.

        Parameters
        ----------
        timestamp : float
            The timestamp of the packet being processed.

        Returns
        -------
        bool
            True if the timestamp is within a good period (no loss), False otherwise (bad period with bursty loss).
        """
        # If the timestamp is greater than the current good_high, it means the current period is a bad period
        # with bursty loss.

        
        # if self.good_low <= timestamp < self.good_high:
        #     print(f"timestamp of packet {timestamp} is between low: {self.good_low} and high : {self.good_high}")
        #     # If the timestamp is within the current good period interval, it's a good period.
        #     return True
        # else:
        #     # If the timestamp is outside the current good period interval, it's a bad period.
        #     # Calculate the start and end times for the next good period.
        #     print(f"timestamp of packet {timestamp} is outside the good interval: {self.good_low} and {self.good_high}")
        #     if(timestamp > self.good_high): # we need to know the next good period
        #         self.good_low = self.good_high + self.rng_b.exponential(self.mean_b) 
        #         self.good_high = self.good_low + self.rng_g.exponential(self.mean_g)
        #     return False

        while timestamp >= self.good_high:
            print(f"timestamp of packet {timestamp} is greater than good high:  {self.good_high}")
            self.good_low = self.good_high + self.rng_b.exponential(self.mean_b)
            self.good_high = self.good_low + self.rng_g.exponential(self.mean_g)
            print(f"New low: {self.good_low} and new high: {self.good_high}")
        if self.good_low <= timestamp < self.good_high:
            if begin_transmission < self.good_low or begin_transmission >= self.good_high:
                print(f"Timestamp {timestamp} is in a good period, but beginning of transmission {begin_transmission} is in a bad period.")
        else:
            print("Timestamp is in a bad period.")  
        if self.good_low <= begin_transmission < self.good_high:
            print("Beginning of transmission is in a good period.")
        else:
            print("Beginning of transmission is in a bad period.")      
        return self.good_low <= timestamp < self.good_high and self.good_low <= begin_transmission < self.good_high
    
"""example:
good low = 0
good high = 0 + 3 =3
timestamp = 0
0<=0 so we are in good period(returns true)
then,
timestamp = 4.5
4.5 > 3
so if statement is correct so
good low = 3+4 (bad) = 7
good high = 7 + 6 (good) = 11
and we return false and we should drop this packet
then:
timestamp: 6
6 not between 7 << 11
so bad perid and returns false
then:
timestamp: 7.5
so we are in good period(returns true)
then:
timestamp: 9
so we are in good period(returns true)
then:
timestamp: 10.5
so we are in good period(returns true)
then:
timestamp: 12
12>11 
returns False, bad period
good low = 11+4 (bad) = 15
good high = 15+6 (good) = 21
then:
timestamp: 13.5
returns false
    """

    