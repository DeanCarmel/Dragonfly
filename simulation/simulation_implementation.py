import sys
sys.path.append(".")
import os.path
from pathlib import Path
import random
import numpy
from multiprocessing import Process
from signal import SIGINT, SIGKILL
from time import sleep

from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from datetime import datetime
from mininet.node import OVSController
from mininet.util import pmonitor

from simulation.simulation_topology import SimulationTopology
from simulation.single_connection_statistics import SingleConnStatistics
from simulation.tcpdump_statistics import TcpdumpStatistics
from simulation.tc_qdisc_statistics import TcQdiscStatistics
from simulation.graph_implementation import GraphImplementation
from learning.env import *


def create_csv(sim_obj, client, generate_graphs=False):
    print("calculating statistics for %s" % client)
    in_file = os.path.join(sim_obj.res_dirname, 'client_%s.txt' % client)
    out_file = os.path.join(sim_obj.res_dirname, 'server_%s.txt' % client)
    rtr_file = os.path.join(sim_obj.res_dirname, 'rtr_q.txt')
    graph_file_name = os.path.join(sim_obj.res_dirname, 'Conn_Graph_%s.png' % client)
    plot_title = client
    interval_accuracy = sim_obj.interval_accuracy
    q_line_obj = SingleConnStatistics(in_file, out_file, rtr_file, graph_file_name, plot_title, generate_graphs,
                                      interval_accuracy)
    q_line_obj.conn_df.to_csv(os.path.join(sim_obj.res_dirname, 'single_connection_stat_%s.csv' % client))


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
        self.simulation_topology: SimulationTopology = simulation_topology
        self.iperf_start_after: int = iperf_start_after
        self.net = Mininet(simulation_topology, controller=OVSController, link=TCLink, autoSetMacs=True)
        self.seconds = seconds
        self.simulation_name = simulation_name
        self.port_algo_dict = {}
        self.background_noise = background_noise
        self.interval_accuracy = interval_accuracy
        tn = datetime.now()
        time_str = str(tn.month) + "." + str(tn.day) + "." + str(tn.year) + "@" + str(tn.hour) + "-" + str(
            tn.minute) + "-" + str(tn.second)

        # Create results directory, with name includes num of clients for each algo, and time:
        self.res_dirname = os.path.join(Path(os.getcwd()).parent,
                                        "classification_data",
                                        "with_data_repetition", "queue_size_500", "thesis_new_topology", "0_background_flows_new", time_str + "_" + self.simulation_name)
        os.mkdir(self.res_dirname, 0o777)

        # Set results file names:
        self.iperf_out_filename = os.path.join(self.res_dirname, "iperf_output.txt")
        self.rtr_q_filename = os.path.join(self.res_dirname, "rtr_q.txt")

    def SetCongestionControlAlgorithm(self, host, tcp_algo):
        """
        :param tcp_algo: a member of TcpAlgorithm enum e.g. TcpAlgorithm.westwood
        """
        cmd = 'echo %s > /proc/sys/net/ipv4/tcp_congestion_control' % tcp_algo
        self.net.getNodeByName(host).cmd(cmd)

    def process_results(self, generate_graphs=False, keep_dump_files=False):
        processes = list()
        for client in self.simulation_topology.measured_host_list:
            # x = threading.Thread(target=create_csv, args=(self, client))
            x = Process(target=create_csv, args=(self, client))
            processes.append(x)
            x.start()

        for index, proc in enumerate(processes):
            proc.join()

        if generate_graphs:
            tcpdump_statistsics = TcpdumpStatistics(self.port_algo_dict, self.interval_accuracy)
            for filename in self.file_captures:
                tcpdump_statistsics.parse_tcpdump_file(filename)
            tc_qdisc_statistics = TcQdiscStatistics(self.rtr_q_filename)
            GraphImplementation(tcpdump_statistsics, tc_qdisc_statistics,
                                plot_file_name=os.path.join(self.res_dirname, 'Graphs.png'),
                                plot_fig_name="host_bw_%s_host_delay_%s_srv_bw_%s_srv_delay_%s_queue_size_%s.png" % (
                                    host_bw, host_delay, srv_bw, srv_delay, queue_size))
        if (keep_dump_files == False):
            for p in Path(self.res_dirname).glob("client_*.txt"):
                print(p)
                p.unlink()
            for p in Path(self.res_dirname).glob("server_*.txt"):
                print(p)
                p.unlink()

    def StartSimulation(self):
        self.net.start()

        srv = self.net.getNodeByName(self.simulation_topology.srv)
        srv_ip = srv.IP()
        popens = {}
        srv_procs = []
        rtr = self.net.getNodeByName(self.simulation_topology.rtr2)
        self.net['r1'].cmd("ip route add 10.1.0.0/24 via 10.100.0.2 dev r1-r2")

        for i in range(30):
            self.net['r2'].cmd("ip route add 10.0." + str(i) +".0/24 via 10.100.0.1 dev r2-r1")

        # Generate background noise
        noise_gen = self.net.getNodeByName(self.simulation_topology.noise_gen)

        if self.background_noise > 0:
            noise_gen.popen('python noise_generator.py %s %s' % (srv_ip, self.background_noise))
        client_counter = 0

        for client in self.simulation_topology.host_list:
            # Modify TCP algorithms (because iperf3 does not support vegas in -C parameter):
            cwnd_algo = client[0:client.find("_")]
            self.SetCongestionControlAlgorithm(client, cwnd_algo)

            test_port = (5201 + client_counter)

            # Map test port to algo. This will serve us in results processing
            self.port_algo_dict[test_port] = cwnd_algo

            # In iperf3, each test should have its own server. We have to terminate them at the end,
            # otherwise they are stuck in the system, so we keep the proc nums in a list.
            srv_cmd = 'iperf3 -s -p %d &' % test_port
            srv_procs.append(srv.popen(srv_cmd))

            # Run tcpdump only on measured hosts
            if client in self.simulation_topology.measured_host_list:
                # Throughput measuring- using tcpdump:
                # Running tcpdump on client side, saving to txt file (a separate txt file for each client):
                capture_filename = os.path.join(self.res_dirname, "client_%s.txt" % client)
                interface_name = "r1-%s" % client
                client_mac = self.net.getNodeByName(client).MAC()
                cmd = "tcpdump -n -i r2-r1 'ether host %s'>%s&" % (client_mac, capture_filename)
                rtr.cmd(cmd)

                # Running tcpdump on server side, saving to txt file (a separate txt file for each client):
                capture_filename = os.path.join(self.res_dirname, "server_%s.txt" % client)
                self.file_captures.append(capture_filename)
                # cmd = "tcpdump -n -i r1-r2 'tcp port %d'>%s&" % (test_port, capture_filename)
                cmd = "tcpdump -n -i r2-srv 'tcp port %d'>%s&" % (test_port, capture_filename)
                rtr.cmd(cmd)

            client_counter += 1

            # Disable TSO for the client
            cmd = "ethtool -K %s-r1 tso off" % client
            self.net.getNodeByName(client).cmd(cmd)

        # Disable TSO for router
        cmd = "ethtool -K r2-srv tso off"
        rtr.cmd(cmd)

        sleep(5)
        # Traffic generation loop:
        client_counter = 0
        for client in self.simulation_topology.host_list:
            cwnd_algo = client[0:client.find("_")]
            start_after = random.randint(0, self.iperf_start_after) / 1000
            cmd = 'sleep %f && iperf3 -c %s -t %d -p %d -C %s' % (
                start_after, srv_ip, self.seconds, 5201 + client_counter, cwnd_algo)
            popens[client] = (self.net.getNodeByName(client)).popen(cmd, shell=True)
            client_counter += 1

        # Gather statistics from the router:
        q_proc = rtr.popen('python tc_qdisc_implementation.py r2-srv %s %d'
                             % (self.rtr_q_filename, self.interval_accuracy))

        # q_proc = rtr.popen('python tc_qdisc_implementation.py r1-r2 %s %d'
        #                     % (self.rtr_q_filename, self.interval_accuracy))

        print("==========DEBUG==============" + str(q_proc.pid))

        # Wait until all commands are completed:
        for client, line in pmonitor(popens, timeoutms=1000):
            if client:
                print('<%s>: %s' % (client, line), )
        # Kill the server's iperf -s processes, the router's queue monitor and tcpdumps:
        sleep(5)
        for process in srv_procs:
            process.send_signal(SIGKILL)
        q_proc.send_signal(SIGINT)

        # make sure q_disc file is saved before leaving mininet
        for t in range(15):
            if os.path.isfile(self.rtr_q_filename):
                break
            else:
                print("qdisc file not ready: " + str(t))
                sleep(1)
        self.net.stop()


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


if __name__ == '__main__':
    interval_accuracy = 3
    # Simulation's parameters initializing:
    measured_dict = {}
    unmeasured_dict = {}
    simulation_duration = 6 + START_AFTER / 1000
    setLogLevel('info')

    background_noise = 0
    host_delay = 250
    srv_delay = 250
    iteration = 0

    host_bw = 500
    srv_bw = 500
    queue_size = 500
    process_results = True
    for srv_bw in numpy.linspace(50, 100, 50):
        for host_bw in numpy.linspace(srv_bw, srv_bw + 100, 50):
            iteration = 0
            while iteration < 2:

                measured_dict['reno'] = 1
                measured_dict['bbr'] = 1
                measured_dict['cubic'] = 1
                # Background flows:
                unmeasured_dict['reno'] = 5
                unmeasured_dict['bbr'] = 5
                unmeasured_dict['cubic'] = 5
                algo_streams = AlgoStreams(measured_dict, unmeasured_dict)

                total_delay = 2 * (host_delay + srv_delay)
                simulation_topology = SimulationTopology(algo_streams, host_delay=host_delay, host_bw=host_bw,
                                                         srv_bw=srv_bw,
                                                         srv_delay=srv_delay, rtr_queue_size=queue_size)
                simulation_name = create_sim_name(measured_dict)
                iteration += 1
                simulator = Iperf3Simulator(simulation_topology, simulation_name, simulation_duration,
                                            iperf_start_after=START_AFTER,
                                            background_noise=background_noise,
                                            interval_accuracy=interval_accuracy, iteration=iteration)
                simulator.StartSimulation()

                simulator.process_results(generate_graphs=False, keep_dump_files=False)
                clean_sim()
