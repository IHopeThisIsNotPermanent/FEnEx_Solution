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
            node_info must contain "IN":(None, 1, (nodes connected to In), 0)
                               and "OUT":(None, 1, (), 0)
        
        contribution can either be a float between 0 and 1 inclusivly, or a map, containing a list of tuples
        each indexed at the same index as the output for the corresponding connection
        containing the values -
        (base input, priority, max input, "FORWARD")
        or
        (base output, priority, min output, "BACKWARD")
        
        scenario1 - you have more then 100% input to a node, ways to handle:
            Option 1 - ignore it, you have a system already in place to remove exess, and it does not 
                need to be simulated, as it can be represented by capping out inputs at 100%
            Option 2 - reduce the work done my machines prior to set the input to 100%
        
        scenario2 - you have less than 100% input to a set of nodes, ways to handle:
            Option 1 - ignore it, you just split the input evenly among the machines you already have
            Option 2 - disable as many nodes as you can further down, and split the input between the remaining nodes
            
        scenario3 - a node is disabled, and so no input can be used, ways to handle:
            this is same as the first scenario, the expected input for a disabled node is 0%, so any amount is over
            100%


        Returns
        -------
        None.

        """
        
        #Calcualte the backwards node list, used in the path value calculation
        
        backward_node_info = {}
        for node in node_info:
            backward_node_info[node] = node_info[node]
            backward_node_info[node][2] = []
            
        for node in node_info:
            for nxt in node_info[node][2]:
                backward_node_info[nxt].append(node)
            
        for node in backward_node_info:
            backward_node_info[node][2] = tuple(backward_node_info[node][2])
        
        self.backward_node_info = backward_node_info
        
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
        
        
        
        self.all_paths = []
        
        Queue = [[1,]*(len(self.node_info)-2),]
        
        self.all_paths.append(tuple(Queue[0]))
        
        while Queue:
            nxt = Queue.pop(0)
            for i in range(len(self.node_info)-2):
                if nxt[i] == 0:
                    continue
                test = list(nxt)
                test[i] = 0
                test = tuple(test)
                if self.path_output(test) == 0:
                    continue
                if test in self.all_paths:
                    continue
                Queue.append(test)
                self.all_paths.append(test)
                
        
                    
    
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
                        #the third is the last time the node was updated
                        #the forth is if this node has been bounced (0 none, 1 forward, 2 backward, 3 both)
                        #the output of a node is these two values multiplied by each other
        for index, node in enumerate(self.node_info):
            if index == 0 or index == len(self.node_info)-1:
                continue
            cumulation[node] = [0, failures[index-1], 0, 0]
        cumulation["IN"] = [1, 1, 0, 0]
        cumulation["OUT"] = [0, 1, 0, 0]
        
        node_index = 0
        time_index = 0
        
        while node_index < len(self.node_info):
            node = self.node_info.keys[node_index]
            if time_index > cumulation[node][2]:
                cumulation[node][2] = time_index
            if not isinstance(self.node_info[node][2][0][1], tuple):
                for nxt in self.node_info[node][2]:
                    cumulation[nxt][0] = most(cumulation[nxt][0]+self.node_info[node][1]*cumulation[node][0]*cumulation[node][1])
            elif self.node_info[node][2][0][1][3] == "Backward":
                for nxt in self.node_info[node][2]:
                    cumulation[nxt][0] = most(cumulation[nxt][0]+self.node_info[node][1]*cumulation[node][0]*cumulation[node][1])
            else:
                total = 0
                for nxt in self.node_info[node][2]:
                    if cumulation[nxt][1] == 0:
                        total += self.node_info[node][0]
                
                while True:
                    
                    crt_lowest = 0
                    crt_node = -1
                    
                    for nxt, i in enumerate(self.node_info[node][2]):
                        if cumulation[nxt][1] != 0 and cumulation[nxt][3] in (0,2):
                            if crt_index ==nnj -1:
                                crt_index = nxt
                                crt_lowest = self.node_info[node][1][1]
                        
                    if crt_node == "-1":
                        break
                    
                    amount = min(total, (self.node_info[node][1][2] - self.node_info[node][1][0]))
                    total -= amount
                    cumulation[node][0] = self.node_info[node][1][0] + amount
                    
        
    
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
                if x[index-1] == 0: # if the path says the node should be failed, use the probability as given
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
    PARALLEL_TEST = {"IN":(None, 1, ("A","B","C","D"), 0),
                     "A":(FailureFunction(params = (10,10)),  0.25, ("OUT",), 6),
                     "B":(FailureFunction(params = (20,10)),  0.25, ("OUT",), 6),
                     "C":(FailureFunction(params = (5,5)),  0.25, ("OUT",), 6),
                     "D":(FailureFunction(params = (4,5)),  0.25, ("OUT",), 6),
                     "OUT":(None, 1, (), 0)}

    HOTWIRE_TEST = {"IN":(None, 1, ("A","B"), 0),
                    "A":(FailureFunction(params = (1.2, 1230)),1,("C","D"), 2000),
                    "B":(FailureFunction(params = (1.2, 1230)),1,("C","E"), 2000),
                    "C":(FailureFunction(params = (1.2, 1230)),1,("D","E"), 2000),
                    "D":(FailureFunction(params = (1.2, 1230)),1,("OUT",), 2000),
                    "E":(FailureFunction(params = (1.2, 1230)),1,("OUT",), 2000),
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

    if False: #Plot Tests
        
        Test2 = System(PARALLEL_TEST)
        Test2.disp()
        plt.title("Expected Impact for PARALLEL_TEST")
        plt.xlabel("Time")
        plt.ylabel("Efficiency")
        plt.plot([x/10 for x in range(300)], [Test2.sample_reliability(x/10) for x in range(300)])
        
        HotwireTest = System(HOTWIRE_TEST)
        HotwireTest.disp()
        print("This system is the system from the webpage: https://weibull.com/hotwire/issue3/hottopics3.htm")
        print("The page also has a table of results at the bottom that are the values they got")
        print("The values from the table matched to the values from this model:")
        reliabilites = [1,0.9950,0.9748,0.9374,0.8823,0.8184,0.7419,0.6621,0.5816,0.5038,0.4332,0.3683,0.3087,0.2565,0.2121,0.1738]
        for i,n in enumerate(reliabilites):
            print("t = ", i*100, "their value = ", n, "our values = ", HotwireTest.sample_reliability(i*100))

        Test3 = System(COMPLEXISH_TEST)
        Test3.disp()
        plt.title("Expected Impact for COMPLEXISH_TEST")
        plt.xlabel("Time")
        plt.ylabel("Efficiency")
        plt.plot([x/10 for x in range(300)], [Test3.sample_reliability(x/10) for x in range(300)])
    
    PARALLEL_CONST = {"IN":(None, 1, ("A","B","C","D"), 0),
                     "A":(FailureFunction(choose = "Constant", params = (0.3,1)),  1, ("OUT",), 1),
                     "B":(FailureFunction(choose = "Constant", params = (0.2,1)),  1, ("OUT",), 1),
                     "C":(FailureFunction(choose = "Constant", params = (0.1,1)),  1, ("OUT",), 1),
                     "OUT":(None, 1, (), 0)}

    SERIES_CONST = {"IN":(None, 1, ("A","B","C","D"), 0),
                     "A":(FailureFunction(choose = "Constant", params = (0.5,1)),  1, ("B",), 1),
                     "B":(FailureFunction(choose = "Constant", params = (0.2,1)),  1, ("C",), 1),
                     "C":(FailureFunction(choose = "Constant", params = (0.1,1)),  1, ("OUT",), 1),
                     "OUT":(None, 1, (), 0)}
    
    COMPLEX_CONST = {"IN":(None, 1, ("A","B"), 0),
                    "A":(FailureFunction(choose = "Constant", params = (0.5,1)),1,("C","D"), 1),
                    "B":(FailureFunction(choose = "Constant", params = (0.5,1)),1,("C","E"), 1),
                    "C":(FailureFunction(choose = "Constant", params = (0.5,1)),1,("D","E"), 1),
                    "D":(FailureFunction(choose = "Constant", params = (0.5,1)),1,("OUT",), 1),
                    "E":(FailureFunction(choose = "Constant", params = (0.5,1)),1,("OUT",), 1),
                    "OUT":(None, 1, (), 0)}

    if False:# Constant Tests
        Contst_Test1 = System