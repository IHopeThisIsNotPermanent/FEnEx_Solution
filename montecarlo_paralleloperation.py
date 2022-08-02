import random, time
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import truncnorm

class FailureFunction:
    """
    
    INPUTS
    ------
    choose : string
        The distribution you want to use, choose from:
            Weibill, 
    params : list<float>
        choose       | params
        ----------------------------
        Weibull      | (beta, eta)
    """
    def __init__(self, choose = "Weibull", params = None):
        self.choose = choose
        if params is None:
            if choose == "Weibull":
                self.params = (2,10)
        
    def sample(self, n = 1):
        if self.choose == "Weibull":
            return [((-1*math.log(x))**(1/self.params[0]))*self.params[1] for x in np.random.rand(n)]
        
    def f(x):
        if self.choose == "Weibull":
            return math.exp(-1*(x/self.params[1])**self.params[0])

class ParallelOperation:
    def __init__(self, n_components, component_contribution, component_function = )