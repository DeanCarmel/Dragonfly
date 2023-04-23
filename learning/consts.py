import torch

# Debugging data:

DEBUG = '/home/dean/PycharmProjects/cwnd_clgo_classifier/classification_data/physical data/10 seconds/bottleneck/DEBUG_1_DATAFRAME/STATS'

# Classification data:

DATA_EXAMPLE = r'/home/dean/PycharmProjects/cwnd_clgo_classifier/learning/data'
RESULT_EXAMPLE = r'/home/dean/PycharmProjects/cwnd_clgo_classifier/learning/result'

ABSOLUTE_PATH = r'/home/dean/PycharmProjects/cwnd_clgo_classifier/'

CBIQ_UNUSED_PARAMETERS = ("CBIQ", ['CBIQ', 'Capture Time Gap', 'in_seq_num', 'out_seq_num', 'In Throughput', 'Out Throughput', 'deepcci'])
DEEPCCI_UNUSED_PARAMETERS = ("Deepcci", ['timestamp', 'CBIQ',  'in_seq_num', 'out_seq_num', 'In Throughput', 'Out Throughput', 'Capture Time Gap'])
IN_THROUGHPUT_UNUSED_PARAMETERS = ("In Throughput", ['timestamp', 'CBIQ',  'in_seq_num', 'out_seq_num', 'deepcci', 'Out Throughput', 'Capture Time Gap'])
OUT_THROUGHPUT_UNUSED_PARAMETERS = ("Out Throughput", ['timestamp', 'CBIQ',  'in_seq_num', 'out_seq_num','deepcci', 'In Throughput', 'Capture Time Gap'])
THROUGHPUT_UNUSED_PARAMETERS = ("Throughput", ['timestamp', 'CBIQ',  'in_seq_num', 'out_seq_num', 'deepcci', 'Capture Time Gap'])
CAPTURE_UNUSED_PARAMETERS = ("Capture Arrival Time", ['timestamp', 'CBIQ',  'in_seq_num', 'out_seq_num', 'deepcci', 'In Throughput', 'Out Throughput'])
ALL_PARAMETERS_UNUSED_PARAMETERS = ("All Parameters", ['deepcci'])
DRAGONFLY_UNUSED_PARAMETERS = ("Dragonfly", ['Capture Time Gap', 'deepcci'])

MININET_UNUSED_PARAMETERS = ["timestamp", "In Throughput", "Out Throughput", "Connection Num of Drops", "Connection Num of Retransmits", "Send Time Gap", "CBIQ", "Total Bytes in Queue", "Num of Packets", "Num of Drops"]
MININET_CBIQ_UNUSED_PARAMETERS = ("CBIQ", ["In Throughput", "Out Throughput", "Connection Num of Drops", "Connection Num of Retransmits", "Send Time Gap", "Total Bytes in Queue", "Num of Packets", "Num of Drops"])
MININET_THROUGHPUT_UNUSED_PARAMETERS = ("Throughput", ["timestamp", "CBIQ", "Out Throughput", "Connection Num of Drops", "Connection Num of Retransmits", "Send Time Gap", "Total Bytes in Queue", "Num of Packets", "Num of Drops"])
MININET_DRAGONFLY_UNUSED_PARAMETERS = ("Dragonfly", ["Out Throughput", "Connection Num of Drops", "Connection Num of Retransmits", "Send Time Gap", "Total Bytes in Queue", "Num of Packets", "Num of Drops"])
MININET_DEEPCCI_UNUSED_PARAMETERS = ("Deepcci", ["CBIQ", "In Throughput", "Out Throughput", "Connection Num of Drops", "Connection Num of Retransmits", "Send Time Gap", "Total Bytes in Queue", "Num of Packets", "Num of Drops"])

SLEEP_DURATION = 60*60*1

NUM_OF_CLASSIFICATION_PARAMETERS = 8
IS_BATCH = True
IS_DIVERSE_DATA = False
IS_DATA_SAMPLE = False
IS_SAMPLE_RATE = True
SAVE_MODEL_PT = False
IS_FULL_SESSION = False
IS_MININET = False

# GPU:
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")