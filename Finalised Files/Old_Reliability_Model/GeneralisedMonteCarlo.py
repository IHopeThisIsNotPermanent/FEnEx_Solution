from ReliabilityFunctions import FailureFunction
from functools import lru_cache

import matplotlib.pyplot as plt  

class FailureSample(FailureFunction):
    def __init__(self, multi = False, choose = "Weibull", params = None):
        if not multi:
            super().__init__(choose, params)
    
    
    
    
HOTWIRE_TEST = {"IN":(None, 1, ("A","B"), 0),
                "A":(FailureFunction(params = (1.2, 1230)), 1, ("C","D"), 1500),
                "B":(FailureFunction(params = (1.2, 1230)), 1, ("C","E"), 1500),
                "C":(FailureFunction(params = (1.2, 1230)), 1, ("D","E"), 1500),
                "D":(FailureFunction(params = (1.2, 1230)), 1, ("OUT",), 1500),
                "E":(FailureFunction(params = (1.2, 1230)), 1, ("OUT",), 1500),
                "OUT":(None, 1, (), 0)}

COMPLEXISH_TEST = {"IN":(None, 1, ("A","C"), 0),
                "A":(FailureFunction(params = (10, 12)),1,("B",), 6),
                "B":(FailureFunction(params = (2, 12)),1,("E","F","G"), 5),
                "C":(FailureFunction(params = (1.2, 4)),1,("D","O"), 6),
                "D":(FailureFunction(params = (2, 5)),1,("F","G"), 4),
                "E":(FailureFunction(params = (10, 1)),1,("H",), 6),
                "F":(FailureFunction(params = (12, 7)),1,("H",), 2),
                "G":(FailureFunction(params = (13, 8)),1,("I","H"), 3),
                "H":(FailureFunction(params = (20, 2)),1,("J",), 5),
                "I":(FailureFunction(params = (4, 10)),1,("J",), 2),
                "J":(FailureFunction(params = (5, 13)),1,("OUT",), 6),
                "K":(FailureFunction(params = (1.4, 14)),1,("J",), 3),
                "L":(FailureFunction(params = (1.2, 10.2)),1,("K",), 2),
                "M":(FailureFunction(params = (1.2, 11)),1,("K",), 1),
                "N":(FailureFunction(params = (1.2, 12)),1,("M","D", "L"), 2),
                "O":(FailureFunction(params = (1.2, 13)),1,("N",), 4),
                "OUT":(None, 1, (), 0)}

def most(x):
    if x > 1:
        return 1
    return x

class GMC:
    def __init__(self, node_info, arange):
        """
        This class is used to simulate the generalised monte carlo simulations.
        Given the node info, and the arange what this class will do is calcualte the reliability values for all
        the t values in the arange. This is because if you try and store the outcome of each iteration of the simulation
        as the range of times the system was running at efficiency E, then the amount of info you need to do so gets
        very large very quickly.
        Also note we use FailureSample, not FailureFunction. This is because the output of sampling the funciton
        
        PARAMETERS
        ----------
        node_info : dict
            a mapping of each {node_name: (failfunc, contribution, node list, TTR)}
            node_info must contain "IN" :(None, 1, (nodes connected to In), 0)
                               and "OUT":(None, 1, (), 0)
            
        arange : tuple
            the arange of times you wish to be able to sample
            of the form (starting value, ending value, number of steps)
        """
        #Determine the order, and count of each node for displaying
        #The algorithm works by assigning each node 3 values, its rank, its order, and the count
        #a nodes rank is the distance the node is from IN
        #the nodes order is used to distinguish between nodes of the same rank, ranging from 0 - number of node
        #of that order
        #the nodes count is the number of nodes with the same rank.
        
        #add the three values to the list of parameters for each node
        for node in node_info:
            node_info[node] = list(node_info[node]) + [[0,1,1],]
        
        Queue = ["IN",] #create a FIFO queue
        while Queue:
            nxt = Queue.pop(0) #take the first node from the queue
            for check in node_info[nxt][2]: #assign the rank of current rank + 1 to all nodes connected
                Queue.append(check)
                node_info[check][4][0] = node_info[nxt][4][0] + 1
            
        node_count = {} #set up the mapping from node rank, a counter
        for x in range(1+max([node_info[n][4][0] for n in node_info])):
            node_count[x] = 0   
            
        for n in node_info: # iterate through the nodes, update the specific count for the nodes rank, and 
                            # set the order of that node to the current count
            node = node_info[n]
            node[4][1] = node_count[node[4][0]]
            node_count[node[4][0]] += 1
            
        for n in node_info: #set the count in each node to the count of its rank.
            node = node_info[n]
            node[4][2] = node_count[node[4][0]]
        
        
        #Reorder the keys based on the nodes ranks.
        node = [(x, node_info[x]) for x in node_info]
        node = sorted(node, key = lambda x: x[1][4][0])
        
        node_info = {x[0]: x[1] for x in node}
        
        self.node_info = node_info
        
        self.arange = arange
        
        #this array stores the reliability values calcualted in the simulation
        self.data = [0 for x in range(arange[2])]
        
        #this integer stores the number of iterations of the simulation have been ran
        self.sim_count = 0
        
    def disp(self):
        
        fig, ax = plt.subplots()
        
        x_vals = [self.node_info[n][4][0] for n in self.node_info]
        y_vals = [self.node_info[n][4][1]-self.node_info[n][4][2]*0.5 for n in self.node_info]
        
        plt.title("Node graph")
        
        plt.scatter(x_vals, y_vals)

        
        for n in self.node_info:
            node = self.node_info[n]
            for other_n in node[2]:
                other = self.node_info[other_n]
                plt.plot((node[4][0], other[4][0]),
                         (node[4][1]-node[4][2]*0.5, other[4][1]-other[4][2]*0.5))
        
        for i,txt in enumerate(self.node_info):
            ax.annotate(txt, (x_vals[i], y_vals[i]+0.07), ha = "center")
        
        plt.ylim([min(y_vals)-0.07,max(y_vals)+0.14])
        
        plt.axis("off")
        
        
        plt.figure()
           
    @lru_cache(maxsize=None)
    def path_output(self, failures):
        """
        This function tells you the output of the system, given certain nodes failing.
        
        The algorithm iterates through all the node by rank, where each nodes output is 
        the sum of the nodes leading into it, multiplied by the nodes contribution, multiplied 
        by if the node succeded

        we can iterate by rank, because nodes of the same rank will never lead into each other, and
        node of a greater rank will always only have input nodes of smaller ranks.
        
        Note: this algorithm requires the keys of the node_info to be ordered by rank.

        Parameters
        ----------
        failures : binary
            a zero at position n means that the node whos key has index n has failed.
            a one means otherwise.

        Returns
        -------
        float
            the output of the system.

        """
        cumulation = {} #maps each node to a list, the first value is the current sum of all input nodes
                        #the second value is whether or not the node has failed.
                        #the output of a node is these two values multiplied by each other
        for index, node in enumerate(self.node_info):
            if index == 0 or index == len(self.node_info)-1:
                continue
            cumulation[node] = [0, failures[index-1]]
        cumulation["IN"] = [1, 1]
        cumulation["OUT"] = [0, 1]
        
        for node in self.node_info: #iterate through the nodes.
            for nxt in self.node_info[node][2]:
                cumulation[nxt][0] = most(cumulation[nxt][0]+self.node_info[node][1]*cumulation[node][0]*cumulation[node][1])
        return cumulation["OUT"][0] * cumulation["OUT"][1]
    
    def simulate(self, n = 10000): 
        """
        This function actually does the simulation. 
        You can run this fuction as many times as you wish.
        
        The algorthm works as follows:
        
        For i in range(number of iterations):
            generate a list of failure times for each component, call it fail_times
            then for each point in the arange, check which components are currently failed, 
            then calcuate the current output of the system, add the output of the system
            to the relivent position to the data list.

        Parameters
        ----------
        n : TYPE, optional int
            This parameter determines the number of iterations you want the simulation to run through. The default is 10000.


        """
        
        #update simulation iteration count.
        self.sim_count += n
        
        fail_times = {} #this dict stores the lists of times each component fails in an iteration of the simulation
        for i in range(n): #
            failures = [1 for x in range(len(self.node_info)-2)]
            for x in self.node_info:
                if x in ("IN", "OUT"):
                    continue
                fail_times[x] = self.node_info[x][0].sample()
            
            crt_fail = {} # We keep track of the index of the last time the node failed, and how much longer it will be failed because of this time.
                          # a none on index 0 means that there are no times left to bother checking.
            for x in self.node_info:
                if x in ("IN", "OUT"):
                    crt_fail[x] = (None,self.arange[2])
                    continue
                if len(fail_times[x]) == 0:
                    crt_fail[x] = [None, 0]
                else:
                    crt_fail[x] = [0,0]
            
            for step in range(self.arange[2]): #update each time point in data
                t = self.arange[0] + (self.arange[1]-self.arange[0])*(step/self.arange[2])
                
                for i,x in enumerate(crt_fail): #iterate through the keeping track of who is failed list
                    if crt_fail[x][0] is None: #if it cannot fail again, ignore this node
                        continue
                    if crt_fail[x][1] == 0: #if it is currently not failed
                       if fail_times[x][crt_fail[x][0]] <= t: #if it now is failed
                           failures[i-1] = 0                  #update the failures list
                           crt_fail[x] = [crt_fail[x][0] + 1, self.node_info[x][3]] #update the crt_fail list
                    else: #if the node is currently failed
                        crt_fail[x][1] -= (self.arange[1]-self.arange[0])/self.arange[2] #reduce the time it has left to be failed  
                        if crt_fail[x][1] <= 0: #if after the reduction it is no longer failed
                            failures[i-1] = 1   #update the failures list
                            crt_fail[x][1] = 0  #update the crt_fail list
                            if len(fail_times[x]) >= crt_fail[x][0]: #if this node has ran out of times it could fail
                                crt_fail[x][0] = None                #update the crt_fail list
                #print(failures, self.path_output(tuple(failures)))
                self.data[step] += self.path_output(tuple(failures)) 
     
    def summarise(self):
        
        plt.title("Expected Impact")
        plt.xlabel("Time")
        plt.ylabel("Efficiency")
        
        plt.plot([self.arange[0] + (self.arange[1]-self.arange[0])*(t/self.arange[2]) for t in range(self.arange[2])],
                 [x/self.sim_count for x in self.data]) 
        
    def sample(self, t):
        """
        Just samples the data list
        If you select a point outside of arange it will return the closest point
        If you select a point inside arange, but not on a point, it will return the closest point

        Parameters
        ----------
        t : float
            The time you wish to sample the reliability of.

        Returns
        -------
        float
            The reliabilty of the system at time t.

        """
        t = int((t - self.arange[0])*self.arange[2]/(self.arange[1]-self.arange[0]))
        
        if t < 0: return self.data[0]/self.sim_count
        if t >= self.arange[2]: return self.data[len(self.data)-1]/self.sim_count
        return self.data[t]/self.sim_count

if __name__ == "__main__":
    if True:    
        TEST1 = GMC(HOTWIRE_TEST, (0,1500,100))
        TEST1.disp()
        TEST1.simulate(n = 10000)
        TEST1.summarise()
        plt.plot([100*x for x in range(16)],[1,0.9950,0.9748,0.9374,0.8823,0.8184,0.7419,0.6621,0.5816,0.5038,0.4332,0.3683,0.3087,0.2565,0.2121,0.1738])
        plt.show()
        plt.figure()
    
    if True:
        TEST2 = GMC(COMPLEXISH_TEST, (0, 30, 300))
        TEST2.disp()
        TEST2.simulate(n = 10000)
        TEST2.summarise()
        
        