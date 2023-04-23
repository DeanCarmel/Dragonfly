import signal
import subprocess
from datetime import datetime
from subprocess import Popen
from sys import argv
import re  # xu
import time

run = True
debug_file_name = "./debug_files/%d_qdisc_debug.csv" % int(time.time())
debug_file = open(debug_file_name, 'w')


# debug_file = open("q_disc_debug.txt", 'w')


def signal_handler(signal, frame):
    global run
    # print ("exiting")
    run = False


if __name__ == '__main__':
    queue_len_bytes_dict = {}
    drops_dict = {}
    loop_count = 0
    # queue_len_packets_list = []
    assert argv != 4, "usage: tc_qdisc_implementation <ifName> <filename> <tick interval accuracy (0-4)>"
    if_name = argv[1]
    results_filename = argv[2]
    tick_interval_accuracy = argv[3]
    # Check if tick_interval_accuracy is between 0 to 4
    tick_interval_accuracy = int(tick_interval_accuracy)
    print("tick_interval_accuracy: %d" % tick_interval_accuracy)
    # assert tick_interval_accuracy<0 or tick_interval_accuracy>4, "accuracy (last parameter) should be a number between 0 to 4"

    signal.signal(signal.SIGINT, signal_handler)
    last_dropped = 0
    results_file = open(results_filename, 'w')
    while run:
        # it's fair to say that in this stage we do not mean to run forever
        loop_count += 1
        if loop_count > 2000000:
            break
        p = Popen(["/sbin/tc", "-s", "qdisc", "show", "dev", if_name], stdout=subprocess.PIPE,
                  universal_newlines=True)
        output = p.communicate()
        debug_file.write(output[0])

        # parse queue length TODO: make more generic
        out_str = output[0].split('clsact')[0]

        match = re.search(r'dropped\s+(\d+).*\n.?backlog\s+(\d+[kK]?)b\s+(\d+)p', out_str, re.DOTALL)
        if match:
            drops_str = match.group(1)
            drops = int(drops_str) - last_dropped
            last_dropped = int(drops_str)

            if output[0].find("K") == -1:
                num_of_bytes = match.group(2)
            else:
                num = int(match.group(2)[0:-1]) * 1000
                num_of_bytes = str(num)
            num_of_packets = match.group(3)
            num_of_cut_digits = tick_interval_accuracy - 6
            time_str = datetime.now().strftime("%H:%M:%S.%f")[:num_of_cut_digits]

            queue_len_bytes_dict[datetime.now().strftime("%H:%M:%S.%f")[:num_of_cut_digits]] = "%s\t%s\t%d" % (
                num_of_bytes, num_of_packets, drops)
            debug_file.write("%s\t%s\t%s\t%s\n" % (time_str, num_of_bytes, num_of_packets, drops_str))
            results_file.write("%s\t%s\t%s\t%s\n" % (time_str, num_of_bytes, num_of_packets, drops_str))
        else:
            debug_file.write("------------------NO MATSHSHSHSH + out_str\n")

        if tick_interval_accuracy == 0:
            time_to_sleep = 0.993
        elif tick_interval_accuracy == 1:
            time_to_sleep = 0.093
        elif tick_interval_accuracy == 2:
            time_to_sleep = 0.003
        else:
            time_to_sleep = 0.0001
        time.sleep(time_to_sleep)

    # SIGINT was called. Save all results in a file:
    tt = int(time.time())
    debug_file.write("%d-------saving to file %s\n" % (tt, results_filename))
    # for key, val in queue_len_bytes_dict.items():
    # time_str = key
    # num_of_bytes, num_of_packets, drops_str = val.split()
    # results_file.write("%s\t%s\t%s\t%s\n" % (time_str, num_of_bytes, num_of_packets, drops_str))
    debug_file.write("%d------results  saves %s\n" % (tt, results_filename))

    results_file.close()
    debug_file.close()
