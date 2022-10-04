#Decomposition Method
from ReliabilityFunctions import *

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

def DFSPaths(D, u, v):
    visited = {}
    for x in D:
        visited[x] = False
    currentPath = []
    simplePaths = []
    DFS(D, u, v, visited, currentPath, simplePaths)
    return simplePaths

def DFS(D, u, v, visited, currentPath, simplePaths):
    if visited[u]:
        return
    visited[u] = True
    currentPath.append(u)
    if u == v:
        simplePaths.append(list(currentPath))
        visited[u] = False
        currentPath.pop()
        return
    for x in D[u][2]:
        DFS(D,x,v,visited,currentPath,simplePaths)
    try:
        currentPath.pop()
    except:
        pass
    visited[u] = False

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
        
        self.checklist = []
        
        temppaths = [[list(node_info.keys()).index(y)-1 for y in x[1:len(x)-1]] for x in DFSPaths(node_info, "IN", "OUT")]
        
        paths = []
        for x in temppaths:
            paths.append(0)
            for i in range(len(node_info)-2):
                paths[len(paths)-1] = paths[len(paths)-1] << 1
                if i in x:
                    paths[len(paths)-1] += 1
        
        all_paths = []
        
        for x in range(2**len(paths)):
            bools = fill("0", len(paths), str(bin(x))[2:])
            nxt = 0
            for i,x in enumerate(bools):
                nxt |= int(x)*paths[i]
            all_paths.append(nxt)
            
        self.all_paths = list(set(all_paths))
    
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
        
        plt.ylim([min(y_vals)-0.07,max(y_vals)+0.14])
        
        plt.axis("off")
        
        
        plt.figure()
    
    def reliability(self, failures): #TODO: precalcualte the reliability
        cumulation = {}
        for index, node in enumerate(self.node_info):
            cumulation[node] = [0, failures[index]]
        cumulation["IN"] = [1, 1]
        cumulation["OUT"] = [0, 1]
        for node in self.node_info:
            for nxt in self.node_info[node][2]:
                cumulation[nxt][0] = most(cumulation[nxt][0]+self.node_info[node][1]*cumulation[node][0]*cumulation[node][1])
        return cumulation["OUT"][0] * cumulation["OUT"][1]
            
    
    def sample_reliability(self,t):
        total = 0
        
        for x in self.all_paths: #range(2**(len(self.node_info)-2)):
            bools = fill("0", len(self.node_info)-2, str(bin(x))[2:])
            bools = "1"+bools+"1"
            bools = [int(x) for x in bools]
            R = self.reliability(bools)
            if R == 0:
                continue
            P = 1
            for index, node in enumerate(self.node_info):
                if index == 0 or index == len(self.node_info)-1:
                    continue
                if bools[index] == 0:
                    inv = lambda x: x 
                else:
                    inv = lambda x: 1 - x
                failfunc = self.node_info[node][0].intg
                P *= inv(failfunc(t) - failfunc(t-self.node_info[node][3]))
            total += R*P
        
        return total
    
        

if __name__ == "__main__":
    Test1 = System(EXAMPLESYSTEM)
    Test1.disp()
    plt.plot([x/10 for x in range(300)], [Test1.sample_reliability(x/10) for x in range(300)])
    
    Test2 = System(PARALLEL_TEST)
    Test2.disp()
    plt.plot([x/10 for x in range(300)], [Test2.sample_reliability(x/10) for x in range(300)])
    
    Test3 = System(COMPLEXISH_TEST)
    Test3.disp()
    plt.plot([x/10 for x in range(300)], [Test3.sample_reliability(x/10) for x in range(300)])
     
    HotwireTest = System(HOTWIRE_TEST)
    HotwireTest.disp()
    plt.plot([x for x in range(1234)], [HotwireTest.sample_reliability(x) for x in range(1234)])
    