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

        self.packets_dropped = 0

        self.debug = debug
        self.action = env.process(self.run())
        # Loss period generator configuration
        seed_b, seed_g = 1234, 4321  # Seeds for random number generators
        mean_b, mean_g = 50, 50      # Mean values for exponential distributions
        self.loss_period_generator = LossPeriodGenerator(seed_b, seed_g, mean_b, mean_g)


    def run(self):
        """The generator function used in simulations."""
        print("Propagation delay is: ",self.delay_dist()) # check propagation delay
        while True:
            packet = yield self.store.get()

            if self.loss_dist is None or random.uniform(
                    0, 1) >= self.loss_dist(packet_id=packet.packet_id):
                # The amount of time for this packet to stay in my store
                queued_time = self.env.now - packet.current_time
                print("queued_time",queued_time)
                delay = self.delay_dist()

                # If queued time for this packet is greater than its propagation delay,
                # it implies that the previous packet had experienced a longer delay.
                # Since out-of-order delivery is not supported in simulation, deliver
                # to the next component immediately.
                if queued_time < delay:
                    yield self.env.timeout(delay - queued_time)

                self.out.put(packet)

                if self.debug:
                    print("Left wire #{} at {:.3f}: {}".format(
                        self.wire_id, self.env.now, packet))
            else:
                self.packets_dropped += 1
                if self.debug:
                    print("Dropped! on wire #{} at {:.3f}: {}".format(
                        self.wire_id, self.env.now, packet))
            # ADDED: calculate the loss rate
            if self.packets_rec > 0:
                loss_rate = (self.packets_dropped / self.packets_rec) * 100
            else:
                loss_rate = 0

            print("Packet Loss Rate for Wire #{}: {:.2f}%. {} packets in total and {} packets lost".format(self.wire_id, loss_rate, self.packets_rec, self.packets_dropped))

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
        self.good_low = 0
        self.good_high = self.good_low + self.rng_g.exponential(self.mean_g) # Upper bound of the current good period

    def is_good_period(self, timestamp):
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

        if timestamp > self.good_high:
            self.good_low = self.good_high + self.rng_b.exponential(self.mean_b)
            self.good_high = self.good_low + self.rng_g.exponential(self.mean_g)
            return False
        return True
