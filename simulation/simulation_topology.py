"""
Congestion control reavluation classification topology:

   reno_host_i-----+
        .    |
        .    r1 ---- r2 ---- srv
        .    |
   vegas_host_i----+

"""
from logging import info
from itertools import chain
# from mininet.link import TCLink
from mininet.node import Node
from mininet.topo import Topo


class LinuxRouter(Node):
    "A Node with IP forwarding enabled."

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        info('enabling forwarding on ', self)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class SimulationTopology(Topo):
    def __init__(self, algo_streams, host_bw=None, host_delay=None, srv_bw=None, srv_delay=None, rtr_queue_size=None):
        self.algo_streams = algo_streams
        self.host_bw = host_bw
        self.host_delay = host_delay
        self.srv_bw = srv_bw
        self.srv_delay = srv_delay
        self.rtr_queue_size = rtr_queue_size
        self.host_list = []  # All hosts, measured and unmeasured
        self.measured_host_list = []

        self.as_addr_prefix = "10.0."

        # super should be called only after class member initialization.
        # The super constructor calls build.
        super(SimulationTopology, self).__init__()

    def to_dict(self):
        my_dict = {"algo_streams": self.algo_streams, "host_bw": self.host_bw, "host_delay": self.host_delay,
                "srv_bw": self.srv_bw, "srv_delay": self.srv_delay, "rtr_queue_size": self.rtr_queue_size}
        return my_dict

    def add_host(self, algo, index):
        client_subnet_prefix = self.as_addr_prefix + str(index)
        host = self.addHost(algo + '_' + str(index),
                            ip=client_subnet_prefix + '.10/24',
                            defaultRoute="via " + client_subnet_prefix + '.1'
                            )
        self.host_list.append(host)
        # Add only measured hosts to the measured hosts list
        total_measured_hosts = sum(self.algo_streams.measured_dict.values())
        if index < total_measured_hosts:
            self.measured_host_list.append(host)

    def build(self, **_opts):
        # The router configuration:
        self.rtr1 = self.addHost('r1', cls=LinuxRouter, ip='10.0.0.1/24')
        self.rtr2 = self.addHost('r2', cls=LinuxRouter, ip='10.1.0.1/24')

        # Hosts configuration:
        host_number = 0
        for key, val in chain(self.algo_streams.measured_dict.items(), self.algo_streams.unmeasured_dict.items()):
            for h in range(0, val):
                self.add_host(key, host_number)
                self.addLink(self.host_list[host_number], self.rtr1,
                             intfName1='%s_%s-r1' % (key, str(host_number)),
                             intfName2='r1-%s_%s' % (key, str(host_number)),
                             params2={'ip': self.as_addr_prefix + str(host_number) + '.1/24'},
                             bw=self.host_bw,
                             use_tbf=True,
                             delay=self.host_delay
                             )
                host_number += 1

        # Add noise generator. Its index is the next one after the server:
        noise_gen_addr = self.as_addr_prefix + str(host_number) + '.10'
        self.noise_gen = self.addHost('noise_gen', ip=noise_gen_addr + '/24',
                                      defaultRoute="via " + self.as_addr_prefix + str(host_number) + '.1')
        self.addLink(self.noise_gen, self.rtr1,
                     intfName1='noise-gen-r1',
                     intfName2='r1-noise-gen',
                     params2={
                         'ip': self.as_addr_prefix + str(host_number) + '.1/24'
                     },
                     bw=self.host_bw,
                     use_tbf=True,
                     max_queue_size=int(self.rtr_queue_size),
                     delay=self.host_delay
                     )
        host_number += 1

        # The Server (the receiver) configuration Its index is the current host number defined in clients loop:
        srv_addr ="10.1.0.10"
        self.srv = self.addHost('srv', ip=srv_addr + '/24',
                                defaultRoute="via " + '10.1.0.1')
        self.addLink(self.srv, self.rtr2,
                     intfName1='srv-r2',
                     intfName2='r2-srv',
                     params2={
                         'ip': "10.1.0.1/24",
                         'delay': str(self.srv_delay)
                     },
                     bw=self.srv_bw,
                     use_tbf=True,
                     max_queue_size=int(self.rtr_queue_size)
                     )


        # Configuration of the link between the two routers:
        self.addLink(self.rtr1, self.rtr2,
                     intfName1='r1-r2',
                     intfName2='r2-r1',
                     params1={
                         'ip': "10.100.0.1/24",
                         'delay': str(self.srv_delay)
                     },
                     params2={
                         'ip': "10.100.0.2/24",
                         'delay': str(self.srv_delay)
                     },
                     bw=self.srv_bw,
                     use_tbf=True,
                     max_queue_size=int(self.rtr_queue_size)
                     )
