#!/usr/bin/python3
import shlex
import subprocess
import sys

base_port = int(sys.argv[1])
num_of_servers = int(sys.argv[2])

for server_port in range(base_port, base_port + num_of_servers):
    srv_cmd = 'iperf3 -s -p %d' % server_port
    cmds = shlex.split(srv_cmd)
    subprocess.Popen(cmds, start_new_session=True)
