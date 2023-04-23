import signal
from random import randint
from subprocess import Popen
from sys import argv
import time
import string
import socket

if __name__ == '__main__':
    # queue_len_packets_list = []
    assert argv != 3, "argv was %d. add destination ip address an number of packets as parameters" % len(argv)
    srv_ip = argv[1]
    UDP_PORT = 5005
    avg_packets_per_tick = int(argv[2]) # Tick is 0.1 sec

    # if avg packets per tick is less than 1, we probably don't want to generate backgound traffic
    if (avg_packets_per_tick < 1):
        exit()
    # Build string to echo, about 1400 chars long
    udp_str = ""
    for _ in range(27):
        udp_str += string.ascii_letters
    udp_bytes = str.encode(udp_str)
    sock = socket.socket(socket.AF_INET,  socket.SOCK_DGRAM)
    while True:
        for _ in range(randint(1, avg_packets_per_tick)):
            sock.sendto(udp_bytes, (srv_ip, UDP_PORT))

        time.sleep(0.1)
