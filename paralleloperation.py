import random, time, math
import numpy as np
import matplotlib.pyplot as plt
import linfunc
from scipy.stats import truncnorm


def cap(x, most):
    if x > most:
        return most
    return x


def get_truncated_normal(mean, sd, low, upp): #This is rediculously slow. fix it.
    """
    yoinked from:
    https://stackoverflow.com/questions/36894191/how-to-get-a-normal-distribution-within-a-range-in-numpy
    """
    return truncnorm(
        (low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)


class FailureFunction:
    def __init__(self, choose = "Weibull", params = None):
        """
        
        Inputs
        ------
        choose : string
            The distribution you want to use, choose from:
                Weibill, Normal
                
        params : list<float>
            choose       | params
            ----------------------------
            Weibull      | (beta, eta)
            Normal       | (mean, std, upper = 10000)
            
        """
        
        if params is None:
            if choose == "Weibull":
                params = (2,10)
            if choose == "Normal":
                params = (10,2)
                
        if choose == "Weibull":
            self.sample_func = lambda : ((-1*math.log(1-random.random()))**(1/params[0]))*params[1] 
        if choose == "Normal":
            if(len(params)) == 2:
                upper = 10000
            else:
                upper = params[2]
            self.sample_func = lambda : get_truncated_normal(params[0], params[1], 0, upper).rvs()
        
    def sample(self):
        return self.sample_func()
    
    
class FailureCount:
    def __init__(self, choose = "Set", params = None):
        if params is None:
            if choose == "Set":
                params = 1
        
        if choose == "Set":
            self.sample_func = lambda : params
        
        
    def sample(self):
        return self.sample_func()
    
    
class FailSegment:
    def __init__(self, start, end, value):
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
        return max(self.start, other.start) < min(self.end, other.end)
    
    def compose(self, other):
        """
        

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
        while firsts_index < len(firsts):
            
            if vals_index == len(self.vals):
                self.vals += [0,] * len(self.vals)
                
            if firsts[firsts_index] < seconds[seconds_index]:
                count += 1
                self.vals[vals_index] = (firsts[firsts_index], count)
                firsts_index += 1
                self.integral += (self.vals[vals_index][0]-start)*self.vals[vals_index][1]
                start = self.vals[vals_index][0]
                vals_index += 1
            elif firsts[firsts_index] > seconds[seconds_index]:
                count -= 1
                self.vals[vals_index] = (seconds[seconds_index], count)
                seconds_index += 1
                self.integral += (self.vals[vals_index][0]-start)*self.vals[vals_index][1]
                start = self.vals[vals_index][0]
                vals_index += 1
            elif firsts[firsts_index] == seconds[seconds_index]:
                seconds_index += 1
                firsts_index += 1
            
        
        while seconds_index < len(seconds):
            
            if vals_index == len(self.vals):
                self.vals += [0,] * len(self.vals)
            
            count -= 1
            self.vals[vals_index] = (seconds[seconds_index], count)
            seconds_index += 1
            
            vals_index += 1
            
        if 0 in self.vals:
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
            self.comp_failcount = comp_failcounts()

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
            for comp_index in range(self.n_comps):
                fail_count = self.comp_failcount[comp_index].sample()
                nxt = [0,] * fail_count
                for r in range(fail_count):
                    start = self.comp_functions[comp_index].sample()
                    nxt[r] = FailSegment(start, start + self.ttf, 1)
               
                nxt.sort()
                
                index = 0
                while index < len(nxt)-1:
                    if nxt[index].collide(nxt[index+1]):
                        merged = nxt[index].merge(nxt[index+1])
                        del nxt[index]
                        del nxt[index]
                        nxt.insert(index, merged)
                    else:
                        index += 1
                fail_segments = fail_segments + nxt
            
            fail_segments.sort()

            
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
            plt.plot([x[0] for x in disp], [x[1]/intg for x in disp], label = str(n+1) + " failures")
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
                self.arranged_data.append(linfunc.linsample([x[0] for x in self.data[comp].vals], [x[1]/intg for x in self.data[comp].vals], (least, most, RESOLUTION)))
        
        
        plt.title("Expected efficiency")
        plt.xlabel("Time")
        plt.ylabel("Efficiency")
        
        x_vals = list(np.arange(least, most, (most-least)/RESOLUTION))
        while len(x_vals) > 1000:
            x_vals.pop()
        y_vals = [1, ] * RESOLUTION
        for x in range(RESOLUTION):
            for comp in range(self.n_comps):
                y_vals[x] -= self.arranged_data[comp][x]*self.iof(comp+1)
                
        plt.plot(x_vals, y_vals)
        plt.show()
        plt.figure()
        
        
if __name__ == "__main__":
    print("Test1, 4 components, 10000 iterations, ttf = 6, no.failures is set at 2, failure distribution is weibull(2,10)")
    Test1 = ParallelOperation(4,1/4, ttf = 6)
    Test1.simulate(timeit = True)
    Test1.summarise()
    
    print("Test2, 4 components, 10000 iterations, ttf = 6, no.failures is set to 1, failure distribution is weibull")
    print("the parameters for the weibull dists are: (10,10),(10,20),(5,5),(4,5)")
    Test2 = ParallelOperation(4,1/4,comp_functions = (FailureFunction(params = (10,10)),
                                                      FailureFunction(params = (10,20)),
                                                      FailureFunction(params = (5,5)),
                                                      FailureFunction(params = (4,5))), ttf = 6)
    Test2.simulate(timeit = True)
    Test2.summarise()
        
        
        
        
        
        
        
        
        
        