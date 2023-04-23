import sys
sys.path.append('/home/roy/cwnd_clgo_classifier')
#sys.path.append('/home/roy/cwnd_clgo_classifier/simulation')
print(sys.path)
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

from matplotlib import cycler, gridspec

import simulation.tcpdump_statistics
#from simulation.tcpdump_statistics import TcpdumpStatistics


'''def time_str_to_timedelta(time_str):
    my_time = datetime.strptime(time_str, "%H:%M:%S.%f")
    my_timedelta = my_time - datetime(1900, 1, 1)
    return my_timedelta'''


def get_delta(curr_timedelta, base_timedelta):
    """Get Seconds from time."""
    return (curr_timedelta - base_timedelta).seconds + (curr_timedelta - base_timedelta).microseconds / 1000000



class SingleConnStatistics:
    def __init__(self, interval_accuracy, rtr_q_filename):
        self.conn_df = self.in_conn_df = self.out_conn_df = None
        self.interval_accuracy = interval_accuracy
        self.rtr_q_filename = rtr_q_filename

    def build_df(self):
        in_passed_df, in_dropped_df, in_retransmit_df = self.reduce_dropped_packets(self.in_conn_df)

        self.in_conn_df = self.remove_retransmissions(self.in_conn_df)
        self.out_conn_df = self.remove_retransmissions(self.out_conn_df)

        # Add timedelta to in and out conn DFs
        self.in_conn_df['Time'] = pd.to_timedelta(self.in_conn_df['date_time'])
        self.out_conn_df['Time'] = pd.to_timedelta(self.out_conn_df['date_time'])

        # If we want accurate capture time, we need to do it before we round times by interval accuracy
        capture_time_column_name = "Capture Time Gap"
        # calculate the packet arrival time difference
        # since we want to maintain the data based on time intervals, we should expect some intervals to include
        # a lot of packets, and others with only few of them.
        # It is hard to process such information, so we will
        # extract the maximal time gap between two sent packets for each interval.
        time_gap_series = self.in_conn_df['Time'].diff()
        time_gap_series = pd.to_numeric(time_gap_series)
        time_gap_series = time_gap_series.clip(lower=0)
        time_gap_series = time_gap_series/1000000 #convert from nano to milli
        #time_gap_series = time_gap_series.astype('int64')
        print('a')


        # Join it to th conn df
        time_gap_series.name = capture_time_column_name
        self.in_conn_df = self.in_conn_df.join(time_gap_series)

        # Round time by interval accuracy
        self.in_conn_df['date_time'] = self.in_conn_df['date_time'].map(
            lambda x: x[0:self.interval_accuracy - 6])
        self.out_conn_df['date_time'] = self.out_conn_df['date_time'].map(
            lambda x: x[0:self.interval_accuracy - 6])

        # Create a DF with all possible time ticks between min time to max time
        in_start_time = self.in_conn_df['date_time'].iloc[0]
        out_start_time = self.out_conn_df['date_time'].iloc[0]
        start_timedelta = min(in_start_time, out_start_time)
        millies = 10 ** (3 - self.interval_accuracy)
        tdi = pd.timedelta_range(start_timedelta, periods=10000, freq='%dL' % millies)
        self.conn_df = tdi.to_frame(name="Time")


        # Complete the capture delta time setup by getting the maximal value for each time slot
        capture_delta_df = self.in_conn_df.groupby(by=['date_time'], as_index=False)[['date_time', capture_time_column_name]].max()
        capture_delta_df['Time'] = pd.to_timedelta(capture_delta_df['date_time'])
        capture_delta_df = capture_delta_df.drop(columns=['date_time'])
        self.conn_df = pd.merge(self.conn_df, capture_delta_df, on='Time', how='left')
        #self.conn_df = self.conn_df.join(capture_delta_df[capture_time_column_name])

        self.count_throughput(self.in_conn_df, 'In Throughput')
        self.count_throughput(self.out_conn_df, 'Out Throughput')
        #self.count_throughput(in_passed_df, 'In Goodput')



        # Calculate CBIQ
        in_temp_df = self.create_seq_df(self.in_conn_df, 'in_seq_num')
        self.join_time_df(in_temp_df, 'date_time')
        out_temp_df = self.create_seq_df(self.out_conn_df, 'out_seq_num')
        self.join_time_df(out_temp_df, 'date_time')
        #temp_df = in_temp_df.merge(out_temp_df, how='inner', on=['date_time'])
        #temp_df = temp_df.set_index('date_time')
        self.conn_df['CBIQ'] = self.conn_df['in_seq_num'] - self.conn_df['out_seq_num']
        self.conn_df = self.conn_df.drop(columns=['in_seq_num', 'out_seq_num'])

        self.count_ts_val(self.out_conn_df, "Send Time Gap")
        # ts_val_df = self.create_ts_val_df(in_conn_lines, self.interval_accuracy)

        self.conn_df.index.name = 'Time'

        # The gap between the total in and the total out indicates what's in the queue. We want to convert form
        # Mbps to Bytes

        if self.rtr_q_filename is not None:
            # Add qdisc columns, only for existing keys (inner join)
            qdisc_df = pd.read_csv(self.rtr_q_filename, sep="\t", header=None)
            qdisc_df.columns = ['Time', 'Total Bytes in Queue', 'Num of Packets', 'Num of Drops']
            reference_start_time = qdisc_df['Time'][0]
            qdisc_df = qdisc_df.drop_duplicates(subset=['Time'],keep='last')
            qdisc_df['Time'] = pd.to_timedelta(qdisc_df['Time'])
            qdisc_df = qdisc_df.set_index('Time')
            self.conn_df = self.conn_df.join(qdisc_df, lsuffix='_caller')
            self.conn_df = self.conn_df.fillna(method='ffill')
        else:
            reference_start_time=self.conn_df['Time'][0]

        # Convert the time string into time offset float
        #self.conn_df['timestamp'] = self.conn_df['Time'].map(lambda x: get_delta(x, self.conn_df['Time'][0]))
        self.conn_df['timestamp'] = self.conn_df['Time'].map(lambda x: get_delta(x, reference_start_time))
        self.conn_df = self.conn_df.set_index('timestamp')
        self.conn_df = self.conn_df.drop(columns=['Time'])

        # Fill all Nan with 0 (we don't know anything better for what's left)
        self.conn_df = self.conn_df.fillna(0)

        return

    def remove_retransmissions(self, conn_df):
        # Remove retransmissions
        for n in range(100):
            t_series = conn_df['seq_num'].diff()
            t_series.fillna(0)
            if t_series.min() >=0:
                break
            conn_df = conn_df.join(t_series,rsuffix='_diff')
            conn_df = conn_df.drop(conn_df[conn_df['seq_num_diff'] < 0].index)
            conn_df = conn_df.drop(columns=['seq_num_diff'])
        return conn_df


    def join_time_df(self, time_df, time_col_name):
            time_df['Time'] = pd.to_timedelta(time_df[time_col_name])
            self.conn_df = pd.merge(self.conn_df, time_df, on='Time', how='left')
            self.conn_df = self.conn_df.fillna(method='ffill')
            self.conn_df = self.conn_df.drop(columns=['date_time'])



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
        bytes_per_timeslot_df = conn_df.groupby(by=['date_time'], as_index=False)[['date_time', 'length']].sum()
        bytes_per_timeslot_df['Time'] = pd.to_timedelta(bytes_per_timeslot_df['date_time'])
        bytes_per_timeslot_df = bytes_per_timeslot_df.drop(columns=['date_time'])
        self.conn_df = pd.merge(self.conn_df, bytes_per_timeslot_df, on='Time', how='left')
        #self.conn_df = self.conn_df.join(bytes_per_timeslot_df)
        self.conn_df = self.conn_df.rename(columns={"length": column})
        # Translate from Bytes per time tick to Mbps
        self.conn_df[column] = self.conn_df[column].map(lambda num: num * 8 / 10 ** (6 - self.interval_accuracy))
        values = {column: 0}
        self.conn_df = self.conn_df.fillna(value=values)

    def create_seq_df(self, conn_df, col_name):
        temp_df = conn_df.drop_duplicates(subset=["date_time"],keep='first')
        temp_df = temp_df[['date_time', 'seq_num']]
        temp_df.columns = ['date_time', col_name]
        return temp_df

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


class OnlineSingleConnStatistics(SingleConnStatistics):
    def __init__(self, in_df = None, out_df=None, in_file=None, out_file=None, interval_accuracy=3, rtr_q_filename=None):
        super().__init__(interval_accuracy, rtr_q_filename)

        # Either in/out DF or in/out files should be filled. We trus the code and don't check
        if in_file:
            self.in_conn_df = pd.read_csv(in_file, sep=",")
            self.out_conn_df = pd.read_csv(out_file, sep=",")
        else:
            self.in_conn_df = in_df
            self.out_conn_df = out_df

        self.in_conn_df = self.in_conn_df.sort_values(by=['date_time'])
        self.out_conn_df = self.out_conn_df.sort_values(by=['date_time'])
        self.build_df()


if __name__ == '__main__':
    intv_accuracy = 3
    abs_path = "/tmp/8.25.2021@10-51-48_aaa"
    in_file = abs_path + "/1629877918_167772161_64502_167772417_5201_3.csv"
    out_file = abs_path + "/1629877918_167772161_64502_167772417_5201_4.csv"
    q_line_obj = OnlineSingleConnStatistics(in_file=in_file, out_file=out_file, interval_accuracy= intv_accuracy, rtr_q_filename=None)
    q_line_obj.conn_df.to_csv(abs_path + '/single_connection_stat_debug.csv')

