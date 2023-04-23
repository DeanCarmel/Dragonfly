#!/usr/bin/python3

import os
import re
import shutil
from pathlib import Path
from pssh.clients import SSHClient

from time import sleep, time

import time
from physical_sim.sismaot import getCredentials


class PhysicalTopology:
    def __init__(self, client_list, rtr, srv):
        self.host_list = client_list
        self.rtr = rtr
        self.srv = srv
        self.rtr_srv_ifName = 'eno2'
        self.rtr_hosts_ifName = 'enp2s0'


class AlgoStreams:
    def __init__(self, measured_dict, unmeasured_dict):
        self.measured_dict = measured_dict
        self.unmeasured_dict = unmeasured_dict


class Iperf3Simulator:
    def __init__(self, simulation_topology, simulation_name, seconds=10, iperf_start_after=0,
                 background_noise=0, interval_accuracy=1, iteration=0):
        """
        :param interval_accuracy:
        :param simulation_topology: The topology class to be used
        :param simulation_name: the results folder will contain the test name
        :param seconds: The test duration
        :param iperf_start_after: iperf will start the after random time up to this value in ms
        :param tick_interval: tick duration. effects qdisc sample interval, background noise generation
        :param background_noise: Amount of packets per tick to send as background noise
        """
        self.file_captures = []
        self.simulation_topology: PhysicalTopology = simulation_topology
        self.iperf_start_after: int = iperf_start_after
        self.seconds = seconds
        self.simulation_name = simulation_name
        self.port_algo_dict = {}
        self.background_noise = background_noise
        self.interval_accuracy = interval_accuracy

    def start_simulation(self):

        srv_mgmt_ip = self.simulation_topology.srv
        rtr_mgmt_ip = self.simulation_topology.rtr
        user, password = getCredentials()

        client_counter = 0


        ssh_to_rtr = SSHClient(rtr_mgmt_ip, user=user, password=password)

        for host in self.simulation_topology.host_list:

            #cwnd_algo = host[0:host.find("_")]

            test_port = (5201 + client_counter)

            # Map test port to algo. This will serve us in results processing

            #self.port_algo_dict[test_port] = cwnd_algo


        # Run the online_sim command with all the interfaces. Server interface should always be the first one!
        cd_cmd = 'cd cwnd_clgo_classifier/online_sim'
        self.simulation_name = 'bbb'
        ebpf_cmd = 'sudo ./tcp_smart_dump.py'
        rtr_cmd = "%s;%s %d %s %s %s&>debug_files/%s_rtr_ebpf_out.txt" % (
            cd_cmd, ebpf_cmd, simulation_duration, self.simulation_name, self.simulation_topology.rtr_srv_ifName,
            self.simulation_topology.rtr_hosts_ifName, time.time())
        #rtr_cmd = "touch qqq_%s" % (time.time())
        print(rtr_cmd)
        curr_out = ssh_to_rtr.run_command(rtr_cmd)
        sleep(15)
        '''sleep(2)
        # Traffic generation loop:
        client_counter = 0
        for client in self.simulation_topology.host_list:
            cwnd_algo = client[0:client.find("_")]
            start_after = randint(0, self.iperf_start_after) / 1000
            if client in self.simulation_topology.measured_host_list:
                client_port = 64501 + list(measured_dict.keys()).index(
                    cwnd_algo)  # Set client port according to algo. hint for csv file names
            else:
                client_port = 64499

            cmd = 'sleep %f && iperf3 -c %s -t %d -p %d --bind 10.0.%d.10 --cport %d -C ' \
                  '%s>debug_files/ipuff_debig_%s.txt' % (
                      start_after, srv_ip, self.seconds, 5201 + client_counter, client_counter, client_port, cwnd_algo,
                      client)
            print("sleeeeeeeeeeeeeeeeeeeeeeping %s " % cmd)
            popens[client] = (self.net.getNodeByName(client)).popen(cmd, shell=True)
            client_counter += 1

        for client, line in pmonitor(popens, timeoutms=1000):
            if client:
                print('<%s>: %s' % (client, line), )
        print("--------------------after monitoring " + str(len(popens)))
        # Kill the server's iperf -s processes, the router's queue monitor and tcpdumps:
        rtr_ebpf_proc.send_signal(SIGINT)
        sleep(2)
        for process in srv_procs:
            process.send_signal(SIGINT)'''


def clean_sim():
    cmd = "mn -c"
    os.system(cmd)


def create_sim_name(cwnd_algo_dict):
    name = ''
    if len(cwnd_algo_dict) == 0:
        return "WTF"
    for key, val in cwnd_algo_dict.items():
        name += "%d_%s_" % (val, key)
    return name[0:-1]


def arrange_res_files():
    des_res_dir = os.path.join(Path(os.getcwd()).parent, "classification_data", "3_bg_flows")
    curr_root_dir = os.path.join(Path(os.getcwd()).parent, "classification_data", "online")
    result_files = list(Path(curr_root_dir).rglob("*_6450[0-9]_*"))
    count = 0
    for res_file in result_files:
        search_obj = re.search(r'[0-9]+_[0-9]+_(6450[0-9])_[0-9]+_52[0-9][0-9].csv', str(res_file))
        if not search_obj:
            continue
        port = int(search_obj.group(1))
        port_offset = port - 64501
        curr_algo = list(measured_dict.keys())[port_offset]
        file_new_name = 'single_connection_stat_%s_%d.csv' % (curr_algo, count)
        os.rename(res_file, os.path.join(os.path.dirname(res_file), file_new_name))
        count += 1

    # Move the files to final destination
    file_names = os.listdir(curr_root_dir)
    for file_name in file_names:
        # shutil.move(folderr, des_res_dir)
        shutil.move(os.path.join(curr_root_dir, file_name), des_res_dir)


if __name__ == '__main__':

    client_mgmt_addr_list = ['132.68.60.206', '132.68.60.131']
    srv_mgmt_addr = '132.68.60.135'
    rtr_mgmt_addr = '132.68.60.140'
    iperf3_srv_addr_list = ['10.0.100.1', '10.0.101.1', '10.0.102.1', '10.0.103.1']
    iperf3_client_addr_list = ['10.0.0.1', '10.0.1.1', '10.0.2.1', '10.0.3.1']

    # interval accuracy: a number between 0 to 3. For value n, the accuracy will be set to 1/10^n
    interval_accuracy = 3

    # Simulation's parameters initializing:
    measured_dict = {}
    unmeasured_dict = {}
    simulation_duration = 15  # 60 # 80 # 120  # seconds.
    # total_bw = max(host_bw * sum(algo_dict.itervalues()), srv_bw).

    # queue_size = 800  # 2 * (
    # srv_bw * total_delay) / tcp_packet_size  # Rule of thumb: queue_size = (bw [Mbit/sec] * RTT [sec]) / size_of_packet.
    # Tell mininet to print useful information:

    background_noise = 0
    host_delay = 2.5
    srv_delay = 2.5
    iteration = 0

    host_bw = 200
    srv_bw = 200
    queue_size = 500
    for lcount in range(1):
        measured_dict['reno'] = 1
        measured_dict['bbr'] = 1
        measured_dict['cubic'] = 1
        #unmeasured_dict['reno'] = bg
        #unmeasured_dict['bbr'] = bg
        #unmeasured_dict['cubic'] = bg
        algo_streams = AlgoStreams(measured_dict, unmeasured_dict)
        # algo_dict['bbr']=10
        total_delay = 2 * (host_delay + srv_delay)
        simulation_topology = PhysicalTopology(client_mgmt_addr_list, rtr_mgmt_addr, srv_mgmt_addr)
        simulation_name = create_sim_name(measured_dict)
        iteration += 1
        simulator = Iperf3Simulator(simulation_topology, simulation_name, simulation_duration,
                                    iperf_start_after=2,
                                    background_noise=background_noise,
                                    interval_accuracy=interval_accuracy, iteration=iteration)
        # iperf_start_after=500, background_noise=100)
        simulator.start_simulation()
        sleep(2)
        arrange_res_files()
        clean_sim()
