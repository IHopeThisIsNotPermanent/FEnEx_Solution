



class System:
    def __init__(self, block_list):
        """
        Parameters
        ----------
        block_list : (tuple(tuple))
            contains tuples containing ("Block identifyer", (machine throughput, machine IOF), ...)
            or
            tuples containing ("Skip idetifyer", the index of the skip it ends/start at, (machine throughput, machine IOF)...)
        """
        
        self.block_list = block_list
        
        self.total_throughput_calced = False
        self.total_throughput = {}
        
        self.IOF_calced = False
        self.IOF = {}
        
    def calc_total_throughput(self):
        """
        Pre-calculates all the values for the total throughput

        Returns
        -------
        None.

        """
        
        if self.total_throughput_calced:
            return
        
    
        
        self.total_throughput_calced = True
        
    def calc_IOF(self):
        """
        

        Returns
        -------
        None.

        """
    
        if self.IOF_calced:
            return
    
        if not self.total_throughput_calced:
            self.calc_total_throughput()
            
        ### CODE HERE ###
            
        self.IOF_calced = True
    
    def sample_total_throughput(self, failures):
        """
        

        Parameters
        ----------
        failures : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """

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









