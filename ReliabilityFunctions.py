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
            self.sample_expected() = lambda: params
        
        
    def sample(self):
        return self.sample_func()
    
    def expected(self):
        return self.sample_expected()
    
    
    
if __name__ == "__main__":
    pass
        