#Decomposition Method
from ReliabilityFunctions import *

class System:
    def __init__(self, node_info):
        """
        This class represents Complex Reliability Systems

        Parameters
        ----------
        node_info : dict
            a mapping of each node to their failfunc, failcount, contribution, node list
            node_info must contain "In":(None, None, 1,  (nodes connected to In))
                               and "Out":(None, None, 1, ())

        Returns
        -------
        None.

        """
        self.node_info = node_info
        
        #Determine the order, and count of each node for displaying
        for node in node_info:
            node_info[node] = list(node_info[node]) + [[0,1,1],]
        
        Queue = ["In",]
        NextQueue = []
        while Queue:
            for nxt in Queue:
                for check in nxt[3]:
                    Next_Queue.append(check)
                    node_info[check][4][0] = node_info[nxt][4][0] + 1

    
    def disp(self):
