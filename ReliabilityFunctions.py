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
            self.intg_func = lambda t : 1 - math.exp(-1*(t/params[1])**params[0])

    def sample(self):
        return self.sample_func()
    
    def intg(self, t):
        if t < 0:
            return 0
        return self.intg_func(t)
    
    
class FailureCount:
    def __init__(self, choose = "Set", params = None):
        """
        This is the class that is a standin for the number of failures the component is expected to have
        over a given period of time. The only thing the actual class must have is the sample function.
        
        """
        if params is None:
            if choose == "Set":
                params = 1
                
            if choose == "Discrete":
                params = {0:0.5, 1:0.5}
            
        
        if choose == "Set":
            self.sample_func = lambda : params
            self.sample_expected = lambda: params
            
        if choose == "Discrete":
            total = 0
            for key in params:
                total += params[key]
                params[key] = total
            self.sample_func = lambda : 1 #NOT CORRECT FIX LATER 
            self.sample_expected = params[1]
        
    def sample(self):
        return self.sample_func()
    
    def expected(self):
        return self.sample_expected()
    
    
    
if __name__ == "__main__":
    pass
        