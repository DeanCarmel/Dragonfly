#!/usr/bin/python3
import os
import shlex
import subprocess
import sys
from random import randint

from paramiko.client import SSHClient
from pssh.clients import ParallelSSHClient
from sismaot import getCredentials

user, password = getCredentials()
algo_list = ['reno', 'bbr', 'cubic']
#algo_list = ['reno', 'bbr', 'cubic', 'vegas', 'htcp', 'bic']  # IMPORTANT! should be inline with online_filtering algo_dict
sim_name = sys.argv[1]
#num_of_bg_flow_list = [0,20]
#num_of_bg_flow_list = [5, 10, 20, 25]
iperf_duration = 600
min_q_size, max_q_size, q_size_step = 2000, 6001, 2000
#list of algo permutations the number represents the location in algo_list.
# The location in the tuple determine for which sender the algo refers to.
# Example: (1,1,2) determines that senders 0 and 1 will user bbr algo, and sender 2 will use cubic algo.
# Altogether we have 9 permutation with 1 or 2 cwnd algos.
#l_of_t = [(0,1,2),(0,0,0),(1,1,1),(2,2,2),(3,3,3),(4,4,4)]
#l_of_t = [(0,1,2),(0,0,0),(1,1,1),(2,2,2), (0,0,1),(0,0,2), (1,1,2), (1,1,0), (2,2,0), (2,2,1)]
l_of_t = [(0,1,2)]

client01 = SSHClient()
client01.load_host_keys(os.path.join(os.path.dirname(__file__), 'known_hosts'))
client01.connect('132.68.60.206', username=user, password=password)
client23 = SSHClient()
client23.load_host_keys(os.path.join(os.path.dirname(__file__), 'known_hosts'))
client23.connect('132.68.60.131', username=user, password=password)
router01 = SSHClient()
router01.load_host_keys(os.path.join(os.path.dirname(__file__), 'known_hosts'))
router01.connect('132.68.60.140', username=user, password=password)

# This file is the main loop for the router.
# It cleans clsact, sets qdisc limit length and starts tcp ebpf monitor
# It will stop the monitor before changing the limit, for stability purposes (hopefully)
# We use subprocess call, becaue all of the commands should complete before the next command executes


for packet_limit in range(min_q_size, max_q_size, q_size_step):
    # set the qdisc length on router01 server side interface
    cmd = 'sudo tc qdisc replace dev eno2 root pfifo limit %d ' % packet_limit
    router01.exec_command(cmd)
    #cmds = shlex.split(cmd)
    #subprocess.call(cmds)

    for t in l_of_t:
        for num_of_bg_flows in num_of_bg_flow_list:
            # Run measured iperf3 flows
            for algo in algo_list:
                dest_port = 5201 + algo_list.index(algo)
                src_port = 64501 + algo_list.index(algo)
                slp = randint(0, 2)
                cmd = 'sleep %d && iperf3 -c 10.0.100.1 -p %d --cport %d -t %d -i 10 -C %s ' % (slp, dest_port, src_port, (iperf_duration-slp-5), algo)
                if algo_list.index(algo)<len(algo_list)/2:
                    curr_client = client01
                else:
                    curr_client = client23
                curr_client.exec_command(cmd)

            # Clean the previous round's clsact definitions, if any
            cmd = 'sudo ./clean_clsact.sh'
            cmds = shlex.split(cmd)
            subprocess.call(cmds)

            # Generate iperf3 background flows
            cmd = '~/bg_iperf.py  %d %d 5211 10.0.100.1 %s' % (num_of_bg_flows, iperf_duration,algo_list[t[0]])
            client01.exec_command(cmd)
            cmd = '~/bg_iperf.py  %d %d 5300 10.0.101.1 %s' % (num_of_bg_flows, iperf_duration,algo_list[t[1]])
            client01.exec_command(cmd)
            cmd = '~/bg_iperf.py  %d %d 5400 10.0.102.1 %s' % (num_of_bg_flows, iperf_duration,algo_list[t[2]])
            client23.exec_command(cmd)

            # Monitor the router and create raw data
            # create abbreviation string e.g. ccr for cubic cubic reno. in case of 60 bg flows it will mean
            # 40 flows of cubic, 20 for reno and 0 for bbr
            algo_abbr = algo_list[t[0]][0]+algo_list[t[1]][0]+algo_list[t[2]][0]
            curr_sim_name = 'NumBG_%d_Algo_%s_Queue_%d_%s' % (num_of_bg_flows*3, algo_abbr, packet_limit, sim_name)

            # Run the smart dump command (different interfaces) remotely in router01
            cmd = 'cd ~/cwnd_clgo_classifier/online_sim && sudo ~/cwnd_clgo_classifier/online_sim/tcp_smart_dump.py %s %d eno2 enp2s0f0 enp2s0f1 ' \
                  'enp2s0f2 enp2s0f3 ' % ('r01_' + curr_sim_name, iperf_duration)
            router01.exec_command(cmd)

            # Run the tcp_smart dump command locally synchronously
            cmd = 'sudo ../online_sim/tcp_smart_dump.py %s %d enp2s0 enp1s0 ' % ('r02_' + curr_sim_name, iperf_duration)
            cmds = shlex.split(cmd)
            subprocess.call(cmds)

