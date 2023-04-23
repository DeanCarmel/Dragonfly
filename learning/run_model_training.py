import os
from enum import Enum
from learning import model_training
from learning.consts import *

class NetEnum(Enum):
    MY_NET = 1
    DEEPCCI_NET = 2
    FULLY_CONNECTED_NET = 3

class SimParams:
    def __init__(self, data_path, absolute_path, results_path, model_path, diverse_data_path, csv_filename, is_data_sample, is_diverse_data, is_full_session, sleep_duration, save_model_pt, is_mininet):
        self.data_path = data_path
        self.absolute_path = absolute_path
        self.results_path = results_path
        self.model_path = model_path
        self.diverse_data_path = diverse_data_path
        self.csv_filename = csv_filename
        self.is_data_sample = is_data_sample
        self.is_diverse_data = is_diverse_data
        self.is_full_session = is_full_session
        self.sleep_duration = sleep_duration
        self.save_model_pt = save_model_pt
        self.is_mininet = is_mininet


class ModelParams:
    def __init__(self, num_of_congestion_controls, num_of_time_samples, net_type, bg_flow, chunk_size, is_batch):
        # self.net = net_enum.name
        self.num_of_congestion_controls = num_of_congestion_controls
        self.num_of_time_samples = num_of_time_samples
        self.net_type = net_type
        self.bg_flow = bg_flow
        self.chunk_size = chunk_size
        self.is_batch = is_batch


class NetType:
    def __init__(self, net_enum, unused_parameters, deepcci_num_of_time_samples=None):
        if net_enum == NetEnum.MY_NET:
            self.net = "my_net"
        elif net_enum == NetEnum.DEEPCCI_NET:
            self.net = "deepcci_net"
            self.deepcci_num_of_time_samples = deepcci_num_of_time_samples
        else:
            self.net = "fully_connected_net"
        self.parameters, self.unused_parameters_list = unused_parameters
        self.num_of_classification_parameters = NUM_OF_CLASSIFICATION_PARAMETERS - len(self.unused_parameters_list)

    def get_net(self):
        return os.path.join(self.net, self.parameters)

    def get_unused_parameters(self):
        return self.unused_parameters_list

    def get_num_of_classification_parameters(self):
        return self.num_of_classification_parameters

    def get_deepcci_num_of_time_samples(self):
        if self.net == "deepcci_net":
            return deepcci_num_of_time_samples
        else:
            return None

def get_net_types():
    net_types = []
    for net_enum in NetEnum:
        if net_enum == NetEnum.MY_NET:
            for unused_parameters in [DRAGONFLY_UNUSED_PARAMETERS, CBIQ_UNUSED_PARAMETERS]:
                 net_types.append(NetType(net_enum, unused_parameters))
        elif net_enum == NetEnum.DEEPCCI_NET:
            continue
            net_types.append(NetType(net_enum, DEEPCCI_UNUSED_PARAMETERS))
        else:
            continue
    return net_types

def get_results_path(absolute_path, bg_flow, filter, net_type, chunk_size):
    results_path = os.path.join(absolute_path, str(bg_flow) + " background flows", str(filter) + " filter",
                                net_type, str(chunk_size))
    return results_path

def get_filter_from_data_path(data_path):
    return data_path.split("filter", 1)[-1].split("/")[-1].split()[0]

if __name__ == '__main__':
    # Automatic graphs generation:
    num_of_congestion_controls = 3
    num_of_time_samples = 60000
    data_paths = [DATA_EXAMPLE]
    absolute_result_paths = [RESULT_EXAMPLE]
    chunk_sizes = [1, 10, 50, 100, 200, 300, 400, 500, 1000, 10000, 60000]
    model_path = os.path.join(ABSOLUTE_PATH,
                              r'graphs/thesis_prime/classification of different datasets using a single trained model- in multiple routers- Results15/model/state_dict.pt')
    diverse_data_path = [r'filtered_0', r'filtered_0.5', r'filtered_0.9']
    if IS_SAMPLE_RATE:
        csv_filename = "ConnStat"
    else:
        csv_filename = "single_connection"
    bg_flows = [0, 15, 30, 60, 75]
    sleep_duration = 0
    for data_path, absolute_result_path in zip(data_paths, absolute_result_paths):
        for bg_flow in bg_flows:
            for net_type in get_net_types():
                filter = get_filter_from_data_path(data_path)
                for chunk_size in chunk_sizes:
                    deepcci_num_of_time_samples = int(chunk_size / 1000)
                    if deepcci_num_of_time_samples < 1:
                        deepcci_num_of_time_samples = 1
                    if chunk_size == 60000:
                        DEVICE = "cpu"
                    results_path = get_results_path(absolute_result_path, bg_flow, filter, net_type.parameters, chunk_size)
                    sim_params = SimParams(data_path, absolute_result_path, results_path, model_path, diverse_data_path, csv_filename, IS_DATA_SAMPLE, IS_DIVERSE_DATA, IS_FULL_SESSION, sleep_duration, SAVE_MODEL_PT, IS_MININET)
                    model_params = ModelParams(num_of_congestion_controls, num_of_time_samples, net_type, bg_flow, chunk_size, IS_BATCH)
                    model_training.main_train_and_validate(sim_params, model_params, DEVICE)
