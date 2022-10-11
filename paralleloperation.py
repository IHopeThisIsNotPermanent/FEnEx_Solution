from ReliabilityFunctions import *
from linfunc import *


import random, time, math
import numpy as np
import matplotlib.pyplot as plt            
            
class ParallelOperation:
    def __init__(self, n_comps, comp_contribution, comp_functions = None, 
                 comp_failcounts = None, ttr = 1):
        """
        This class represents a set of n components in parallel. 
        The parameters you have to work with are
        .the ttr, assumed to be the same for all components
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
        ttr : float, optional
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

        self.ttr = ttr
        
        self.data = [SegmentGraph() for x in range(n_comps)] #self.data[0] if you fit linear segments to the data points, it will
                                                 #             tell you the number of times only 1 failure was occuing
                                                 #self.data[1] will be 2 failures, ect...
                                                 
        self.sorted = False
        self.arranged_data = [] #the y values of all the aligned x_values
        self.iteration_count = 0;
        
    def simulate(self, n = 10000, timeit = False): #probs make quicker
        self.iteration_count += n
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
                    nxt[r] = FailSegment(start, start + self.ttr, 1) #record the range it occurs at using the ttr
               
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
        
        most = max([max([0,] + [y[0] for y in x.vals]) for x in self.data])
        least = min([min([most, ]+[y[0] for y in x.vals]) for x in self.data])
        
        plt.title("Probability of n-failures")
        plt.xlabel("Time")
        plt.ylabel("Probability of exactly n failues")
        intg = sum([self.data[n].integral for n in range(self.n_comps)]) #sum the failures
        intg = self.iteration_count
        for n in range(self.n_comps):
            disp = self.data[n].vals
            plt.plot([x[0] for x in disp], [(x[1])/intg for x in disp], label = str(n+1) + " failures")
        plt.legend()
        plt.show()
        plt.figure()
        
        RESOLUTION = 1000
        
        if not self.sorted:
            self.sorted = True
            for x in self.data:
                x.vals.insert(0,(least,0))
                x.vals.append((most,0))
            
            self.arranged_data = []
            for comp in range(self.n_comps):
                self.arranged_data.append(linfunc.linsample([x[0] for x in self.data[comp].vals], [x[1]/intg for x in self.data[comp].vals], (least, most, RESOLUTION)))
        
        
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
    #print("Test1, 4 components, 10000 iterations, ttr = 6, no.failures is set at 2, failure distribution is weibull(2,10)")
    #Test1 = ParallelOperation(4,1/4, ttr = 6)
    #Test1.simulate(timeit = True)
    #Test1.summarise()

    print("Test2, 4 components, 10000 iterations, ttr = 6, no.failures is set to 1, failure distribution is weibull")
    print("the parameters for the weibull dists are: (10,10),(10,20),(5,5),(4,5)")
    Test2 = ParallelOperation(4,1/4,comp_functions = (FailureFunction(params = (10,10)),
                                                      FailureFunction(params = (20,10)),
                                                      FailureFunction(params = (5,5)),
                                                      FailureFunction(params = (4,5))),
                                    comp_failcounts = (FailureCount(params = 1),
                                                       FailureCount(params = 1),
                                                       FailureCount(params = 1),
                                                       FailureCount(params = 1)),
                                    ttr = 6)
    Test2.simulate(timeit = True)
    Test2.summarise()
    
    

        