#Decomposition Method
from ReliabilityFunctions import *

"""
https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8764359
"""

import numpy as np   
import networkx as nx  
import matplotlib.pyplot as plt
import time

EXAMPLESYSTEM = {"IN":(None, 1, ("A",), 0),
                 "A":(FailureFunction(),1,("B","C","D"), 0.1),
                 "B":(FailureFunction(),0.5,("E",), 0.1),
                 "C":(FailureFunction(),1,("E","F"), 0.1),
                 "D":(FailureFunction(),0.5,("F",), 0.1),
                 "E":(FailureFunction(),0.7,("G",), 0.1),
                 "F":(FailureFunction(),0.7,("G",), 0.1),
                 "G":(FailureFunction(),1,("OUT",), 0.1),
                 "OUT":(None, 1, (), 0)}

PARALLEL_TEST = {"IN":(None, 1, ("A","B","C","D"), 0),
                 "A":(FailureFunction(params = (10,10)),  0.25, ("OUT",), 6),
                 "B":(FailureFunction(params = (20,10)),  0.25, ("OUT",), 6),
                 "C":(FailureFunction(params = (5,5)),  0.25, ("OUT",), 6),
                 "D":(FailureFunction(params = (4,5)),  0.25, ("OUT",), 6),
                 "OUT":(None, 1, (), 0)}

HOTWIRE_TEST = {"IN":(None, 1, ("A","B"), 0),
                "A":(FailureFunction(params = (1.2, 1230)),1,("C","D"), 1500),
                "B":(FailureFunction(params = (1.2, 1230)),1,("C","E"), 1500),
                "C":(FailureFunction(params = (1.2, 1230)),1,("D","E"), 1500),
                "D":(FailureFunction(params = (1.2, 1230)),1,("OUT",), 1500),
                "E":(FailureFunction(params = (1.2, 1230)),1,("OUT",), 1500),
                "OUT":(None, 1, (), 0)}


def fill(character, length, current):
    if len(current) >= length:
        return current
    return character*(length-len(current)) + current

def most(x):
    if x > 1:
        return 1
    return x

class System:
    def __init__(self, node_info):
        """
        This class represents Complex Reliability Systems

        Parameters
        ----------
        node_info : dict
            a mapping of each node to their failfunc, failcount, contribution, node list, TTf
            node_info must contain "IN":(0, None, None, 1,  (nodes connected to In))
                               and "OUT":(0, None, None, 1, ())

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
                for check in node_info[nxt][2]:
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
            for other_n in node[2]:
                other = self.node_info[other_n]
                plt.plot((node[4][0], other[4][0]),
                         (node[4][1]-node[4][2]*0.5, other[4][1]-other[4][2]*0.5))
        
        for i,txt in enumerate(self.node_info):
            ax.annotate(txt, (x_vals[i], y_vals[i]+0.07), ha = "center")
        
        #plt.axis("off")
        
        plt.figure()
    
    def sample_reliability(self,t):
        pass
    
        

if __name__ == "__main__":
    #Test1 = System(EXAMPLESYSTEM)
    #Test1.disp()
    #tot=Test1.sample_reliability(1)
    Test2 = System(PARALLEL_TEST)
    Test2.disp()
    plt.plot([x/10 for x in range(300)], [Test2.sample_reliability(x/10) for x in range(300)])
    
    