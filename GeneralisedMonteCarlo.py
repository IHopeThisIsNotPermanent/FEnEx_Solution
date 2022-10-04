from ReliabilityFunctions import *
from linfunc import *


import random, time, math
import numpy as np
import matplotlib.pyplot as plt  

HOTWIRE_TEST = {"IN":(("A","B"),()),
                "A":(("C","D"),(FailureFunction(params = (1.2, 1230)),FailureCount(),1, 1500)),
                "B":(("C","E"),(FailureFunction(params = (1.2, 1230)),FailureCount(),1, 1500)),
                "C":(("D","E"), (FailureFunction(params = (1.2, 1230)),FailureCount(),1, 1500)),
                "D":(("OUT",),(FailureFunction(params = (1.2, 1230)),FailureCount(),1, 1500)),
                "E":(("OUT",),(FailureFunction(params = (1.2, 1230)),FailureCount(),1, 1500)),
                "OUT":((),())}

class GMC:
    def __init__(self, node_info, arange):
        """
        

        """
        
        #Determine the order, and count of each node for displaying
        for node in node_info:
            node_info[node] = list(node_info[node]) + [[0,1,1],]
        Queue = ["IN",]
        Next_Queue = []
        while Queue:
            for nxt in Queue:
                for check in node_info[nxt][0]:
                    Next_Queue.append(check)
                    node_info[check][2][0] = node_info[nxt][2][0] + 1
            Queue = list(Next_Queue)
            Next_Queue = []
            
        node_count = {}
        for x in range(1+max([node_info[n][2][0] for n in node_info])):
            node_count[x] = 0   
            
        for n in node_info:
            node = node_info[n]
            node[2][1] = node_count[node[2][0]]
            node_count[node[2][0]] += 1
            
        for n in node_info:
            node = node_info[n]
            node[2][2] = node_count[node[2][0]]
    
        self.node_info = node_info
        
        self.arange = arange
        
        self.data = [0]*arange[2]
    
    def disp(self):
        
        fig, ax = plt.subplots()
        
        x_vals = [self.node_info[n][2][0] for n in self.node_info]
        y_vals = [self.node_info[n][2][1]-self.node_info[n][2][2]*0.5 for n in self.node_info]
        
        plt.scatter(x_vals, y_vals)

        
        for n in self.node_info:
            node = self.node_info[n]
            for other_n in node[0]:
                other = self.node_info[other_n]
                plt.plot((node[2][0], other[2][0]),
                         (node[2][1]-node[2][2]*0.5, other[2][1]-other[2][2]*0.5))
        
        for i,txt in enumerate(self.node_info):
            ax.annotate(txt, (x_vals[i], y_vals[i]+0.07), ha = "center")
        
        plt.ylim([min(y_vals)-0.07,max(y_vals)+0.14])
        
        plt.axis("off")
        
        plt.figure()
            
    def reliability(self, failures): #TODO: precalcualte the reliability.
        cumulation = {}
        for index, node in enumerate(self.node_info):
            cumulation[node] = [0, failures[index]]
        cumulation["IN"] = [1, 1]
        cumulation["OUT"] = [0, 1]
        for node in self.node_info:
            for nxt in self.node_info[node][2][2]:
                cumulation[nxt][0] = most(cumulation[nxt][0]+self.node_info[node][2][1]*cumulation[node][0]*cumulation[node][1])
        return cumulation["OUT"][0] * cumulation["OUT"][1]
        
    def simulate(self, n = 10000, timeit = False): 
        if timeit:
            T1 = time.time()
        
        for i in range(n):
            
            #Given different setups, for example, maybe you have multiple distributions for when the component fails once, twice, n times
            #Whatever the input is, this is the code block where you generate the fail segments, which is all this method really needs.
            #the fail segments are just the times that the component is not online.
            
            fail_segments = []
            for comp_index in range(len(self.node_info)-2): #for each component
                node_name = list(self.node_info.keys())[comp_index+1]
                fail_count = self.node_info[node_name][1][1].sample() #sample how many failures
                nxt = [0,] * fail_count
                for r in range(fail_count):
                    start = self.node_info[node_name][1][0].sample() #sample when the failure occurs
                    nxt[r] = FailSegment(start, start + self.node_info[node_name][1][2], 2**comp_index) #record the range it occurs at using the ttf
               
                nxt.sort()
                
                index = 0
                while index < len(nxt)-1: #merge segments, if failures occur while you are fixing (may be wrong assumption)
                    if nxt[index].collide(nxt[index+1]):
                        merged = nxt[index].merge(nxt[index+1])
                        del nxt[index]
                        del nxt[index]
                        nxt.insert(index, merged)
                    else:
                        index += 1
                fail_segments = fail_segments + nxt
            
            fail_segments.sort()

            for x in fail_segments:
                print(str(x))
             
            
            
            
        if timeit:
            print(n, " Iterations in ", time.time() - T1, " seconds.")
        
    def iof(self, n = 1):
        return max(0, 1-(self.n_comps-n)*self.comp_contribution)
    
    def summarise(self):
        
        most = max([max([0,] + [y[0] for y in x.vals]) for x in self.data])
        least = min([min([most, ]+[y[0] for y in x.vals]) for x in self.data])
        
        plt.title("Probability of n-failures")
        plt.xlabel("Time")
        plt.ylabel("Probability of exactly n failues")
        intg = sum([self.data[n].integral for n in range(self.n_comps)]) #sum the failures
        intg = self.iteration_count
        for n in range(self.n_comps):
            disp = self.data[n].vals
            plt.plot([x[0] for x in disp], [(x[1])/intg for x in disp], label = str(n+1) + " failures")
        plt.legend()
        plt.show()
        plt.figure()
        
        RESOLUTION = 1000
        
        if not self.sorted:
            self.sorted = True
            for x in self.data:
                x.vals.insert(0,(least,0))
                x.vals.append((most,0))
            
            self.arranged_data = []
            for comp in range(self.n_comps):
                self.arranged_data.append(linsample([x[0] for x in self.data[comp].vals], [x[1]/intg for x in self.data[comp].vals], (least, most, RESOLUTION)))
        
        
        plt.title("Expected impact")
        plt.xlabel("Time")
        plt.ylabel("Efficiency")
        
        x_vals = list(np.arange(least, most, (most-least)/RESOLUTION))
        while len(x_vals) > RESOLUTION:
            x_vals.pop()
        y_vals = [1, ] * RESOLUTION
        for x in range(RESOLUTION):
            for comp in range(self.n_comps):
                y_vals[x] -= self.arranged_data[comp][x]*self.iof(comp+1)
                
        plt.plot(x_vals, y_vals)
        plt.show()
        plt.figure()

if __name__ == "__main__":
    TEST1 = GMC(HOTWIRE_TEST, (0,1234,1234))
    TEST1.disp()
    TEST1.simulate(2)
