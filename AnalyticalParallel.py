# -*- coding: utf-8 -*-
"""
Created on Tue Sep 20 14:50:59 2022

@author: Saul
"""

from ReliabilityFunctions import *
from itertools import permutations

import numpy as np
import matplotlib.pyplot as plt


class AnalyticalParallel:
    def __init__(self, n_comps, comp_contribution, comp_functions = None, ttf = 1):
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

        self.ttf = ttf
        
    def iof(self, n = 1):
        return max(0, 1-(self.n_comps-n)*self.comp_contribution)
        
    def pf(self, n_fails, t):
        total = 0
        for p in list(set(permutations([1,]*n_fails+[0]*(self.n_comps-n_fails)))):
            temp = 1
            for i, x in enumerate(p):
                if x == 1:
                    flip = lambda x: x
                if x == 0:
                    flip = lambda x: 1 - x
                temp *= flip(self.comp_functions[i].intg(t) - self.comp_functions[i].intg(t - self.ttf))
            total += temp
        return total
    
    def summarise(self):
        plt.title("Probability of n-failures")
        plt.xlabel("Time")
        plt.ylabel("Probability of exactly n failues")

        x_vals = [x/10 for x in range(300)]

        for n in range(self.n_comps):
            plt.plot(x_vals, [self.pf(n+1, x) for x in x_vals])
            
        plt.legend()
        plt.show()
        plt.figure()
    
    
        plt.title("Expected impact")
        plt.xlabel("Time")
        plt.ylabel("Efficiency")
        y_vals = []
        for x in x_vals:
            temp = 1
            for f in range(1,self.n_comps+1):
                temp -= (self.iof(f))*self.pf(f,x)
            y_vals.append(temp)
        
        plt.plot(x_vals, y_vals)
        plt.show()
        plt.figure()
        
if __name__ == "__main__":
    Test2 = AnalyticalParallel(4,1/4,comp_functions = (FailureFunction(params = (10,10)),
                                                      FailureFunction(params = (20,10)),
                                                      FailureFunction(params = (5,5)),
                                                      FailureFunction(params = (4,5))), ttf = 6)
    Test2.summarise()
