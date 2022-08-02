import random, time
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import truncnorm

def get_truncated_normal(mean=0, sd=1, low=0, upp=10):
    """
    yoinked from:
    https://stackoverflow.com/questions/36894191/how-to-get-a-normal-distribution-within-a-range-in-numpy
    """
    return truncnorm(
        (low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)

class NormalParallelOperation:    
    def __init__(self, components, pof_dists = None):
        """
        This class represents the blocks of components in parallel
        This one assumes that the PoV for each component is set, at each iteration.
        
        Inputs
        ------
        components : tuple
            format as (no.compoments, output as a decimal)
        pof_dists : tuple 
            format as (the decimal change of failure for each component)
        """
        
        self.components = components
        if pof_dists is None:
            self.pof_dists = (0.1,)*components[0]
        else:
            self.pof_dists = pof_dists
        self.data_points = [0,]*(components[0]+1) #the index is the number of failures
                                                  #the value is the number count
        
    def iof(self, n = 1):
        return max(0, 100-100*(self.components[0]-n)*self.components[1])
        
    def iof_display(self, n = None):
        if n is None:
            n = self.components[0]
        for i in range(n):
            print("IoF n-", str(i+1), " = ", str(int(self.iof(i+1))), "%")
            
    def sample_iof(self):
        """
        Does 1 round of the Monte-Carlo method

        Returns
        -------
        tuple
            output is of form (IoF, no. of failures)

        """
        failures = 0
        for i in self.pof_dists:
            failures += random.random() <= i
        return (self.iof(failures), failures)
    
    def leq(a, b):
        return a <= b
    
    def simulate(self, n = 10000):
        leq_vect = np.vectorize(NormalParallelOperation.leq)
        probs = [x*1000 for x in self.pof_dists]
        for x in [np.sum(leq_vect(np.random.randint(0 ,1000 ,size = self.components[0]), probs)) for i in range(n)]:
            self.data_points[x] += 1
            
    def sumarise(self):
        print("For the one where we dont sample the PoF every interation")
        plt.title("Probability of n-failures")
        plt.xlabel("no. failures")
        plt.ylabel("Probability as a percent")
        
        plt.bar(list(range(0,self.components[0]+1)), [100*x/sum(self.data_points) for x in self.data_points])
        plt.show()
        plt.figure()
        
        decimal_data = [x/sum(self.data_points) for x in self.data_points]
        
        print("After ", sum(self.data_points), " Monte-Carlo Iterations.")
        print("Probability of total failure = ", 100*decimal_data[len(decimal_data) - 1], "%")
        print("Expected efficiency = ", 100 - 100 * sum([self.iof(x+1)*0.01*decimal_data[x] for x in range(self.components[0]+1)]), "%")
        print("")

      
class NormalParallelOperation2:    
    def __init__(self, components, pof_dists = None):
        """
        This class represents the blocks of components in parallel
        This one assumes that the PoV is sampled from a normal distribution each iteration.
        
        Inputs
        ------
        components : tuple
            format as (no.compoments, output as a decimal)
        pof_dists : tuple 
            format as ((the mean decimal chance of failure for each component, sd), ...)
        """
        
        self.components = components
        if pof_dists is None:
            self.pof_dists = [(random.choice([0.1+0.01*x for x in range(11)]),0.01) for x in range(components[0])]
        else:
            self.pof_dists = pof_dists
        self.data_points = [0,]*(components[0]+1) #the index is the number of failures
                                                  #the value is the number count
        self.pof_dists = [get_truncated_normal(t[0], t[1], 0, 1) for t in self.pof_dists]
    
    def iof(self, n = 1):
        return max(0, 100-100*(self.components[0]-n)*self.components[1])
    
    def leq(a, b):
        return a <= b
    
    def simulate(self, n = 10000):
        leq_vect = np.vectorize(NormalParallelOperation.leq)
        for x in [np.sum(leq_vect(np.random.randint(0 ,1000 ,size = self.components[0]), [1000*t.rvs() for t in self.pof_dists])) for i in range(n)]:
            self.data_points[x] += 1
            
    def sumarise(self):
        print("For the one where we sample the PoF every iteration")
        plt.title("Probability of n-failures")
        plt.xlabel("no. failures")
        plt.ylabel("Probability as a percent")
        
        plt.bar(list(range(0,self.components[0]+1)), [100*x/sum(self.data_points) for x in self.data_points])
        plt.show()
        plt.figure()
        
        decimal_data = [x/sum(self.data_points) for x in self.data_points]
        
        print("After ", sum(self.data_points), " Monte-Carlo Iterations.")
        print("Probability of total failure = ", 100*decimal_data[len(decimal_data) - 1], "%")
        print("Expected efficiency = ", 100 - 100 * sum([self.iof(x+1)*0.01*decimal_data[x] for x in range(self.components[0]+1)]), "%")
        print("")
        
                
             
if __name__ == "__main__":
    
    ############
    ### DEMO ###
    ############
    
    #The MCS for PoF is not sampled each iteration
    Test1 = NormalParallelOperation((4,1/3), pof_dists = (0.1, 0.12, 0.13, 0.14))
    Test1.simulate(10000)
    Test1.sumarise()
    
    #The MCS for PoF is sampled each iteration
    Test2 = NormalParallelOperation2((4,1/3), pof_dists = ((0.1,0.1),(0.2,0.3),(0.12,0.01),(0.1,0.4)))
    Test2.simulate(10000)
    Test2.sumarise()
    
    """
    Notes on output:
        Because the components all contribute some percentage to the output, e.g 30%, 100%, and because we have the probabilities
        of certain number of failures, we can multiply the (prob of n failures) by the (IoF), and sum for all number of failures.
    """
    