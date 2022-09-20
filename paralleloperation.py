import random, time, math
import numpy as np
import matplotlib.pyplot as plt
import linfunc


def cap(x, most):
    if x > most:
        return most
    return x


class FailureFunction:
    def __init__(self, choose = "Weibull", params = None):
        """
        This is the standin for the model that you sample for the failure times.
        The only function the actual model object needs for this code to work is 
        .sample(), which returns a sample from the models distribution.
        
        Inputs
        ------
        choose : string
            The distribution you want to use, choose from:
                Weibill, 
                
        params : list<float>
            choose       | params
            ----------------------------
            Weibull      | (beta, eta)
            
        """
        
        if params is None:
            if choose == "Weibull":
                params = (2,10)
                
        if choose == "Weibull":
            self.sample_func = lambda : ((-1*math.log(1-random.random()))**(1/params[0]))*params[1] 

    def sample(self):
        return self.sample_func()
    
    
class FailureCount:
    def __init__(self, choose = "Set", params = None):
        """
        This is the class that is a standin for the number of failures the component is expected to have
        over a given period of time. The only thing the actual class must have is the sample function.
        
        """
        if params is None:
            if choose == "Set":
                params = 1
        
        if choose == "Set":
            self.sample_func = lambda : params
        
        
    def sample(self):
        return self.sample_func()
    
    
class FailSegment:
    def __init__(self, start, end, value):
        """
        This class just represents 1D segments which have a value. it supports a couple of operations 
        between segments.
        
        Parameters
        ----------
        start : float
            the starting value, must be less than the end value
        end : float
            the end value.
        value : float
            the value of this segment
        
        """
        self.start = start
        self.end = end
        self.value = value
    
    def __le__(self, other):
        return self.start <= other.start
    
    def __lt__(self, other):
        return self.start < other.start
    
    def __str__(self):
        return "(" + str(self.start) + ", " + str(self.end) + ", " + str(self.value) + ")"
    
    def collide(self, other):
        """
        checks if two segments overlap.
        """
        return max(self.start, other.start) < min(self.end, other.end)
    
    def compose(self, other):
        """
        If segments were funcions, this is just adding together the functions.
        so like {f(x)=1, 0<x<2} + {f(x)=1, 1<x<3} = {f(x)=1, 0<x<1} + {f(x)=2, 1<x<2} + {f(x)=1, 2<x<3}

        Parameters
        ----------
        other : FailSegment
            The other fail segment you wish to compose this one with.

        Returns
        -------
        tuple<FailSegment>
            the failsegments in reverse order, after a compose

        """
        values = [0,self.value + other.value,0]
        
        if self.start < other.start:
            values[0] = self.value
        if self.start > other.start:
            values[0] = other.value
            
        if self.end < other.end:
            values[2] = other.value
        if self.end > other.end:
            values[2] = self.value
        
        return (FailSegment(min(self.end, other.end), max(self.end, other.end), values[2]),
                FailSegment(max(self.start, other.start), min(self.end, other.end), values[1]),
                FailSegment(min(self.start, other.start), max(self.start, other.start), values[0]))
                
    
    def merge(self, other):
        return FailSegment(min(self.start, other.start), max(self.end, other.end), self.value)
    
    
class SegmentGraph:
    def __init__(self):
        """
        This function just optimises composing lots of segments, assuming the value of each segment is 1.
        """
        self.vals = []
        self.buff = []
        self.integral = 0
        
    def buffer(self, values):
        self.buff += values
        
    def add(self, value):
        self.buff.append(value)
        
    def update(self):
        if len(self.buff) == 0:
            return
        self.vals = [0, ] * len(self.buff)*2
        firsts = list(np.sort([x.start for x in self.buff]))
        seconds = list(np.sort([x.end for x in self.buff]))
        vals_index = 0
        firsts_index = 0
        seconds_index = 0
        count = 0
        self.integral = 0
        start = firsts[0]
        """
        Basically how this algorithm works, is it keeps track of 2 lists, a list of the first x_position of the 
        segments, and the list of the second value of the second x_position of the segments.
        it the remembers what x value it is up to, and check to see if the next closest value is a first or a second
        if its a first, this means you increase the count, if its a second you decrease.
        
        """
        while firsts_index < len(firsts):
            
            if vals_index == len(self.vals):
                self.vals += [0,] * len(self.vals)
                
            if firsts[firsts_index] < seconds[seconds_index]: #If the first part of a segment comes first
                count += 1
                self.vals[vals_index] = (firsts[firsts_index], count)
                firsts_index += 1
                self.integral += (self.vals[vals_index][0]-start)*self.vals[vals_index][1] #This line starts summing the integral
                start = self.vals[vals_index][0]
                vals_index += 1
            elif firsts[firsts_index] > seconds[seconds_index]: #If the second part of a segment comes first
                count -= 1
                self.vals[vals_index] = (seconds[seconds_index], count)
                seconds_index += 1
                self.integral += (self.vals[vals_index][0]-start)*self.vals[vals_index][1]
                start = self.vals[vals_index][0]
                vals_index += 1
            elif firsts[firsts_index] == seconds[seconds_index]: #If they come at the same time.
                seconds_index += 1
                firsts_index += 1
            
        
        while seconds_index < len(seconds): # if we have ran out of firsts, there are only seconds left.
            
            if vals_index == len(self.vals):
                self.vals += [0,] * len(self.vals)
            
            count -= 1
            self.vals[vals_index] = (seconds[seconds_index], count)
            seconds_index += 1
            
            vals_index += 1
            
        if 0 in self.vals: #remove the zeros from the list
            self.vals = self.vals[:self.vals.index(0)]
            
            
class ParallelOperation:
    def __init__(self, n_comps, comp_contribution, comp_functions = None, 
                 comp_failcounts = None, ttf = 1):
        """
        This class represents a set of n components in parallel. 
        The parameters you have to work with are
        .the ttf, assumed to be the same for all components
        .the distribution used to sample the fail times of each component, assumed to be the same for all comps
        .the parameters for each distribution, can be different for different components
        .the function that determines how many times a component will fail in its lifetime
        .the parameters for that function, different for each compoenent
        
        Assumptions
        .the probability that a compoenent will fail is not dependent on if it has failed before, or if other compoenets
            have failed before
        .iof of no components failing is 0

        Parameters
        ----------
        n_comps : int
            The number of components
        comp_contribution : float
            The contribution each component outputs
        comp_functions : FailureFunction, optional
            The functions used to determine when each component fails.
        comp_failcounts : FailureCount, optional
            The functions you want to use to sample the number of times a peice of equiptment fails.
        ttf : float, optional
            the amount of time it takes to repair a peice of equiptment. 

        Returns
        -------
        None.

        """
        self.n_comps = n_comps
        self.comp_contribution = comp_contribution

        if comp_functions == None:
            self.comp_functions = [FailureFunction("Weibull"), ] * n_comps
        else:
            self.comp_functions = comp_functions
        if comp_failcounts == None:        
            self.comp_failcount = [FailureCount("Set")] * n_comps
        else:
            self.comp_failcount = comp_failcounts

        self.ttf = ttf
        
        self.data = [SegmentGraph() for x in range(n_comps)] #self.data[0] if you fit linear segments to the data points, it will
                                                 #             tell you the number of times only 1 failure was occuing
                                                 #self.data[1] will be 2 failures, ect...
                                                 
        self.sorted = False
        self.arranged_data = [] #the y values of all the aligned x_values
        
    def simulate(self, n = 10000, timeit = False): #probs make quicker
        self.sorted = False
    
        if timeit:
            T1 = time.time()
        
        for i in range(n):
            fail_segments = []
            for comp_index in range(self.n_comps): #for each component
                fail_count = self.comp_failcount[comp_index].sample() #sample how many failures
                nxt = [0,] * fail_count
                for r in range(fail_count):
                    start = self.comp_functions[comp_index].sample() #sample when the failure occurs
                    nxt[r] = FailSegment(start, start + self.ttf, 1) #record the range it occurs at using the ttf
               
                nxt.sort()
                
                index = 0
                while index < len(nxt)-1: #merge segments, if failures occur while you are fixing
                    if nxt[index].collide(nxt[index+1]):
                        merged = nxt[index].merge(nxt[index+1])
                        del nxt[index]
                        del nxt[index]
                        nxt.insert(index, merged)
                    else:
                        index += 1
                fail_segments = fail_segments + nxt
            
            fail_segments.sort()

            #start summing up the segments, and count when n many failures occur.
            index = 0
            while index < len(fail_segments)-1:
                if fail_segments[index].collide(fail_segments[index+1]):
                    add_values = fail_segments[index].compose(fail_segments[index+1])
                    del fail_segments[index]
                    del fail_segments[index]
                    for add in add_values:
                        if add.value != 0:
                            fail_segments.append(add)
                    fail_segments.sort()
                else:
                    index += 1
                  
                
            for segment in fail_segments:
                self.data[segment.value-1].add(segment)
            
        for dat in self.data:
            dat.update()
            
        if timeit:
            print(n, " Iterations in ", time.time() - T1, " seconds.")
        
    def iof(self, n = 1):
        return max(0, 1-(self.n_comps-n)*self.comp_contribution)
    
    def summarise(self):
        
        plt.title("Probability of n-failures")
        plt.xlabel("Time")
        plt.ylabel("Probability of exactly n failues")
        intg = sum([self.data[n].integral for n in range(self.n_comps)])
        for n in range(self.n_comps):
            disp = self.data[n].vals
            plt.plot([x[0] for x in disp], [(x[1])/intg for x in disp], label = str(n+1) + " failures")
        plt.legend()
        plt.show()
        plt.figure()
        
        
        most = max([max([0,] + [y[0] for y in x.vals]) for x in self.data])
        least = min([min([most, ]+[y[0] for y in x.vals]) for x in self.data])
        
        RESOLUTION = 1000
        
        if not self.sorted:
            self.sorted = True
            for x in self.data:
                x.vals.insert(0,(least,0))
                x.vals.append((most,0))
            
            self.arranged_data = []
            for comp in range(self.n_comps):
                self.arranged_data.append(linfunc.linsample([x[0] for x in self.data[comp].vals], [(x[1]*(comp+1))/intg for x in self.data[comp].vals], (least, most, RESOLUTION)))
        
        
        plt.title("Expected impact")
        plt.xlabel("Time")
        plt.ylabel("Efficiency")
        
        x_vals = list(np.arange(least, most, (most-least)/RESOLUTION))
        while len(x_vals) > RESOLUTION:
            x_vals.pop()
        y_vals = [1, ] * RESOLUTION
        for x in range(RESOLUTION):
            for comp in range(self.n_comps):
                y_vals[x] -= self.arranged_data[comp][x]*self.iof(comp+1)
                
        plt.plot(x_vals, y_vals)
        plt.show()
        plt.figure()
        
    
        
        
if __name__ == "__main__":
    #print("Test1, 4 components, 10000 iterations, ttf = 6, no.failures is set at 2, failure distribution is weibull(2,10)")
    #Test1 = ParallelOperation(4,1/4, ttf = 6)
    #Test1.simulate(timeit = True)
    #Test1.summarise()
    
    print("Test2, 4 components, 10000 iterations, ttf = 6, no.failures is set to 1, failure distribution is weibull")
    print("the parameters for the weibull dists are: (10,10),(10,20),(5,5),(4,5)")
    Test2 = ParallelOperation(4,1/4,comp_functions = (FailureFunction(params = (10,10)),
                                                      FailureFunction(params = (20,10)),
                                                      FailureFunction(params = (5,5)),
                                                      FailureFunction(params = (4,5))),
                                    comp_failcounts = (FailureCount(params = 2),
                                                       FailureCount(params = 2),
                                                       FailureCount(params = 2),
                                                       FailureCount(params = 2)),
                                    ttf = 6)
    Test2.simulate(timeit = True)
    Test2.summarise()
        
        