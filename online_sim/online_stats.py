import glob
import os
import re
import sys

# print(sys.path)
from pathlib import Path

sys.path.append('/home/another/PycharmProjects/cwnd_clgo_classifier')
import pandas as pd
from datetime import datetime


def time_str_to_timedelta(time_str):
    my_time = datetime.strptime(time_str, "%H:%M:%S.%f")
    my_timedelta = my_time - datetime(1900, 1, 1)
    return my_timedelta


def get_delta(curr_timedelta, base_timedelta):
    """Get Seconds from time."""
    return (curr_timedelta - base_timedelta).seconds + (curr_timedelta - base_timedelta).microseconds / 1000000


class MilliConnStat:
    def __init__(self, in_df=None, out_df=None, interval_accuracy=3, rtr_q_filename=None):
        self.in_conn_df = in_df
        self.out_conn_df = out_df
        self.conn_df = None
        self.interval_accuracy = interval_accuracy
        self.rtr_q_filename = rtr_q_filename

        self.build_df()

    def build_df(self):
        self.in_conn_df = self.in_conn_df.sort_values(by=['date_time'])
        self.out_conn_df = self.out_conn_df.sort_values(by=['date_time'])

        # calculate the packet arrival time difference
        # since we want to maintain the data based on time intervals, we should expect some intervals to include
        # a lot of packets, and others with only few of them.
        # It is hard to process such information, so we will
        # extract the maximal time gap between two sent packets for each interval.
        time_gap_series = pd.to_datetime(self.in_conn_df['date_time']).diff()
        time_gap_series = time_gap_series.convert_dtypes()
        time_gap_series = time_gap_series.fillna(0)
        time_gap_series = time_gap_series / 1000  # convert from nano to micro
        time_gap_series = time_gap_series.astype('int64')

        # Join it to the conn df
        time_gap_series.name = "Capture Time Gap"
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

        # count inbound throughput and attach it to main conn df
        self.in_conn_df = self.count_throughput(self.in_conn_df, 'In Throughput')
        self.in_conn_df['Time'] = self.in_conn_df['date_time'].map(lambda time_str: time_str_to_timedelta(time_str))
        temp_df = self.in_conn_df[['Time', 'In Throughput', time_gap_series.name]]
        self.conn_df = pd.merge(self.conn_df, temp_df, on='Time', how='left')

        # count outbound throughput and attach it to main conn df
        self.out_conn_df = self.count_throughput(self.out_conn_df, 'Out Throughput')
        self.out_conn_df['Time'] = self.out_conn_df['date_time'].map(lambda time_str: time_str_to_timedelta(time_str))
        temp_df = self.out_conn_df[['Time', 'Out Throughput']]
        self.conn_df = pd.merge(self.conn_df, temp_df, on='Time', how='left')

        # Fill 0 when no throughput was recorded
        values = {'In Throughput': 0, 'Out Throughput': 0, time_gap_series.name: -1}
        self.conn_df = self.conn_df.fillna(value=values)

        # Calculate CBIQ
        in_temp_df = self.create_seq_df(self.in_conn_df, 'in_seq_num')
        self.conn_df = pd.merge(self.conn_df, in_temp_df, on='Time', how='left')
        out_temp_df = self.create_seq_df(self.out_conn_df, 'out_seq_num')
        self.conn_df = pd.merge(self.conn_df, out_temp_df, on='Time', how='left')
        self.conn_df = self.conn_df.fillna(method='ffill')
        self.conn_df['CBIQ'] = self.conn_df['in_seq_num'] - self.conn_df['out_seq_num']
        self.conn_df = self.conn_df.drop(columns=['in_seq_num', 'out_seq_num'])

        self.conn_df.index.name = 'Time'

        # Convert the time string into time offset float
        self.conn_df['timestamp'] = self.conn_df['Time'].map(lambda x: get_delta(x, self.conn_df['Time'][0]))
        self.conn_df = self.conn_df.set_index('timestamp')
        self.conn_df = self.conn_df.drop(columns=['Time'])

        # Reorder column to make the DF similar to original single connection stat
        self.conn_df = self.conn_df[[time_gap_series.name, 'In Throughput', 'Out Throughput', 'CBIQ']]
        return

    def count_throughput(self, conn_df, column):
        #bytes_per_timeslot_series = conn_df['seq_num'].diff()
        #bytes_per_timeslot_series = bytes_per_timeslot_series.fillna(0)
        #bytes_per_timeslot_series = bytes_per_timeslot_series.astype('int64')

        #bytes_per_timeslot_series.name = column
        temp_df = conn_df[['seq_num']]
        while True:
            bytes_per_timeslot_series = temp_df['seq_num'].diff()
            bytes_per_timeslot_series = bytes_per_timeslot_series.fillna(1)
            bytes_per_timeslot_series = bytes_per_timeslot_series.astype('int64')
            bytes_per_timeslot_series.name = column
            temp_df = temp_df.join(bytes_per_timeslot_series)

            #temp_df[column] = conn_df['seq_num'].diff()
            temp_df1 = temp_df[(temp_df[[column]] >= 0).all(1)]
            if len(temp_df) == len(temp_df1):
                break
            temp_df = temp_df1.drop(columns=[column])

        conn_df = conn_df.join(temp_df[column])
        conn_df = conn_df.fillna(0)
        # Translate from Bytes per time tick to Mbps
        conn_df[column] = conn_df[column].map(lambda num: num * 8 / 10 ** (6 - self.interval_accuracy))

        # Join it to the conn df
        #bytes_per_timeslot_series.name = column
        #conn_df = conn_df.join(bytes_per_timeslot_series)
        return conn_df

    def create_seq_df(self, conn_df, col_name):
        temp_df = conn_df.drop_duplicates(subset=["date_time"], keep='first')
        temp_df = temp_df[['date_time', 'seq_num']]
        temp_df.columns = ['date_time', col_name]
        temp_df['Time'] = temp_df['date_time'].map(lambda time_str: time_str_to_timedelta(time_str))
        temp_df = temp_df.fillna(method='ffill')
        temp_df = temp_df.drop(columns=['date_time'])
        return temp_df


def create_milli_sample_df(filename):
    df = pd.read_csv(filename, sep=",")
    df = df.sort_values(by=['date_time'])
    df['trunk'] = df['date_time'].str[:-3]
    df = df.drop_duplicates(keep='first', subset=['trunk'])
    df = df.drop(columns=['trunk'])
    return df


if __name__ == '__main__':
    intv_accuracy = 3
    algo_list = ['reno', 'bbr', 'cubic'] # Should be in line with measured_dict keys in online_simulation.py main function
    #abs_path = "/home/another/PycharmProjects/cwnd_clgo_classifier/classification_data/for_dev/fast_data_tree1"
    abs_path = '/tmp/fast_7_7'
    folders_list = os.listdir(abs_path)
    for folder in folders_list:
        result_files = glob.glob(os.path.join(abs_path, folder,"*_6450[0-9]_*"))
        if len(result_files) < 4:
            continue
        # find the destination interface
        if_dict = {}
        for res_file in result_files:
            search_obj = re.search(r'_(\d+).csv$', str(res_file))
            if search_obj:
                if_num = search_obj.group(1)
                if if_num in if_dict.keys():
                    if_dict[if_num] += 1
                else:
                    if_dict[if_num] = 1
        # The first interface with more than one in the value is the server interface
        server_if = 0
        for key, val in if_dict.items():
            if val > 1:
                server_if = int(key)

        # If no interface was spotted more than once, end the iteration
        if server_if == 0:
            continue

        # Find the client files, and make sure there is server file for it.
        # If there is, run stat on them
        for res_file in result_files:
            search_obj = re.search(r'\d+_(\d+_64\d+_\d+_\d+)_(\d+).csv', str(res_file))
            monitored_if = int(search_obj.group(2))
            if search_obj:
                if monitored_if == server_if:
                    continue

            # Look for a matching server file
            search_pattern = search_obj.group(1) + '_' + str(server_if)
            for res_file2 in result_files:
                if search_pattern in res_file2:
                    in_file = os.path.join(abs_path, folder, res_file)
                    out_file = os.path.join(abs_path, folder, res_file2)
                    in_df = create_milli_sample_df(in_file)
                    out_df = create_milli_sample_df(out_file)

                    search_obj = re.search(r'[0-9]+_[0-9]+_6450([0-9])_[0-9]+_52[0-9][0-9]', str(res_file))
                    if not search_obj:
                        break
                    algo_id = int(search_obj.group(1))-1
                    algo_name = algo_list[algo_id]
                    q_line_obj = MilliConnStat(in_df=in_df, out_df=out_df, interval_accuracy=intv_accuracy, rtr_q_filename=None)
                    milli_csv_file_name = 'milli_sample_stat_%s_%d.csv' %(algo_name, monitored_if)
                    q_line_obj.conn_df.to_csv(os.path.join(abs_path, folder,milli_csv_file_name))