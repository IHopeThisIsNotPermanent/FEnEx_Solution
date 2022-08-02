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
        
        if choose == "set":
            self.sample_func = lambda : params
        
        
    def sample(self):
        return self.sample_func()
    
    
class ParallelOperation:
    def __init__(self, n_comps, comp_contribution, comp_function = "Weibull", 
                 comp_params = None, comp_failcount = "Set", comp_failparams = None,
                 ttf = 1):
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

        Parameters
        ----------
        n_comps : int
            The number of components
        comp_contribution : float
            The contribution each component outputs
        comp_function : string, optional
            The function used to determine when each component fails.
        comp_params : list<float>, optional
            The list of parameters for the failure sampling function.
            Function  | Parameters
            ----------------------
            Weibull   | (beta, eta)
            Normal    | (mean, std, upper = 10000)
        comp_failcount : string, optional
            The function you want to use to sample the number of times a peice of equiptment fails.
        comp_failparams : list<float>, optional
            The list of parameters for the failcount sampling function.
            Function  | Parameters
            ----------------------
            Set       | (value)
        ttf : float, optional
            the amount of time it takes to repair a peice of equiptment. 

        Returns
        -------
        None.

        """
        self.n_comps = n_comps
        self.comp_contribution = comp_contribution
        if comp_params is None:
            comp_params = [None,]*n_comps
        if comp_failparams is None:
            comp_failcount = [None,]*n_comps
        self.comp_functions = [FailureFunction(comp_function, params) for params in comp_params]
        self.comp_failcount = [FailureCount(comp_failcount, params) for params in comp_failcount]
        
        self.data = [[] for x in range(n_comps)] #self.data[0] if you fit linear segments to the data points, it will
                                                 #             tell you the number of times only 1 failure was occuing
                                                 #self.data[1] will be 2 failures, ect...
                                                 
        self.sorted = False
        self.arranged_data = [] #the y values of all the aligned x_values
        
    def simulate(self, n = 100000, timeit = False): #probs make quicker
        if timeit:
            T1 = time.time()
        
        self.sorted = False
        for i in range(n):
            nxt = [[self.comp_functions[x].sample() for y in range(self.comp_failcount[x].sample())] for x in range(self.n_comps)]
            nxt.sort()
            for k in range(self.n_comps):
                self.data[k].append(nxt[k])
        if timeit:
            print(n, " Iterations in ", time.time() - T1, " seconds.")
        
    def iof(self, n = 1):
        return max(0, 1-(self.n_comps-n)*self.comp_contribution)
        
    def error(self):
        pass
    
    def summarise(self):
        
        y_vals = list(np.arange(0,1,1/(len(self.data[0])+2)))
        
        most = max([max(x) for x in self.data])
        least = min([min(x) for x in self.data])
        
        if not self.sorted:
            self.sorted = True
            for x in self.data:
                x.sort()
            for x in self.data:
                x.insert(0,least)
                x.append(most)
            
            self.arranged_data = []
            for comp in range(self.n_comps):
                self.arranged_data.append(linfunc.linsample(self.data[comp], y_vals, (least, most, len(self.data[0]))))
            
        
        #Overlayed probabilitys of failure  
          
        plt.title("Cumulative probability of failures overlayed")
        plt.xlabel("Time of failure")
        plt.ylabel("Probability as a percent")
        count = 1
        for x_vals in self.data:
            plt.plot(x_vals, y_vals, label = str(count) + " Failures")
            count += 1
        plt.legend()
        plt.show()
        plt.figure()

        #Predicted efficency over time
        
        plt.title("Predicted efficency over time")
        plt.xlabel("Time")
        plt.ylabel("Efficency as a percent")
        
        x_vals = np.arange(least, most, (most-least)/(len(self.data[0])))
        y_vals = []
        
        for x in range(len(x_vals)):
            total = self.arranged_data[self.n_comps-1][x]*self.iof(self.n_comps)
            for comp in range(self.n_comps-1):
                total += (self.arranged_data[comp][x]-self.arranged_data[comp+1][x])*(self.iof(comp+1))
            y_vals.append(100*(1-total))
        
        plt.plot(x_vals, y_vals)
        
        
if __name__ == "__main__":
    Test1 = ParallelOperation(4,1/3, comp_function = "Weibull")
    Test1.simulate(timeit = True)
    Test1.summarise()
        
        
        
        
        
        
        
        
        
        