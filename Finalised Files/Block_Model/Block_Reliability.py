import csv
import numpy as np
import itertools
import math

def srt(x):
    x.sort()
    return x

def int2bin(n, length):
    if n == 0:
        m = 1
    else:
        m = n
    return [0,]*(length-math.ceil(math.log(m+1)/math.log(2)))+[int(x) for x in str(bin(n))[2:]]

class handle_csv:
    """
    Handle csv is the class used to handle the input and output of the csv files that represent the block systems
    
    """
    def __init__(self, filename = 'example_model.csv'):
        """
        

        Parameters
        ----------
        filename : string, optional
            the file name or path to the csv file you wish to load. The default is 'example_model.csv'.

        Returns
        -------
        None.

        """
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
            The entries must be ordered as they are connected.
        """
        
        self.block_list = block_list
        
        #this array contains the two important parameters for each machine, indexed at the index of the machine
        self.machine_values = np.array([list(itertools.chain.from_iterable([[machine[1] for machine in self.block_list[block]] for block in self.block_list])), #Capacity
                                        list(itertools.chain.from_iterable([[machine[2] for machine in self.block_list[block]] for block in self.block_list]))])#POF
        
        # This section of code sets up the windows used in the sample_total_throughput function
        
        # The way these work is like so, if we take the example_model, and line up all its machines you get this:
        
        #OHP1, Ship_loader_1, Stacker_1, Stacker_2, Stacker_3, Stockpile_1, Relcaimer_1, Reclaimer_2, Reclaimer_3, Sink_1
        
        #We want to start by summing up the capacities of each of the blocks, so we do that with the R1_sum_index windows, this will create a list of 
        #different length, which we need to keep in mind, the windows for this will be:
            
        #R1_sum_blocks = [[0,1],[1,2],[2,5],[5,6],[7,9],[9,10]]
        
        #we then need to find the minimum of each chain of blocks, there are 4 chains here, the first is OHP1, the second is the shiploader chain, 
        #the third is the stacker, stockpile, reclaimer chain, and the third is the sink chain. R1_min_blocks finds the ranges of blocks we need to 
        #min for this, in this example the windows for this will be: 
            
        #R1_min_blocks = [[0,1],[1,2],[2,5],[5,6]]
        
        #Because the output of the two chains that run parallel when a skip is occuring need to be recombined at the other side, we then need to sum these two
        #chains together, so the windows in this example will be: 
            
        #R2_sum_blocks = [[0,1],[1,3],[3,4]]
        
        #we then find the min of these blocks to get the output of the system
        
        
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
        
        #Block reliability distribution is a map that maps block and configuration to the output distribution. 
        
        #for example, you may have a block called "Stacker_Block_1", and it has 5 machines, and each one has a %50 of functioning, and a capacity of 1
        #and we have taken out the first and last machine for maintainence, to get the output distribution we would use: 
        #self.block_reliability_dist[""Stacker_Block_1""][(0,1,1,1,0)].
        #in this case it will return : {0: 0.125, 1: 0.375, 2: 0.375, 3: 0.125,}
        #the way you read this map, is the key is the throughput of the block, and the value is probability of that throughput
        
        self.block_reliability_dist = {}
        
        for block in self.block_list:
            if block[0] == "Skip End":
                self.block_reliability_dist[block[1]+"_end"] = {(0,) : {0.0: 1.0}}
                continue
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
        """
        This function is used to calcualte the throughput of two throughput distributions in parallel, being combined

        Parameters
        ----------
        dist_1 : map
            the first throughput distirbution 
        dist_2 : map
            the second throughput distirbution 

        Returns
        -------
        Options : map
            the resulting throughput distribution

        """
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
        """
        This function is used to calcualte the throughput of two throughput distributions in series

        Parameters
        ----------
        dist_1 : map
            the first throughput distirbution 
        dist_2 : map
            the second throughput distirbution 

        Returns
        -------
        Options : map
            the resulting throughput distribution

        """
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
        Sample reliability returns the throughput distribution, given a failures list.
        
        runs 100000 iterations in 2.25 seconds with the basic model (10 machines)
        runs 100000 iterations in 37.68 deconds for the more complex model (41 machines)
        runs 100000 iterations in 167.33 seconds for the even more complex model (83 machines)
        
        If this becomes an issue there is another way of doing this that speeds it up for more complex examples.
        
        Parameters
        ----------
        failures : tuple(int)
            The list of failures/machines being repaired, 0 indicates that it is not currently in operation, and 1 otherwise.

        Returns
        -------
        map
            returns a map in the same format that block_reliability_dist has, where the keys are the throughput, and the value is the 
            probability of that throughput

        """
        
        #Options is just the slives of the failures that correspond to each block, so options[0] would return something like (1,0,1), which are is
        #the slice of the failues list that corresponds to the first blocks machines, of which in this case there are 3.
        
        options = []
        index = 0
        block_index = 0
        while index < len(self.machine_values[0]):
            nxt = len(self.block_list[list(self.block_list.keys())[block_index]])
            options.append(tuple(failures[index:index+nxt]))
            index += nxt
            block_index += 1
        
        #This algorithm works by keeping track of 3 paths, the main, the continuation, and the skip path.
        #If we are not currently up to a block which is either skipped over, or a skip block, we just use the 
        #following function to add the next block to the main path,
        #if we are in a skip block, we add it to the skip path, and if a block is currently being skipped over, we add
        #it to the continuation path.
        #if we get to the end of a skip path, we combine the two paths, then use the following function to add it back to the 
        #main path.
        
        Main_Path = self.block_reliability_dist[list(self.block_reliability_dist.keys())[0]][options[0]]
        Continuation = {}
        Continuation_Stockpiled = False
        Skip = {}
        Skip_Stockpiled = False
        Skipping = False
        
        for block_index, block in enumerate(list(self.block_list.keys())[1:]):
            
            if Skipping == True and block[0] == "Skip End": #if we reach the end of the skip 
                if Continuation_Stockpiled == False and Skip_Stockpiled == False:
                    Continuation = System.combine_operation(Continuation, Skip)
                    Main_Path = System.following_operation(Main_Path, Continuation)
                if Continuation_Stockpiled == True and Skip_Stockpiled == False:
                    Main_Path = System.following_operation(Main_Path, Skip)
                    Main_Path = System.combine_operation(Main_Path, Continuation)
                if Continuation_Stockpiled == False and Skip_Stockpiled == True:
                    Main_Path = System.following_operation(Main_Path, Continuation)
                    Main_Path = System.combine_operation(Main_Path, Skip)
                if Continuation_Stockpiled == True and Skip_Stockpiled == True:
                    Main_Path = System.combine_operation(Skip, Continuation)
                    
                Continuation = {}
                Continuation_Stockpiled = False
                Skip = {}
                Skip_Stockpiled = False
                Skipping = False
                
                continue
            
            block_index += 1
            nxt_dist = self.block_reliability_dist[block[1]][options[block_index]]
            
            if Skipping == False and block[0] != "Skip Start":
                if block[1][:9] == "Stockpile":
                    Main_Path = nxt_dist
                else:
                    Main_Path = System.following_operation(Main_Path, nxt_dist)
                    
            if block[0] == "Skip Start":
                if block[1][:9] == "Stockpile":
                    Skip_Stockpiled = True
                if Skipping == False:
                    Skip = nxt_dist
                if Skipping == True :
                    if block[1][:9] == "Stockpile":
                        Skip = nxt_dist
                    else:
                        Skip = System.following_operation(Skip, nxt_dist)
                Skipping = True
                        
            if Skipping == True and block[0] == "Block":
                if block[1][:9] == "Stockpile":
                    Continuation_Stockpiled = True
                if Continuation == {}:
                    Continuation = nxt_dist
                else:
                    if block[1][:9] == "Stockpile":
                        Continuation = nxt_dist
                    else:
                        Continuation = System.following_operation(Continuation, nxt_dist)
        return Main_Path

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
    #test2 = handle_csv("example_model2.csv")
    test3 = handle_csv("example_model3.csv")





