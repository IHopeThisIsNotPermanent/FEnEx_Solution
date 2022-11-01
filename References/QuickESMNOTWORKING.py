from ReliabilityFunctions import FailureFunction
import matplotlib.pyplot as plt
from functools import lru_cache


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
            a mapping of each {node_name: (failfunc, contribution, node list, TTR)}
            node_info must contain "IN":(0, None, None, 1,  (nodes connected to In))
                               and "OUT":(0, None, None, 1, ())

        Returns
        -------
        None.

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
        
        #This algorith goes as follows, use the DSF algorithm to create a list of all paths
        #Represent the paths as binaries, for example in a 3 node system, we will say if the first node is
        #in the path set the first bit to 1, if the second node, set the second bit and so on.
        #we then just combine all these paths by iterating through all combinations of the paths, OR-ing '
        #together the binary representations
        
        #get the list of paths as lists of the indexes of each node
        temppaths = [[list(node_info.keys()).index(y)-1 for y in x[1:len(x)-1]] for x in DFSPaths(node_info, "IN", "OUT")]
        
        #convert that list of indexes into the binaries
        paths = []
        for x in temppaths:
            paths.append(0)
            for i in range(len(node_info)-2):
                paths[len(paths)-1] = paths[len(paths)-1] << 1
                if i in x:
                    paths[len(paths)-1] += 1
        
        all_paths = []
        
        print(len(paths))
        
        #iterate through all combinations, OR-ing together the paths. 
        for x in range(2**len(paths)):
            bools = fill("0", len(paths), str(bin(x))[2:])
            nxt = 0
            for i,x in enumerate(bools):
                nxt |= int(x)*paths[i]
            all_paths.append(nxt)
        
        #cache the paths
        self.all_paths = list(set(all_paths))
        self.all_paths.remove(0)
        
        #convert from binary to list of 1's and 0's in string form, we will never or the paths 
        #together again, so this is just more convinient for indexing.
        self.all_paths = [fill('0',len(self.node_info)-2,bin(x)[2:]) for x in self.all_paths]
        

    
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
            cumulation[node] = [0, int(failures[index-1])]
        cumulation["IN"] = [1, 1]
        cumulation["OUT"] = [0, 1]
        
        for node in self.node_info: #iterate through the nodes.
            for nxt in self.node_info[node][2]:
                cumulation[nxt][0] = most(cumulation[nxt][0]+self.node_info[node][1]*cumulation[node][0]*cumulation[node][1])
        return cumulation["OUT"][0] * cumulation["OUT"][1]
            
    
    def sample_reliability(self, t):
        """
        Samples the reliability of the system at time t.
        This function works by iterating through all possible configurations of nodes being failed or not.
        Though we note that all configurations that are not composed of combinations of paths from IN to OUT
        will have a system output of 0, so their contribution is always zero.
        for each configuration whos system output is not 0, we calcuate the system output using system_out, 
        the multiply that by the proability the system is in this configuration, we then sum up the product
        of the system output and configuration probaility.

        Parameters
        ----------
        t : float
            the time you are sampling the system.

        Returns
        -------
        total : float
            the reliability of the system at time t.

        """
        total = 0
        
        for x in self.all_paths: #iterates through all the paths
            R = self.path_output(x) #calcualtes the system output of the path
            
            P = 1 #sets the probability of this path 
            
            for index, node in enumerate(self.node_info): #iterates through each node, multiplying P by the probability
                                                          #the node is currently as the path says it should be
                if index == 0 or index == len(self.node_info)-1: #ignore the IN, and OUT nodes
                    continue
                if x[index-1] == '0': # if the path says the node should be failed, use the probability as given
                    inv = lambda x: x 
                else:
                    inv = lambda x: 1 - x # otherwise do 1 - prob, because thats the probability the node has not 
                                          # failed.
                failfunc = self.node_info[node][0].intg
                #P = the probability the node as the path says is should be (failed or not)
                #and is calucalted as the integral of the failure distribution over the period of time
                #from the sample time, till ttr time back. 
                P *= inv(failfunc(t) - failfunc(t-self.node_info[node][3])) 
                
            total += R*P
        
        return total
    
        

if __name__ == "__main__":

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


    Test3 = System(COMPLEXISH_TEST)
    Test3.disp()
    plt.title("Expected Impact for COMPLEXISH_TEST")
    plt.xlabel("Time")
    plt.ylabel("Efficiency")
    plt.plot([x/10 for x in range(300)], [Test3.sample_reliability(x/10) for x in range(300)])
        