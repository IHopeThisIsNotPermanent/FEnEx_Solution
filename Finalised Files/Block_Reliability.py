import csv
import numpy as np
import itertools

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
                
            block_list[(label, component["BlockID"])].append((component["Component"], Cap, POF))
        
        self.system = System(block_list)
        

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
    
    def sample_total_throughput(self, failures):
        """
        Takes around 1.2 seconds to complete 100000 calcultions

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
        
        

    def sample_IOF(self, failures):
        """
        Parameters
        ----------
        failures : (binary)
            the binary of which machines are offline or not, in order of when they appear in the block_list

        Returns
        -------
        The expected impact to throughput due to failure

        """
        
        mask = failures
        vals = np.multipy(mask, self.machine_values)



if __name__ == "__main__":
    test = handle_csv()





