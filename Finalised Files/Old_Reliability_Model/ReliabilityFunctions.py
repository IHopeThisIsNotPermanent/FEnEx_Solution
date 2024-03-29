import random, math
from scipy.stats import norm

import numpy as np

def cap(x, most):
    if x > most:
        return most
    return x


class FailureFunction:
    def __init__(self, choose = "Weibull", params = None):
        """
        This is the standin for the model that you sample for the integral of the failure dist (used for the 
        analytic methods), or to sample the failure times (used for the monte carlo method).
        Note intg and sample_func are not defined for all choices of distribution.
        
        Inputs
        ------
        choose : string
            The distribution you want to use, choose from:
                Weibill, Constant, Normal, NDWeibull
                
        params : list<float>
            choose       | params
            ----------------------------
            Weibull      | (beta, eta)
            Constant     | (value, ttr)
            Normal       | (mean, sd)
            NDWeibull    | ((prob of 1 failure, ... prob of N failures),(beta_1, eta_1),(beta_2, eta_2),...(beta_N, eta_N))
            
        """
        
        if params is None:
            if choose == "Weibull":
                params = (2,10)
            if choose == "Constant":
                params = (0.5, 1)
            if choose == "Normal":
                params = (0,1)
            if choose == "NDWeibull":
                params = ((0.5,0.5),(2,10),(2,10))
                
        if choose == "Weibull":
            self.sample_func = lambda : (((-1*math.log(1-random.random()))**(1/params[0]))*params[1],) 
            self.intg_func = lambda t : 0 if t <= 0 else 1 - math.exp(-1*(t/params[1])**params[0])

        if choose == "Constant":
            self.sample_func = lambda : (params[0] < random.random(),)
            self.intg_func = lambda t : t * (params[0]/params[1]) #kinda jank, but if you "integrate" between 
                                                                #t and t-ttr it will always return params[0]
                                                                
        if choose == "Normal":
            adjusted_cdf = lambda x : norm.cdf((x-params[0])/params[1])
            self.sample_func = lambda : ((norm.ppf(random.random()*(1-adjusted_cdf(0)) + (adjusted_cdf(0)))+(params[0]/params[1])),)
            self.intg_func = lambda t : 0 if t <= 0 else adjusted_cdf(t) - adjusted_cdf(0)

        if choose == "NDWeibull":
            """
            This is meant to be a standin for an actual model. please ignore. 
            """
            weibull = lambda beta, eta: ((-1*math.log(1-random.random()))**(1/beta))*eta
            self.sample_func = lambda : (lambda count: (lambda inp: tuple([sum(inp[:n+1]) for n in range(len(inp))]))([weibull(params[1+x][0],params[1+x][1]) for x in range(int(count))]))(np.random.choice(range(1,len(params[0])+1), p = params[0])) 
    def sample(self):
        """
        This function samples the distribution.

        Returns
        -------
        float
            The time the component failed
        """
        return self.sample_func()
    
    def intg(self, t):
        """
        This function integrates the function between 0-t

        Parameters
        ----------
        t : float
            the time you wish to integrate to.

        Returns
        -------
        float
            the integral of the distribution.

        """
        return self.intg_func(t)
        
if __name__ == "__main__":
    pass
        