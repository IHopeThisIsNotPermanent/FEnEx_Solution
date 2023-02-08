import csv
import numpy as np
import itertools
import math

from functools import lru_cache

def srt(x):
    x.sort()
    return x

def int2bin(n, length):
    if n == 0:
        m = 1
    else:
        m = n
    return [0,]*(length-math.ceil(math.log(m+1)/math.log(2)))+[int(x) for x in str(bin(n))[2:]]

class Binary_Operation_Tree:
    def __init__(self, operation, data, node_1, node_2 = None):
        self.operation = operation
        self.data = data
        self.node_1 = node_1
        self.node_2 = node_2
        
    def __str__(self):
        if self.node_2 is None:
            return "("+str(self.node_1)+")"
        
        else:
            return "("+ str(self.node_1) + {System.combine_operation:"V", System.following_operation:">"}[self.operation] + str(self.node_2) +")"
        
    def calculate(self, options):
        print(self.node_1, self.node_2, self.operation)
        if self.node_2 is None:
            return self.data[list(self.data.keys())[self.node_1]][options[self.node_1]]
        
        if type(self.node_1) == Binary_Operation_Tree:
            N1 = self.node_1.calculate(options)
        elif type(self.node_1) == int:
            N1 = self.data[list(self.data.keys())[self.node_1]][options[self.node_1]]
        else:
            N1 = self.node_1
        if type(self.node_2) == Binary_Operation_Tree:
                N2 = self.node_2.calculate(options)
        elif type(self.node_2) == int:
            N2 = self.data[list(self.data.keys())[self.node_2]][options[self.node_2]]
        else:
            N2 = self.node_2
        return self.operation(N1, N2)

class handle_csv:
    def __init__(self, filename = 'example_model.csv'):
        self.components = {}
        with open(filename, mode = 'r') as file:
            File = csv.reader(file)
            header = next(File)
            IDindex = header.index("Component")
            for line in File:
                self.components[line[IDindex]] = {}
                for field, value in zip(header, line):
                    self.components[line[IDindex]][field] = value
                    
        # set up the system from this information
        
        block_list = {}
        
        Skip_start = None
        Skip_end = None
        
        for component in self.components: #iterate through, and identify input, output, skips, and order of the components
            component = self.components[component]
        
            #checks if it is a skip
            label = "Block"
            if component["Skips_To"] != '':
                Skip_start = component["BlockID"]
                Skip_end = component["Skips_To"]
                label = "Skip Start"
                
            if component["BlockID"] == Skip_start:
                label = "Skip Start"
                
            if not Skip_end is None: 
                if component["BlockID"] == Skip_end:
                    block_list[("Skip End", Skip_start)] = []
            
            #figure out of there is POF, or capacity, if not remove entry
            POF = float("0"+component["Availability"])
            Cap = float("0"+component["Capacity"])
            
            if Cap == 0 or POF == 0:
                continue
            
            if not (label, component["BlockID"]) in block_list:
                block_list[(label, component["BlockID"])] = []
                
            block_list[(label, component["BlockID"])].append((component["Component"], Cap, 1-POF))
        
        self.system = System(block_list)
        
    def generate_throughput_table(self, depth, warning = False):
        """
        Parameters
        ----------
        depth : int
            for each layer, how many can be offline at any given time
        warning : boolean, OPTIONAL
            depending on the depth, and number of nodes, the operation may take a very long time,
            and/or create a very large file select true to get a warning of the time it will take.
            The default is False.

        Returns
        None.

        """
        

class System:
    def __init__(self, block_list):
        """
        Parameters
        ----------
        block_list : {map(list)}
            contains entries containing ("Block", "Block identifyer"): [(MachineID, Capacity, POF), ...]
            or
            tuples containing ("Skip Start", "Skip id") :[(MachineID, Capacity, POF), ...]
            with a corresponding ("Skip End", "Skip id") : [] when it ends
        """
        
        self.block_list = block_list
        
        self.machine_values = np.array([list(itertools.chain.from_iterable([[machine[1] for machine in self.block_list[block]] for block in self.block_list])), #Cap
                                        list(itertools.chain.from_iterable([[machine[2] for machine in self.block_list[block]] for block in self.block_list]))])#POF
        
        # This section of code sets up the windows used in the sample_total_throughput function
        
        self.R1_sum_blocks = [] 
        
        self.R1_min_blocks = [[0,]]
        
        self.R2_sum_blocks = [[0,]]
        
        
        R1_sum_index = 0
        R1_min_index = 0
        R2_sum_index = 0
        
        crt_skip = False
        skip_over = True
        
        for block in self.block_list:
            
            self.R1_sum_blocks.append((R1_sum_index, R1_sum_index + len(self.block_list[block])))
            
            R1_sum_index += len(self.block_list[block])
            R1_min_index += 1
            
            if block[0] in ("Skip Start","Skip End"):
                R2_sum_index += 1
                if len(self.R1_min_blocks[-1]) == 1:
                    self.R2_sum_blocks[-1].append(R2_sum_index)
                    self.R2_sum_blocks.append([R2_sum_index, ])
                    self.R1_min_blocks[-1].append(R1_min_index-1)
                    self.R1_min_blocks.append([R1_min_index-1,])
                else:
                    self.R1_min_blocks.append([R1_min_index-1,])
                if crt_skip == False:
                    crt_skip = block[1]
                    skip_over = False
                else:
                    crt_skip = False
                    
            elif skip_over == False:
                R2_sum_index += 1
                self.R1_min_blocks[-1].append(R1_min_index-1)
                self.R1_min_blocks.append([R1_min_index-1,])
                skip_over = True
        
        self.R1_sum_blocks.pop()
        self.R1_min_blocks.pop()
        self.R2_sum_blocks.pop()
        
        self.total_throughput_calced = False
        self.total_throughput = {}
        
        self.IOF_calced = False
        self.IOF = {}
        
        # This code sets up the block info for the sample_reliability function
        
        self.block_reliability_dist = {}
        
        for block in self.block_list:
            self.block_reliability_dist[block[1]] = {}
            machine_count = len(self.block_list[block])
            for configuration in range(2**machine_count):
                mask = tuple(int2bin(configuration, machine_count))
                self.block_reliability_dist[block[1]][mask] = {}
                new_selection = []
                for v, c in zip(self.block_list[block], mask):
                    if c == 0:
                        continue
                    new_selection.append((v[1], v[2]))
                for combination in range(2**len(new_selection)):
                    com_mask = int2bin(combination, len(new_selection))
                    new_val = sum(np.multiply(com_mask, [x[0] for x in new_selection]))
                    if not new_val in self.block_reliability_dist[block[1]][mask]: 
                        self.block_reliability_dist[block[1]][mask][new_val] = 0
                    self.block_reliability_dist[block[1]][mask][new_val] += np.prod(np.abs(np.array([x[1] for x in new_selection])-np.array(com_mask)))
        
        self.block_index = -1
        
        self.skip_ID = None
        
        self.operation_tree = self.construct_operation_tree()
        
    def prop_branch(self):
        
        return Binary_Operation_Tree(System.following_operation, self.block_reliability_dist, self.block_index, self.construct_operation_tree())
        
    def construct_operation_tree(self):
        #if we start a skip_chain
        
        print(self.block_index, self.skip_ID)
        
        #if we get to the end
        if not self.skip_ID is None:
            if list(self.block_list.keys())[self.block_index+1][0] == "Skip End":
                print("i should see this at block_index 13")
                self.skip_ID = None
                self.block_index += 1
                return Binary_Operation_Tree(None, self.block_reliability_dist, self.block_index-1)
        
        self.block_index += 1
        
        if self.block_index >= len(self.block_list)-1:
            return Binary_Operation_Tree(None, self.block_reliability_dist, self.block_index)
        
        
        
        if list(self.block_list.keys())[self.block_index][0] == "Skip Start" and self.skip_ID is None:
            self.skip_ID = list(self.block_list.keys())[self.block_index][1]
            #if it is a one block skip
            if list(self.block_list.keys())[self.block_index+1][0] != "Skip Start":
                print("i should see this")
                skip_branch = Binary_Operation_Tree(None, self.block_reliability_dist, self.block_index)
                self.block_index += 1
            else: #if it is not a one block skip
                print("i should never see this")
                skip_branch = self.prop_branch()
            if list(self.block_list.keys())[len(self.block_list)-1][0] == "Skip End": #if for some ungodly reason the final node is a skip end
                print("i should not see this")
                main_branch = self.prop_branch()
                self.skip_ID = None
                return Binary_Operation_Tree(System.combine_operation, self.block_reliability_dist, skip_branch, main_branch)
            
            main_branch = self.construct_operation_tree()
            continuation = self.construct_operation_tree()
            return Binary_Operation_Tree(System.following_operation, self.block_reliability_dist,
                                         Binary_Operation_Tree(System.combine_operation, self.block_reliability_dist, skip_branch, main_branch),
                                             continuation)
            
        if list(self.block_list.keys())[self.block_index][0] == "Skip Start" and not self.skip_ID is None:
            #if this is the last block
            if list(self.block_list.keys())[self.block_index+1][0] != "Skip Start":
                return Binary_Operation_Tree(None, self.block_reliability_dist, self.block_index)
            else:
                return self.prop_branch()
        
        return self.prop_branch()
            
        
        
        
        
        #Where > is follow operation, and V is combine operation, the basic example should be:
        #OHP1>(SHIP_LOADER V (STACKER>(STOCKPILE>RECLAIMER)))
        
        
    def sample_total_throughput(self, failures):
        """
        Takes around 1.2 seconds to complete 100000 iterations of the basic one (10 machines)
        Takes around 3.4 seconds to complete 100000 iterations of the more complex one (41 machines)
        We expect the complexity to increase linearly.

        Parameters
        ----------
        failures : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        mask = failures
        vals = [x * y for x,y in zip(mask, self.machine_values[0])]
        R1_sums = [sum(vals[window[0]:window[1]]) for window in self.R1_sum_blocks]
        R1_mins = [min(R1_sums[window[0]:window[1]]) for window in self.R1_min_blocks]
        R2_sums = [sum(R1_mins[window[0]:window[1]]) for window in self.R2_sum_blocks]
        
        return min(R2_sums)
        
    
        
    def combine_operation(dist_1, dist_2):
        Options = {}
        for M1 in dist_1:
            for M2 in dist_2:
                nxt = M1 + M2
                if not nxt in Options:
                    Options[nxt] = 0
                Options[nxt] += dist_1[M1]*dist_2[M2]
        Options = {x:Options[x] for x in srt(list(Options))}
        return Options
        
        
    def following_operation(dist_1, dist_2):
        Options = []
        total_min = min(max(dist_1), max(dist_2))
        for M1 in dist_1:
            if M1 > total_min:
                break
            Options.append(M1)
        for M2 in dist_2:
            if M2 > total_min:
                break
            if M2 in Options:
                continue
            Options.append(M2)
        Options = {x:0 for x in srt(Options)}
        for M1 in dist_1:
            for M2 in dist_2:
                if M1 == M2:
                    Options[M1] += dist_1[M1]*dist_2[M2]
                if M1 > M2:
                    Options[M2] += dist_1[M1]*dist_2[M2]
                if M2 > M1:
                    Options[M1] += dist_1[M1]*dist_2[M2]
        
        return Options

    def sample_reliability(self, failures):
        """
        runs 100000 iterations in 5.76 seconds with the basic model

        Parameters
        ----------
        failures : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        options = []
        index = 0
        block_index = 0
        while index < len(self.machine_values[0]):
            nxt = len(self.block_list[list(self.block_list.keys())[block_index]])
            options.append(tuple(failures[index:index+nxt]))
            index += nxt
            block_index += 1
        print(options)
        return self.operation_tree.calculate(options)
        

    def sample_POC(self, failures):
        """
        Parameters
        ----------
        failures : (binary)
            the binary of which machines are offline or not, in order of when they appear in the block_list

        Returns
        -------
        The probability that the system is in this configuration

        """
        
        mask = failures
        vals = np.abs(self.machine_values[1] - mask)
        return np.prod(vals)
        
    
        
        
if __name__ == "__main__":
    #test = handle_csv()
    test2 = handle_csv("example_model2.csv")





