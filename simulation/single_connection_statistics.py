import re
import sys
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

from matplotlib import cycler, gridspec

from simulation.tcpdump_statistics import TcpdumpStatistics


def time_str_to_timedelta(time_str):
    my_time = datetime.strptime(time_str, "%H:%M:%S.%f")
    my_timedelta = my_time - datetime(1900, 1, 1)
    return my_timedelta


def get_delta(curr_timedelta, base_timedelta):
    """Get Seconds from time."""
    return (curr_timedelta - base_timedelta).seconds + (curr_timedelta - base_timedelta).microseconds / 1000000


def parse_ip_port(ipp_str):
    # Auxiliary function to separate the IP from the port in tcpdump parsing:
    search_obj = re.search(r'(\S+)\.(\d+)$', ipp_str)
    if search_obj:
        return search_obj.group(1), search_obj.group(2)
    else:
        return None


def parse_seq_line(line):
    # Parse a single line from TCP dump file, return important values only
    # The method parses only lines with TCP data, than include seq key
    # Example of a single line:
    # 21:00:32.248252 IP 10.0.2.10.54094 > 10.0.3.10.5203: Flags [P.], seq 1:38, ack 1, win 83, options [nop,nop,TS val 3161060119 ecr 3216167312], length 37
    # search_obj = re.search(r'(\S+) IP (\S+) > (\S+): Flags.* length (\d+)', line)
    search_obj = re.search(r'(\S+) IP (\S+) > (\S+): Flags.* seq (\d+):.*TS val (\d+) .* length (\d+)', line)
    if search_obj is None:
        return '0', '0', '0', '0', '0'

    # Extract the interesting variables:
    time_str = search_obj.group(1)
    src_ip_port = search_obj.group(2)
    src_ip, src_port = TcpdumpStatistics.parse_ip_port(src_ip_port)
    dst_ip_port = search_obj.group(3)
    dst_ip, dst_port = TcpdumpStatistics.parse_ip_port(dst_ip_port)
    seq_num = search_obj.group(4)
    ts_val = search_obj.group(5)
    throughput = search_obj.group(6)

    if all(v is not None for v in [src_ip, src_port, dst_ip, dst_port]):
        # Look for the dictionary element. If it does not exist, create one
        conn_index = TcpdumpStatistics.get_connection_identifier(src_ip, src_port, dst_ip, dst_port)
        return conn_index, time_str, throughput, ts_val, seq_num
    else:
        return '0', '0', '0', '0', '0'


class SingleConnStatistics:
    def __init__(self, ingress_file_name, egress_file_name, rtr_q_filename, graph_file_name, plot_title,
                 generate_graphs, interval_accuracy):
        self.conn_df = self.rolling_df = None
        self.interval_accuracy = interval_accuracy

        self.build_df(ingress_file_name, egress_file_name, rtr_q_filename)
        # print(self.conn_df)
        # self.create_plots(graph_file_name)
        if generate_graphs:
            self.create_plots(graph_file_name, plot_title)

    def build_df(self, ingress_file_name, egress_file_name, rtr_q_filename):

        # Parse inbound file. Extract dropped packets and passed packets for the connection
        file = open(ingress_file_name, 'r')
        lines = file.readlines()
        in_conn_df = self.build_conn_df(lines)  # take out all the lines that are not related to the connection
        in_passed_df, in_dropped_df, in_retransmit_df = self.reduce_dropped_packets(in_conn_df)

        # Parse outbound file. Extract passed packets for the connection
        file = open(egress_file_name, 'r')
        lines = file.readlines()
        out_conn_df = self.build_conn_df(lines)  # take out all the lines that are not related to the connection

        # Create a DF with all possible time ticks between min time to max time
        in_start_time = in_conn_df['date_time'].iloc[0]
        in_end_time = in_conn_df['date_time'].iloc[-1]
        out_start_time = out_conn_df['date_time'].iloc[0]
        out_end_time = out_conn_df['date_time'].iloc[-1]
        start_timedelta = min(in_start_time, out_start_time)
        end_timedelta = max(in_end_time, out_end_time)
        millies = 10 ** (3 - self.interval_accuracy)
        tdi = pd.timedelta_range(start_timedelta, end_timedelta, freq='%dL' % millies)
        self.conn_df = tdi.to_frame(name="Time")
        # Create several DataFrames from the lines

        self.count_throughput(in_conn_df, 'In Throughput')
        self.count_throughput(out_conn_df, 'Out Throughput')
        self.count_throughput(in_passed_df, 'In Goodput')
        self.count_dropped_packets(in_dropped_df, 'Connection Num of Drops')
        self.count_retransmit_packets(in_retransmit_df, 'Connection Num of Retransmits')
        self.count_ts_val(out_conn_df, "Send Time Gap")
        # ts_val_df = self.create_ts_val_df(in_conn_lines, self.interval_accuracy)

        # Consolidate all the DataFrames into one DataFrame
        # self.conn_df = pd.concat([in_throughput_df, out_throughput_df, dropped_df, ts_val_df],
        #                         axis=1)  # Outer join between in and out df
        self.conn_df.index.name = 'Time'
        # Create the Byte in Queue column
        # Add Total column that indicates the number of bytes passed so far
        in_total_series = self.conn_df['In Throughput'].cumsum()
        out_total_series = self.conn_df['Out Throughput'].cumsum()
        in_goodput_series = self.conn_df['In Goodput'].cumsum()
        data = {'In Total': in_total_series,
                'Out Total': out_total_series,
                'Goodput Total':in_goodput_series}
        temp_df = pd.concat(data, axis=1)
        temp_df['CBIQ'] = temp_df['Goodput Total'] - temp_df['Out Total']
        temp_df['CBIQ'] = temp_df['CBIQ'].map(lambda num: int(num / 8 * 10 ** (6 - self.interval_accuracy)))
        temp_df = temp_df.drop(columns=['Goodput Total'])
        self.conn_df = self.conn_df.join(temp_df)
        self.conn_df = self.conn_df.drop(columns=['In Goodput', 'In Total', 'Out Total'])
        # The gap between the total in and the total out indicates what's in the queue. We want to convert form
        # Mbps to Bytes

        # Add qdisc columns, only for existing keys (inner join)
        try:
            qdisc_df = pd.read_csv(rtr_q_filename, sep="\t", header=None)
        except:
            print ("ERROR: No qdisc file. Terminating!!!")
            sys.exit()

        qdisc_df.columns = ['Time', 'Total Bytes in Queue', 'Num of Packets', 'Num of Drops']
        qdisc_df['Time'] = qdisc_df['Time'].map(lambda time_str: time_str_to_timedelta(time_str))
        qdisc_df = qdisc_df.set_index('Time')
        self.conn_df = self.conn_df.join(qdisc_df, lsuffix='_caller')
        self.conn_df = self.conn_df.fillna(method='ffill')

        # Convert the time string into time offset float
        self.conn_df['timestamp'] = self.conn_df['Time'].map(lambda x: get_delta(x, self.conn_df['Time'][0]))
        self.conn_df = self.conn_df.set_index('timestamp')
        self.conn_df = self.conn_df.drop(columns=['Time'])

        # Fill all Nan with 0 (we don't know anything better for what's left)
        self.conn_df = self.conn_df.fillna(0)

        return

    def count_ts_val(self, conn_df, column):
        # TS val indicates the timestamp in which the packet was sent.
        # since we want to maintain the data based on time intervals, we should expect some intervals to include
        # a lot of packets, and others with only few of them.
        # It is hard to process such information, so we will
        # extract the maximal time gap between two sent packets for each interval.

        # Create diff df first, with delta between ts_vals (this is the time gap
        time_gap_df = pd.DataFrame(conn_df['ts_val'].diff())
        time_gap_df.fillna(0)

        # Join it to th conn df
        time_gap_df = time_gap_df.rename(columns={"ts_val": column})
        conn_df = conn_df.join(time_gap_df)

        # Take the maximal value for each time slot
        bytes_per_timeslot_df = pd.DataFrame(conn_df.groupby('date_time')[column].max())
        self.conn_df = self.conn_df.join(bytes_per_timeslot_df[column])


    def count_throughput(self, conn_df, column):
        bytes_per_timeslot_df = pd.DataFrame(conn_df.groupby('date_time')['length'].sum())
        self.conn_df = self.conn_df.join(bytes_per_timeslot_df)
        self.conn_df = self.conn_df.rename(columns={"length": column})
        self.conn_df[column] = self.conn_df[column].map(lambda num: num * 8 / 10 ** (6 - self.interval_accuracy))
        values = {column: 0}
        self.conn_df = self.conn_df.fillna(value=values)

    def count_dropped_packets(self, dropped_df, column):
        drop_count_df = pd.DataFrame(dropped_df['date_time'].value_counts())
        self.conn_df = self.conn_df.join(drop_count_df)
        self.conn_df = self.conn_df.rename(columns={"date_time": column})
        values = {column: 0}
        self.conn_df = self.conn_df.fillna(value=values)

    def count_retransmit_packets(self, ret_df, column):
        ret_count_df = pd.DataFrame(ret_df['date_time'].value_counts())
        self.conn_df = self.conn_df.join(ret_count_df)
        self.conn_df = self.conn_df.rename(columns={"date_time": column})
        values = {column: 0}
        self.conn_df = self.conn_df.fillna(value=values)

    def build_conn_df(self, lines):
        conn_list = []
        # Take out all lines with length 0
        conn_count = {}
        for line in lines:
            # Ignore if length is 0
            if int(line.find('length 0')) > 0:  # ACK only, ignore
                continue
            conn_index, time_str, length_str, ts_val, seq_num = parse_seq_line(line)
            if time_str == '0':
                continue
            dtime = datetime.strptime(time_str[0:self.interval_accuracy - 6], "%H:%M:%S.%f") - datetime(1900, 1, 1)
            conn_list.append([conn_index, dtime, int(length_str), int(ts_val), seq_num])

        df = pd.DataFrame(conn_list, columns=['conn_index', 'date_time', 'length', 'ts_val', 'seq_num'])
        # extract the connection index
        our_conn_index = df.conn_index.mode()[0]

        # our_conn_index = max(conn_count, key=conn_count.get)
        df = df.loc[df['conn_index'] == our_conn_index]

        return df

        # 09:17:58.297429 IP 10.0.1.10.44848 > 10.0.10.10.5202: Flags [.], seq 1486:2934, ack 1, win 83, options [nop,nop,TS val 4277329349 ecr 645803186], length 1448

    @staticmethod
    def reduce_dropped_packets(conn_df):
        # The method assumes single connection. If lines are from multiple connections, two messages
        # from two different connections with the same seq number will be interpreted as retransmissions
        # If data was sent multiple times, the method keeps only the last retransmission.
        # The method assumes that add df records represent packets with data

        # There is a pd command to filter out duplicates, keeping the last instance
        passed_df = conn_df.drop_duplicates(subset='seq_num', keep='last')

        # Find the items that represent drops, and keep them in a separate df
        dups_series = conn_df.duplicated(subset='seq_num', keep='last')
        dups_only = dups_series[dups_series == True]
        fdf = pd.DataFrame(dups_only).join(conn_df)
        dropped_df = fdf.drop(columns=[0])

        # Find the items that represent retransmissions, and keep them in a separate df
        dups_series = conn_df.duplicated(subset='seq_num', keep='first')
        dups_only = dups_series[dups_series == True]
        fdf = pd.DataFrame(dups_only).join(conn_df)
        retransmit_df = fdf.drop(columns=[0])



        return passed_df, dropped_df, retransmit_df

    def create_plots(self, graph_file_name, plot_title):

        fig2 = plt.figure(constrained_layout=True, figsize=(10, 10))
        fig2.suptitle(plot_title)
        spec2 = gridspec.GridSpec(ncols=1, nrows=3, figure=fig2)
        throughput_ax = fig2.add_subplot(spec2[0, 0])
        q_disc_ax = fig2.add_subplot(spec2[1, 0])
        ts_ax = fig2.add_subplot(spec2[2, 0])
        # max_ax = fig2.add_subplot(spec2[1, 1])
        # f2_ax3 = fig2.add_subplot(spec2[1, 0])
        # f2_ax4 = fig2.add_subplot(spec2[1, 1])

        # fig, (throughput_ax, q_disc_ax) = plt.subplots(2, figsize=(10, 10))

        self.conn_df.plot(kind='line', ax=throughput_ax, y=['In Throughput', 'Out Throughput'],
                          title="Throughput vs. Bytes in Queue")
        throughput_ax.legend(loc=2)
        throughput_ax.set(xlabel='time', ylabel='Throughput (Mbps)')
        throughput_ax.grid()
        ax4 = throughput_ax.twinx()  # instantiate a second axes that shares the same x-axis.
        cm = cycler('color', 'r')
        ax4.set_prop_cycle(cm)
        ax4.set(xlabel='time', ylabel='Bytes')
        self.conn_df.plot(kind='line', ax=ax4, y=['CBIQ'])
        ax4.legend(loc=1)

        self.conn_df.plot(kind='line', ax=q_disc_ax, y=['Connection Num of Drops'], color="red")
        q_disc_ax.set(xlabel='time', ylabel='Drops (pkts)')
        q_disc_ax.grid()
        q_disc_ax.legend(loc=2)
        ax5 = q_disc_ax.twinx()  # instantiate a second axes that shares the same x-axis.
        ax5.set(ylabel='Bytes')
        self.conn_df.plot(kind='line', ax=ax5, y=['CBIQ'],
                          title="Drops vs. Bytes in Queue")
        ax5.legend(loc=1)

        # self.max_cbiq_series.plot(kind='line', ax=max_ax, c='g')
        # self.rolling_df.plot(kind='line', ax=max_ax, c='g', y=['CBIQ'])

        self.conn_df.plot(kind='line', ax=ts_ax, y=['Connection Num of Drops'], color="red")
        ts_ax.set(xlabel='time', ylabel='Drops (pkts)')
        ts_ax.grid()
        ts_ax.legend(loc=2)
        ax6 = ts_ax.twinx()  # instantiate a second axes that shares the same x-axis.
        ax6.set(ylabel='msec')
        self.conn_df.plot(kind='line', ax=ax6, y=['Send Time Gap'],
                          title="Drops vs. Send Time Gap")
        ax6.legend(loc=1)

        plt.savefig(graph_file_name)
        plt.show(block=False)


if __name__ == '__main__':
    interval_accuracy = 3
    generate_graphs = False
    plot_title = "kuku"
    test_name = sys.argv[1]
    host_name = sys.argv[2]
    abs_path = "/home/another/PycharmProjects/cwnd_clgo_classifier/results/12.17.2020@21-0-27_1_reno_1_bbr_1_cubic"
    in_file = abs_path + "/client_cubic_2.txt"
    out_file = abs_path + "/server_cubic_2.txt"
    rtr_file = abs_path + "/rtr_q.txt"
    graph_file_name = abs_path + "BIQ_2.png"
    q_line_obj = SingleConnStatistics(in_file, out_file, rtr_file, graph_file_name, plot_title, generate_graphs,
                                      interval_accuracy)
    q_line_obj.conn_df.to_csv(abs_path + "/single_connection_stat_2.csv")
