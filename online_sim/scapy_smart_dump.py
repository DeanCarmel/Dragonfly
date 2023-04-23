#!/home/another/PycharmProjects/cwnd_clgo_classifier/venv/bin/python3
import shlex

from scapy.all import *
import pandas as pd
import os
import time
from pathlib import Path
import sys
sys.path.insert(0,'..')
from simulation.single_connection_statistics import OnlineSingleConnStatistics

interval_accuracy = 3

res_dir = os.path.join(Path(os.getcwd()).parent, "classification_data", "csvs")
traffic_duration = int(sys.argv[1])
intf_list = sys.argv[2:]
interval_duration = 5
num_of_samples = int(traffic_duration / interval_duration)
server_intf_name = sys.argv[2]

for jj in range(num_of_samples):
    packets_list = []
    # Gather statistics from the router:
    q_disc_file_name = os.path.join(res_dir, "%d_qdisc.csv" % int(time.time()))
    q_disc_cmd = os.path.join(Path(os.getcwd()).parent, "simulation", "tc_qdisc_implementation.py")
    command_line = 'python3 %s r-srv %s %d' % (q_disc_cmd, q_disc_file_name, interval_accuracy)
    args = shlex.split(command_line)
    q_proc = subprocess.Popen(args)

    ## Setup sniff, filtering for IP traffic
    print ("starting to sniff on %s" %",".join(intf_list))
    z= sniff(iface=intf_list,filter="dst port 5201", prn=lambda x: packets_list.append(x), timeout=interval_duration)

    print ("sniff completed %s" %z)

    df_dict = {}
    print ("Building dict")
    for pkt in packets_list:
        # Check if TCP (although we filtered it)
        try:
            if (pkt[0].name is not "Ethernet") or (pkt[1].name is not "IP") or (pkt[2].name is not "TCP"):
                continue
        except IndexError:
            continue
        conn_index = "%s_%s_%s_%s" % (pkt[1].src, pkt[2].sport, pkt[1].dst, pkt[2].dport)
        capture_time = pkt[0].time
        pkt_len = len(pkt)
        ts_val = 111
        seq_num = pkt[2].seq
        intf_name = pkt[0].sniffed_on
        if not conn_index in df_dict:
            # Init ingress list and egres list
            df_dict[conn_index] = {}

        if not intf_name in df_dict[conn_index]:
            df_dict[conn_index][intf_name] = []

        df_dict[conn_index][intf_name].append(
            [conn_index, capture_time, pkt_len, ts_val, seq_num])
    print ("building DF")
    for conn_index in df_dict.keys():
        ssrv_df = None
        clnt_df = None
        "For each connection we can expect 2 interfaces, one ingress and one egress traffic"
        "For now, we assume that there is only one egress port (server facing) in the router"
        for intf_name in df_dict[conn_index].keys():
            df = pd.DataFrame(df_dict[conn_index][intf_name],
                  columns=['conn_index', 'date_time', 'length', 'ts_val', 'seq_num'])
            df.index.name = "num"
            df['date_time'] = df['date_time']  * 1000000
            df['date_time'] = pd.to_datetime(df['date_time'], unit='us')
            df['date_time'] = df['date_time'].dt.tz_localize('UTC').dt.tz_convert('Asia/Jerusalem')
            df['date_time'] = df['date_time'].dt.strftime('%H:%M:%S.%f')
            csv_filename = os.path.join(res_dir, "%d_%s_%s.csv" % (int(time.time()), conn_index, intf_name))
            print ("saving file %s" %csv_filename)
            df.to_csv(csv_filename)
            if intf_name == server_intf_name:
                ssrv_df = df
            else:
                clnt_df = df
        # Create connection stat file out of df objects
        print('-----%screating single connection DF' % str(time.time()))
        if ssrv_df is not None and clnt_df is not None:
            conn_stat_obj = OnlineSingleConnStatistics(in_df=clnt_df, out_df=ssrv_df, interval_accuracy=3,
                                                       rtr_q_filename=q_disc_file_name)
            csv_filename = os.path.join(res_dir, "%d_%s.csv" % (int(time.time()), conn_index))
            conn_stat_obj.conn_df.to_csv(csv_filename)
    print ("DF Completed")
