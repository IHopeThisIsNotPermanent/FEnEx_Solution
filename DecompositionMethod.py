#Decomposition Method
from ReliabilityFunctions import *

import numpy as np   
import networkx as nx  
import matplotlib.pyplot as plt
import time

EXAMPLESYSTEM = {"IN":(None, None, 1, ("A",)),
                 "A":(FailureFunction(),FailureCount(),1,("B","C","D")),
                 "B":(FailureFunction(),FailureCount(),0.5,("E",)),
                 "C":(FailureFunction(),FailureCount(),1,("E","F")),
                 "D":(FailureFunction(),FailureCount(),0.5,("F",)),
                 "E":(FailureFunction(),FailureCount(),0.7,("G",)),
                 "F":(FailureFunction(),FailureCount(),0.7,("G",)),
                 "G":(FailureFunction(),FailureCount(),1,("OUT",)),
                 "OUT":(None, None, 1, ())}

def fill(character, length, current):
    if len(current) >= length:
        return current
    return character*(length-len(current)) + current

class System:
    def __init__(self, node_info):
        """
        This class represents Complex Reliability Systems

        Parameters
        ----------
        node_info : dict
            a mapping of each node to their failfunc, failcount, contribution, node list
            node_info must contain "IN":(None, None, 1,  (nodes connected to In))
                               and "OUT":(None, None, 1, ())

        Returns
        -------
        None.

        """
        
        #Determine the order, and count of each node for displaying
        for node in node_info:
            node_info[node] = list(node_info[node]) + [[0,1,1],]
        
        Queue = ["IN",]
        Next_Queue = []
        while Queue:
            for nxt in Queue:
                for check in node_info[nxt][3]:
                    Next_Queue.append(check)
                    node_info[check][4][0] = node_info[nxt][4][0] + 1
            Queue = list(Next_Queue)
            Next_Queue = []
            
                
        node_count = {}
        for x in range(1+max([node_info[n][4][0] for n in node_info])):
            node_count[x] = 0   
            
        for n in node_info:
            node = node_info[n]
            node[4][1] = node_count[node[4][0]]
            node_count[node[4][0]] += 1
            
        for n in node_info:
            node = node_info[n]
            node[4][2] = node_count[node[4][0]]
    
        self.node_info = node_info
        
        self.efficiencies = None
    
    def disp(self):
        
        fig, ax = plt.subplots()
        
        x_vals = [self.node_info[n][4][0] for n in self.node_info]
        y_vals = [self.node_info[n][4][1]-self.node_info[n][4][2]*0.5 for n in self.node_info]
        
        plt.scatter(x_vals, y_vals)

        
        for n in self.node_info:
            node = self.node_info[n]
            for other_n in node[3]:
                other = self.node_info[other_n]
                plt.plot((node[4][0], other[4][0]),
                         (node[4][1]-node[4][2]*0.5, other[4][1]-other[4][2]*0.5))
        
        for i,txt in enumerate(self.node_info):
            ax.annotate(txt, (x_vals[i], y_vals[i]+0.07), ha = "center")
        
        #plt.axis("off")
        
        plt.figure()
    
    def reliability(self, failures):
        
    
    def sample_reliability(self,t):
        total = 0
        
        T1 = time.time()
        
        for x in range(2**(len(self.node_info)-2)):
            bools = fill("0", len(self.node_info)-2, str(bin(x))[2:])
            Reliability = 
        
        print(time.time()-T1)
        
        return total
    
    def sample_pdf(self, efficiency, t):
        pass
        

if __name__ == "__main__":
    Test1 = System(EXAMPLESYSTEM)
    Test1.disp()
    Test1.sample_reliability(1)