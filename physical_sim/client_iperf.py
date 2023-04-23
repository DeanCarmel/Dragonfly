#!/usr/bin/python3
import subprocess
import sys
import shlex
#######################
# BG Iperf for client
#######################
num_of_flows = int(sys.argv[1])
duration = int(sys.argv[2])
start_port = int(sys.argv[3])
dest_ip = sys.argv[4]
algo = sys.argv[5]

for curr_port in range(start_port, start_port+num_of_flows):
    cmd = 'iperf3 -c %s -p %d  -t %d --cport %d -C %s' % (dest_ip, curr_port, duration,52000+curr_port, algo)
    cmds = shlex.split(cmd)
    subprocess.Popen(cmds, start_new_session=True)
