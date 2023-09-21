"""
Implements a network medium with collision detection and channel errors
"""
import numpy # to create loss periods
import simpy

class Wire:
    """ Implements a network medium that introduces a propagation delay.
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
        mean_b, mean_g = 10, 50     # Mean values for exponential distributions, duration of bad and good periods
        self.loss_period_generator = LossPeriodGenerator(seed_b, seed_g, mean_b, mean_g)

    def run(self):
        print("initial delay in wire: ",0)
        yield self.env.timeout(0) 
        print("Enters wire at: ",self.env.now) # check propagation delay

        while True:
            packet = yield self.store.get()
            colliding_packets = [] # reset
            print("poped packet from store:", packet)
           
            if len(self.store.items) >= 1:
                print("now current_time checking store for collision: ",self.env.now)
                # Check for collisions using time packet entered wire
                colliding_packets = [p for p in self.store.items if p.current_time == packet.current_time]
                for colliding_packet in colliding_packets:
                    print("Colliding Packet ID found: {}, Flow ID: {}, entered wire time: {:.3f}".format(colliding_packet.packet_id,
                                                                                colliding_packet.flow_id,
                                                                                colliding_packet.current_time))
                    print("with popped packet ID: {}, Flow ID: {}, entered wire time: {:.3f}".format(packet.packet_id,
                                                                                packet.flow_id,
                                                                                packet.current_time))
                if len(colliding_packets) != 0:
                    # Collision detected
                    print("COLLISION: Multiple transmission detected in wire!")
                    self.packets_dropped += 2 # Two packets dropped with the same timestamp
                    collided =  self.store.get()
                    print("second packet removed from store:", collided)
                    print("Number of items in store after collision:", len(self.store.items))
                    
            if len(colliding_packets) == 0: # if no collision, check for good or bad period
                # Yield for slot duration now that we know there is no collision
                transmission_time = 1.5
                print("No collision for {} yield for transmission time of 1.5".format(packet))
                yield self.env.timeout(transmission_time)
                print("packet entered wire time is: ", packet.current_time)
                # loss_dist can be removed
                if self.loss_dist is None or not self.loss_period_generator.is_good_period(packet.current_time, packet.begin_transmission):
                    # Packet is dropped during bad periods
                    self.packets_dropped += 1
                    print("Dropped in bad perid! on wire #{} at {:.3f}: {}".format(
                            self.wire_id, self.env.now, packet))
                else: # good period
                    print("Not dropped in good period!")
                    # Packet is not dropped during good periods
                    queued_time = self.env.now - packet.current_time
                    delay = self.delay_dist()

                    # If queued time for this packet is greater than its propagation delay,
                    # it implies that the previous packet had experienced a longer delay.
                    # Since out-of-order delivery is not supported in simulation, deliver
                    # to the next component immediately.
                    if queued_time < delay:
                        yield self.env.timeout(delay - queued_time)
                    # in case of no collision and good period, pass the packet         
                    self.out.put(packet)
                    print("Left wire at {}: {}".format(self.env.now, packet))

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
        while timestamp >= self.good_high:
            # print(f"timestamp of packet {timestamp} is greater than good high:  {self.good_high}")
            self.good_low = self.good_high + self.rng_b.exponential(self.mean_b)
            self.good_high = self.good_low + self.rng_g.exponential(self.mean_g)
            # print(f"New low: {self.good_low} and new high: {self.good_high}")
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

    