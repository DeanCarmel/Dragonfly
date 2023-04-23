import re


class TcpdumpStatistics:
    def __init__(self, port_algo_dict, interval_accuracy):

        '''
        2D Dictionary with amount of transferred data in each cell
        The time column will be the x axis.
        if no data passed for a connection in a specific slot, 0 will be marked
        Time                conn_1          conn_2          conn_3
        ----                ------          ------          ------
        start_time          throughput      throughput      throughput
        start_time+0.1      throughput      throughput      throughput
        start_time+0.2      throughput      throughput      throughput
        '''
        self.throughput_dict_of_dicts = {}
        self.ts_val_dict_of_lists = {}
        self.last_ts_val_dict = {}
        self.port_algo_dict = port_algo_dict
        self.interval_accuracy = interval_accuracy

    @staticmethod
    def get_connection_identifier(src_addr, src_port, dst_addr, dst_port, port_algo_dict={}):
        # Check if we can tell the used algo (we should):
        if int(src_port) in port_algo_dict.keys():
            algo_str = port_algo_dict[int(src_port)] + '_'
        elif int(dst_port) in port_algo_dict.keys():
            algo_str = port_algo_dict[int(dst_port)] + '_'
        else:
            algo_str = ''
        # Determine a unique key string for the connection:
        return "%s%s_%s_%s_%s" % (algo_str, src_addr, src_port, dst_addr, dst_port)

    @staticmethod
    def parse_ip_port(ipp_str):
        # Auxiliary function to separate the IP from the port in tcpdump parsing:
        search_obj = re.search(r'(\S+)\.(\d+)$', ipp_str)
        if search_obj:
            return search_obj.group(1), search_obj.group(2)
        else:
            return None

    @staticmethod
    def parse_line(line, port_algo_dict={}):
        # Parse a single line from TCP dump file, return important values only:
        # Example of a single line:
        # 13:53:23.615538 IP tcpip.48286 > 10.0.8.10.5205: Flags [.], ack 1, win 83, options [nop,nop,TS val 3487210525 ecr 3732313601], length 0
        # search_obj = re.search(r'(\S+) IP (\S+) > (\S+): Flags.* length (\d+)', line)
        search_obj = re.search(r'(\S+) IP (\S+) > (\S+): Flags.*TS val (\d+) .* length (\d+)', line)
        if search_obj is None:
            return '0', '0', '0', '0'

        # Extract the interesting variables:
        time_str = search_obj.group(1)
        src_ip_port = search_obj.group(2)
        src_ip, src_port = TcpdumpStatistics.parse_ip_port(src_ip_port)
        dst_ip_port = search_obj.group(3)
        dst_ip, dst_port = TcpdumpStatistics.parse_ip_port(dst_ip_port)
        ts_val = search_obj.group(4)
        throughput = search_obj.group(5)

        if all(v is not None for v in [src_ip, src_port, dst_ip, dst_port]):
            # Look for the dictionary element. If it does not exist, create one
            conn_index = TcpdumpStatistics.get_connection_identifier(src_ip, src_port, dst_ip, dst_port, port_algo_dict)
            return conn_index, time_str, throughput, ts_val
        else:
            return '0', '0', '0', '0'

    def parse_tcpdump_file(self, file_name):
        # Parse a tcpdump file, line by line:
        file1 = open(file_name, 'r')
        lines = file1.readlines()

        count = 0
        # Strips the newline character
        for line in lines:
            conn_index, time_str, throughput, ts_val = self.parse_line(line, self.port_algo_dict)
            if int(throughput) == 0:  # ACK only, ignore
                continue

            ##### Process throughput:
            # For throughput, round the time according to interval accuracy:
            s_str = '(\S+\.\d{%d})' % self.interval_accuracy
            rounded_time_obj = re.search(r'%s' % s_str, time_str)
            rounded_time = rounded_time_obj.group(1)

            # If needed, add an entry for the connection (a new column):
            if not conn_index in self.throughput_dict_of_dicts:
                conn_throughput_dict = {}
                self.throughput_dict_of_dicts[conn_index] = conn_throughput_dict

            # If needed, add a value for the specific time (a new cell):
            if not rounded_time in self.throughput_dict_of_dicts[conn_index]:
                self.throughput_dict_of_dicts[conn_index][rounded_time] = 0

            self.throughput_dict_of_dicts[conn_index][rounded_time] += int(throughput)

            #### Process TS Val:
            if not conn_index in self.ts_val_dict_of_lists:
                ts_val_list = []
                self.ts_val_dict_of_lists[conn_index] = ts_val_list
                self.last_ts_val_dict[conn_index] = float(ts_val)  # Initialize the first element:
            self.ts_val_dict_of_lists[conn_index].append(float(ts_val) - self.last_ts_val_dict[conn_index])
            self.last_ts_val_dict[conn_index] = float(ts_val)
