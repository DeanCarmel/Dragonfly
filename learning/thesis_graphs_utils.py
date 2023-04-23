import re
import statistics
import matplotlib.pyplot as plt
from learning.results_manager import *
from learning.env import *


def create_accuracy_vs_epoch_graph(results_path, txt_filename, plot_name, short_epoch=False):
    my_net_accuracy = []
    my_net_all_parameters_accuracy = []
    deepcci_net_accuracy = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        res_file = os.path.join(res_dir, txt_filename)
        with open(res_file) as f:
            accuracy = f.readlines()
            accuracy = [x.strip() for x in accuracy]
            accuracy = [float(i) for i in accuracy]
            if "5parameters" in res_file:
                my_net_all_parameters_accuracy = accuracy
            else:
                if "cbiq" in res_file:
                    my_net_accuracy = accuracy
                else:
                    deepcci_net_accuracy = accuracy
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    if short_epoch:
        p1, = plt.plot(my_net_accuracy[0:45])
        p2, = plt.plot(my_net_all_parameters_accuracy[0:45])
        p3, = plt.plot(deepcci_net_accuracy[0:45])
    else:
        p1, = plt.plot(my_net_accuracy)
        p2, = plt.plot(my_net_all_parameters_accuracy)
        p3, = plt.plot(deepcci_net_accuracy)
    plt.legend((p1, p2, p3), ('CBIQ', 'All Parameters', 'Deepcci'))
    axes = plt.gca()
    axes.set(xlabel='epoch', ylabel='f1')
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)

def create_f1_vs_session_duration_graph(results_path, txt_filename, plot_name):
    my_net_accuracy_list, my_net_all_parameters_accuracy_list, deepcci_net_accuracy_list = get_f1_vs_session_duration(
        results_path, txt_filename, plot_name, None)
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    my_net_accuracy_list = sorted(my_net_accuracy_list, key=lambda tup: tup[1])
    session_duration = [x[1] for x in my_net_accuracy_list]
    accuracy = [x[0] for x in my_net_accuracy_list]
    p1, = plt.plot(session_duration, accuracy)
    # plt.title(plot_name)
    if my_net_all_parameters_accuracy_list:
        my_net_all_parameters_accuracy_list = sorted(my_net_all_parameters_accuracy_list, key=lambda tup: tup[1])
        session_duration = [x[1] for x in my_net_all_parameters_accuracy_list]
        accuracy = [x[0] for x in my_net_all_parameters_accuracy_list]
        p2, = plt.plot(session_duration, accuracy)
    if deepcci_net_accuracy_list:
        deepcci_net_accuracy_list = sorted(deepcci_net_accuracy_list, key=lambda tup: tup[1])
        session_duration = [x[1] for x in deepcci_net_accuracy_list]
        accuracy = [x[0] for x in deepcci_net_accuracy_list]
        p3, = plt.plot(session_duration, accuracy)
    if p2 is not None and p3 is not None:
        plt.legend((p1, p2, p3), ('CBIQ', 'All Parameters', 'Deepcci'))
    else:
        if p3 is not None:
            plt.legend((p1, p3), ('CBIQ', 'Deepcci'))
    axes = plt.gca()
    axes.set(xlabel='session duration[seconds]', ylabel='f1')
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_f1_vs_number_of_flows_graph(results_path, txt_filename, plot_name, session_duration):
    my_net_accuracy_list = []
    my_net_all_parameters_accuracy_list = []
    deepcci_net_accuracy_list = []
    for dir_name in os.listdir(results_path):
        number_of_flows = re.findall(r'\d+', dir_name)
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        my_net_accuracy, my_net_all_parameters_accuracy, deepcci_net_accuracy = get_f1_vs_nubmber_of_flows(
            res_dir, txt_filename, plot_name, session_duration)
        if my_net_accuracy:
            my_net_accuracy_list_accuracy = [x[0] for x in my_net_accuracy]
            my_net_accuracy_list.append((int(number_of_flows[0]), my_net_accuracy_list_accuracy[0]))
        if my_net_all_parameters_accuracy:
            my_net_all_parameters_accuracy_list_accuracy = [x[0] for x in my_net_all_parameters_accuracy]
            my_net_all_parameters_accuracy_list.append(
                (int(number_of_flows[0]), my_net_all_parameters_accuracy_list_accuracy[0]))
        if deepcci_net_accuracy:
            deepcci_net_accuracy_list_accuracy = [x[0] for x in deepcci_net_accuracy]
            deepcci_net_accuracy_list.append((int(number_of_flows[0]), deepcci_net_accuracy_list_accuracy[0]))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    # plt.title(plot_name)
    my_net_accuracy_list = sorted(my_net_accuracy_list, key=lambda tup: tup[0])
    number_of_flows = [x[0] for x in my_net_accuracy_list]
    accuracy = [x[1] for x in my_net_accuracy_list]
    p1, = plt.plot(number_of_flows, accuracy)
    p2 = p3 = None
    if my_net_all_parameters_accuracy_list:
        my_net_all_parameters_accuracy_list = sorted(my_net_all_parameters_accuracy_list, key=lambda tup: tup[0])
        number_of_flows = [x[0] for x in my_net_all_parameters_accuracy_list]
        accuracy = [x[1] for x in my_net_all_parameters_accuracy_list]
        p2, = plt.plot(number_of_flows, accuracy)
    if deepcci_net_accuracy_list:
        deepcci_net_accuracy_list = sorted(deepcci_net_accuracy_list, key=lambda tup: tup[0])
        number_of_flows = [x[0] for x in deepcci_net_accuracy_list]
        accuracy = [x[1] for x in deepcci_net_accuracy_list]
        p3, = plt.plot(number_of_flows, accuracy)
    if p2 is not None and p3 is not None:
        plt.legend((p1, p2, p3), ('CBIQ', 'All Parameters', 'Deepcci'))
    else:
        if p3 is not None:
            plt.legend((p1, p3), ('CBIQ', 'Deepcci'))
    axes = plt.gca()
    axes.set(xlabel='number of flows', ylabel='f1')
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_f1_vs_background_flows_multiple_session_duration_graph(results_path, txt_filename, plot_name,
                                                                  session_duration):
    my_net_all_parameters_accuracy_list = []
    graph_legend = ["All Parameters", "CBIQ", "Deepcci", "Throughput"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir or "multiple_rtr" in res_dir:
            continue
        for sub_dir in os.listdir(os.path.join(results_path, dir_name, res_dir)):
            if session_duration not in sub_dir:
                continue
            for graph_type in graph_legend:
                if graph_type in res_dir:
                    graph_legend_aligned.append(graph_type)
            result_path = os.path.join(results_path, dir_name, res_dir, sub_dir)
            my_net_all_parameters_accuracy_list.append(
                get_f1_result_for_subfolders_from_accuracy(result_path, txt_filename, plot_name))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(my_net_all_parameters_accuracy_list)):
        my_net_all_parameters_accuracy = sorted(my_net_all_parameters_accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in my_net_all_parameters_accuracy]
        y_axis = [x[1] for x in my_net_all_parameters_accuracy]
        plt.plot(x_axis, y_axis)
    axes = plt.gca()
    axes.set(xlabel='number of flows', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_multiple_rtr_graph(results_path, txt_filename, plot_name):
    f1_list = []
    f1_sublist = []
    graph_legend = ["All Parameters", "CBIQ", "Deepcci", "Throughput"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for sub_dir in os.listdir(os.path.join(results_path, dir_name, res_dir)):
            result_path = os.path.join(results_path, dir_name, res_dir, sub_dir)
            if not os.path.isdir(result_path) or "old" in result_path:
                continue
            f1_sublist.append(get_f1_result_multiple_rtr(result_path, txt_filename))
        f1_list.append(f1_sublist)
        f1_sublist = []
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    rtr1 = [x[0][0] for x in f1_list]
    rtr2 = [x[1][0] for x in f1_list]
    plt.figure(figsize=(10, 5))
    ind = np.arange(len(rtr1))
    width = 0.3
    plt.bar(ind, rtr1, width)
    plt.bar(ind + width, rtr2, width)
    plt.xticks(ind + width / 2, graph_legend_aligned)
    axes = plt.gca()
    axes.set(xlabel='Datasets', ylabel='F1')
    axes.grid()
    plt.legend(("rtr2", "rtr1"), loc="best")
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_f1_vs_background_flows_for_pre_trained_model_and_session_durations(results_path, txt_filename, plot_name):
    my_net_all_parameters_accuracy_list = []
    graph_legend = ["10 seconds", "20 seconds", "60 seconds"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        for sub_dir_name in os.listdir(res_dir):
            sub_res_dir = os.path.join(results_path, dir_name, sub_dir_name)
            if not os.path.isdir(sub_res_dir) or "_model" in sub_res_dir:
                continue
            for graph_type in graph_legend:
                if graph_type in sub_res_dir:
                    graph_legend_aligned.append(graph_type)
            result_path = os.path.join(results_path, dir_name, res_dir, sub_res_dir)
            my_net_all_parameters_accuracy_list.append(
                get_pre_trained_model_result(result_path, txt_filename, plot_name))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(my_net_all_parameters_accuracy_list)):
        my_net_all_parameters_accuracy = sorted(my_net_all_parameters_accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in my_net_all_parameters_accuracy]
        y_axis = [x[1] for x in my_net_all_parameters_accuracy]
        plt.plot(x_axis, y_axis)
    axes = plt.gca()
    axes.set(xlabel='number of flows', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_f1_vs_number_of_flows(results_path, txt_filename, plot_name):
    my_net_all_parameters_accuracy_list = []
    graph_legend = ["All Parameters", "CBIQ", "Deepcci", "Throughput"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "Throughput" in res_dir:
            continue
        for res_sub_dir in os.listdir(os.path.join(results_path, dir_name, res_dir)):
            if "model" in res_sub_dir:
                continue
            for graph_type in graph_legend:
                if graph_type in res_dir:
                    graph_legend_aligned.append(graph_type)
            result_path = os.path.join(results_path, dir_name, res_dir, res_sub_dir)
            my_net_all_parameters_accuracy_list.append(
                get_pre_trained_model_result(result_path, txt_filename, plot_name))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(my_net_all_parameters_accuracy_list)):
        my_net_all_parameters_accuracy = sorted(my_net_all_parameters_accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in my_net_all_parameters_accuracy]
        y_axis = [x[1] for x in my_net_all_parameters_accuracy]
        plt.plot(x_axis, y_axis)
    axes = plt.gca()
    axes.set(xlabel='number of flows', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)
    # plt.title(plot_name)
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_f1_vs_background_flows_for_pre_trained_model(results_path, txt_filename, plot_name):
    my_net_all_parameters_accuracy_list = []
    my_net_all_parameters_scatter = []
    graph_legend = ["Diverse Training Pre- Trained Model", "0 Background Flows Pre- Trained Model",
                    "75 Background Flows Pre- Trained Model"]
    scatter_legend = ["0", "15", "30", "75"]
    graph_legend_aligned = []
    scatter_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        if "points" in res_dir:
            for scatter_type in scatter_legend:
                if scatter_type in dir_name:
                    scatter_legend_aligned.append(scatter_type)
            if "added_points" in res_dir:
                my_net_all_parameters_scatter.append(
                    get_pre_trained_model_result(os.path.join(results_path, dir_name), txt_filename, plot_name, True))
            else:
                my_net_all_parameters_scatter.append(
                    get_pre_trained_model_result(os.path.join(results_path, dir_name), txt_filename, plot_name, False))
        else:
            for graph_type in graph_legend:
                if graph_type in dir_name:
                    graph_legend_aligned.append(graph_type)
            result_path = os.path.join(results_path, dir_name, res_dir)
            my_net_all_parameters_accuracy_list.append(
                get_pre_trained_model_result(result_path, txt_filename, plot_name))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(my_net_all_parameters_accuracy_list)):
        my_net_all_parameters_accuracy = sorted(my_net_all_parameters_accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in my_net_all_parameters_accuracy]
        y_axis = [x[1] for x in my_net_all_parameters_accuracy]
        plt.plot(x_axis, y_axis)
    for i in range(len(my_net_all_parameters_scatter)):
        my_net_all_parameters_accuracy = sorted(my_net_all_parameters_scatter[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in my_net_all_parameters_accuracy]
        y_axis = [x[1] for x in my_net_all_parameters_accuracy]
        plt.scatter(x_axis, y_axis, color="red")
    axes = plt.gca()
    axes.set(xlabel='number of flows', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_diverse_multiple_rtr_graph(results_path, txt_filename, plot_name, session_duration):
    f1_list = []
    graph_legend = ["5parameters", "cbiq", "deepcci", "throughput"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        f1_list.append(get_f1_result_for_subfolders(res_dir, txt_filename, plot_name))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    rtr1 = [x[0][1] for x in f1_list]
    rtr2 = [x[1][1] for x in f1_list]

    plt.figure(figsize=(10, 5))
    ind = np.arange(len(rtr1))
    width = 0.3
    plt.bar(ind, rtr1, width)
    plt.bar(ind + width, rtr2, width)
    plt.xticks(ind + width / 2, graph_legend_aligned)

    axes = plt.gca()
    axes.set(xlabel='Datasets', ylabel='F1')
    axes.grid()
    plt.legend(("rtr2", "rtr1"), loc="best")
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_result_for_each_parameter_graph(results_path, txt_filename, plot_name):
    f1_list = []
    graph_legend = ["CBIQ", "In Throughput", "Out Throughput", "Number of Drops", "Number of Retransmits",
                    "Send Time Gap"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        f1_list.append(get_f1_result(res_dir, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    f1 = [x[0][1] for x in f1_list]

    plt.figure(figsize=(10, 5))
    ind = np.arange(len(f1))
    width = 0.3
    plt.bar(ind, f1, width)
    plt.xticks(ind + width / 2, graph_legend_aligned)

    axes = plt.gca()
    axes.set(xlabel='Parameter', ylabel='F1')
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_networks_comparison_graph(results_path, txt_filename, plot_name):
    f1_list = []
    graph_legend = ["Fully Connected", "Deepcci", "CNN"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        f1_list.append(get_f1_result(res_dir, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    plt.figure(figsize=(10, 5))
    f1 = [x[0][1] for x in f1_list]
    f1[0], f1[1], f1[2] = f1[1], f1[2], f1[0]
    graph_legend_aligned[0], graph_legend_aligned[1], graph_legend_aligned[2] = graph_legend_aligned[1], graph_legend_aligned[2], graph_legend_aligned[0]
    ind = np.arange(len(f1))
    width = 0.3
    plt.bar(ind, f1, width)
    plt.xticks(ind, graph_legend_aligned, fontsize=8, fontweight='bold')
    axes = plt.gca()
    axes.set(ylabel='F1')
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_online_classification_graph(results_path, txt_filename, plot_name):
    f1_list = []
    graph_legend = ["CBIQ", "Throughput", "All Parameters", "Deepcci"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        f1_list.append(get_f1_result(res_dir, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    f1 = [x[0][1] for x in f1_list]

    plt.figure(figsize=(10, 5))
    ind = np.arange(len(f1))
    width = 0.3
    plt.bar(ind, f1, width)
    plt.xticks(ind, graph_legend_aligned)

    axes = plt.gca()
    axes.set(xlabel='Parameter', ylabel='F1')
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_f1_vs_background_flows_for_online_classification_graph(results_path, txt_filename, plot_name):
    my_net_all_parameters_accuracy_list = []
    my_net_all_parameters_scatter = []
    graph_legend = ["Deepcci", "CBIQ", "Throughput"]  # ,"All Parameters"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        result_path = os.path.join(results_path, dir_name, res_dir)
        my_net_all_parameters_accuracy_list.append(
            get_f1_result_for_subfolders_from_online_accuracy(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(my_net_all_parameters_accuracy_list)):
        my_net_all_parameters_accuracy = sorted(my_net_all_parameters_accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in my_net_all_parameters_accuracy]
        y_axis = [x[1] for x in my_net_all_parameters_accuracy]
        plt.plot(x_axis, y_axis)
    for i in range(len(my_net_all_parameters_scatter)):
        my_net_all_parameters_accuracy = sorted(my_net_all_parameters_scatter[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in my_net_all_parameters_accuracy]
        y_axis = [x[1] for x in my_net_all_parameters_accuracy]
        plt.scatter(x_axis, y_axis, color="red")
    axes = plt.gca()
    axes.set(xlabel='number of flows', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_f1_vs_background_flows_for_online_classification_with_sampling_graph(results_path, txt_filename, plot_name):
    f1_list = []
    graph_legend = ["CBIQ", "Throughput", "All Parameters", "Deepcci"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        f1_list.append(get_f1_result_for_sampling_rate(res_dir, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    f1 = [x[0][1] for x in f1_list]

    plt.figure(figsize=(10, 5))
    ind = np.arange(len(f1))
    width = 0.3
    plt.bar(ind, f1, width)
    plt.xticks(ind, graph_legend_aligned)

    axes = plt.gca()
    axes.set(xlabel='Parameter', ylabel='F1')
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_f1_vs_parameter_for_online_classification_with_sampling_graph(results_path, txt_filename, plot_name):
    my_net_all_parameters_accuracy_list = []
    graph_legend = ["Deepcci", "CBIQ", "Throughput", "All Parameters"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        result_path = os.path.join(results_path, dir_name, res_dir)
        my_net_all_parameters_accuracy_list.append(
            get_f1_result_for_subfolders_from_online_accuracy(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(my_net_all_parameters_accuracy_list)):
        my_net_all_parameters_accuracy = sorted(my_net_all_parameters_accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in my_net_all_parameters_accuracy]
        y_axis = [x[1] for x in my_net_all_parameters_accuracy]
        plt.plot(x_axis, y_axis)
    axes = plt.gca()
    axes.set(xlabel='number of flows', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def get_f1_vs_session_duration(results_path, txt_filename, plot_name, single_session_duration):
    my_net_accuracy_list = []
    my_net_all_parameters_accuracy_list = []
    deepcci_net_accuracy_list = []
    for dir_name in os.listdir(results_path):
        if "old" in dir_name:
            continue
        session_duration = re.findall(r'\d+', dir_name)
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        if single_session_duration is not None:
            if len(re.findall(str(single_session_duration) + '_', res_dir)) == 0:
                continue
        res_file = os.path.join(res_dir, txt_filename)
        try:
            with open(res_file) as f:
                accuracy = f.readlines()
                accuracy = [x.strip() for x in accuracy]
                accuracy = [float(i) for i in accuracy]
                if "my_net" in res_file:
                    if "5parameters" in res_file:
                        my_net_all_parameters_accuracy_list.append(
                            (statistics.mean(accuracy[80:]), int(session_duration[1]) / 1000))
                    else:
                        my_net_accuracy_list.append((statistics.mean(accuracy[80:]), int(session_duration[0]) / 1000))
                else:
                    deepcci_net_accuracy_list.append((accuracy[1], int(session_duration[0]) / 1000))
        except:
            continue
    return my_net_accuracy_list, my_net_all_parameters_accuracy_list, deepcci_net_accuracy_list


def get_f1_vs_nubmber_of_flows(results_path, txt_filename, plot_name, single_session_duration):
    my_net_accuracy_list = []
    my_net_all_parameters_accuracy_list = []
    deepcci_net_accuracy_list = []
    for dir_name in os.listdir(results_path):
        if "old" in dir_name:
            continue
        session_duration = re.findall(r'\d+', dir_name)
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        if single_session_duration is not None:
            if len(re.findall(str(single_session_duration) + '_', res_dir)) == 0:
                continue
        res_file = os.path.join(res_dir, txt_filename)
        try:
            with open(res_file) as f:
                accuracy = f.readlines()
                accuracy = [x.strip() for x in accuracy]
                accuracy = [float(i) for i in accuracy]
                if "my_net" in res_file:
                    if "5parameters" in res_file:
                        my_net_all_parameters_accuracy_list.append(
                            (statistics.mean(accuracy[80:]), int(session_duration[1]) / 1000))
                    else:
                        my_net_accuracy_list.append((statistics.mean(accuracy[80:]), int(session_duration[0]) / 1000))
                else:
                    # deepcci_net_accuracy_list.append((accuracy[1], int(session_duration[0]) / 1000))
                    deepcci_net_accuracy_list.append((statistics.mean(accuracy[80:]), int(session_duration[0]) / 1000))
        except:
            continue
    return my_net_accuracy_list, my_net_all_parameters_accuracy_list, deepcci_net_accuracy_list


def get_f1_result(results_path, txt_filename):
    my_net_all_parameters_accuracy_list = []
    if not os.path.isdir(results_path):
        return
    x_axis = re.findall(r'\d+', results_path)
    res_file = os.path.join(results_path, txt_filename)
    try:
        with open(res_file) as f:
            accuracy = f.readlines()
            my_net_all_parameters_accuracy_list.append((int(x_axis[0]), float(accuracy[-1])))
    except:
        pass
    return my_net_all_parameters_accuracy_list


def get_f1_result_multiple_rtr(results_path, txt_filename):
    my_net_all_parameters_accuracy_list = []
    if not os.path.isdir(results_path):
        return
    res_file = os.path.join(results_path, txt_filename)
    try:
        with open(res_file) as f:
            accuracy = f.readlines()
            my_net_all_parameters_accuracy_list.append(float(accuracy[-1]))
    except:
        pass
    return my_net_all_parameters_accuracy_list


def get_f1_result_for_subfolders(results_path, txt_filename, plot_name):
    my_net_all_parameters_accuracy_list = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        if "old" in res_dir or "model" in dir_name:
            continue
        x_axis = re.findall(r'\d+', dir_name)
        res_file = os.path.join(res_dir, txt_filename)
        try:
            with open(res_file) as f:
                accuracy = f.readlines()
                my_net_all_parameters_accuracy_list.append((int(x_axis[0]), float(accuracy[1])))
        except:
            continue
    return my_net_all_parameters_accuracy_list


def get_f1_result_for_subfolders_from_accuracy(results_path, txt_filename, plot_name):
    my_net_all_parameters_accuracy_list = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        if "old" in res_dir or "model" in dir_name:
            continue
        x_axis = re.findall(r'\d+', dir_name)
        res_file = os.path.join(res_dir, txt_filename)
        try:
            with open(res_file) as f:
                accuracy = f.readlines()
                my_net_all_parameters_accuracy_list.append((int(x_axis[0]), float(accuracy[-1])))
        except:
            continue
    return my_net_all_parameters_accuracy_list


def get_pre_trained_model_result(results_path, txt_filename, plot_name, is_scatter=False):
    my_net_all_parameters_accuracy_list = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        if "model" in dir_name or "old" in dir_name:
            continue
        x_axis = re.findall(r'\d+', dir_name)
        res_file = os.path.join(res_dir, txt_filename)
        with open(res_file) as f:
            accuracy = f.readlines()
            accuracy = [x.strip() for x in accuracy]
            if is_scatter:
                my_net_all_parameters_accuracy_list.append((int(x_axis[0]), float(accuracy[-1])))
            else:
                my_net_all_parameters_accuracy_list.append((int(x_axis[0]), float(accuracy[1])))
    return my_net_all_parameters_accuracy_list


def get_f1_result_for_subfolders_from_online_accuracy(results_path, txt_filename):
    my_net_all_parameters_accuracy_list = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        if "old" in res_dir or "model" in dir_name:
            continue
        x_axis = re.findall(r'\d+', res_dir)
        res_file = os.path.join(res_dir, txt_filename)
        try:
            with open(res_file) as f:
                accuracy = f.readlines()
                my_net_all_parameters_accuracy_list.append((int(x_axis[-1]), float(accuracy[-1])))
        except:
            continue
    return my_net_all_parameters_accuracy_list


def get_f1_result_for_sampling_rate(results_path, txt_filename):
    my_net_all_parameters_accuracy_list = []
    if not os.path.isdir(results_path):
        return
    x_axis = re.findall(r'\d+', results_path)
    res_file = os.path.join(results_path, txt_filename)
    try:
        with open(res_file) as f:
            accuracy = f.readlines()
            my_net_all_parameters_accuracy_list.append((int(x_axis[0]), float(accuracy[-1])))
    except:
        pass
    return my_net_all_parameters_accuracy_list


# Online Filtering CBIQ debugging:
def get_online_filtered_cbiq(results_path, txt_filename):
    if not os.path.isdir(results_path):
        return
    from os import listdir
    from os.path import isfile, join
    dir_files = [f for f in listdir(results_path) if isfile(join(results_path, f))]
    for file in dir_files:
        if txt_filename in file:
            res_file = os.path.join(results_path, file)
            break
    try:
        df = pd.read_csv(res_file, index_col=None, header=0)
        return df['CBIQ']
    except:
        pass


def create_online_filtered_cbiq_graphs(results_path, txt_filename):
    cbiq_accuracy_lists = []
    graph_legend = ["in_ffill_out_ffill", "in_ffill_out_ffill_after_cbiq_calculation",
                    "in_ffill_out_interpolation_after_cbiq_calculation", "in_interpolation_out_interpolation",
                    "in_interpolation_out_interpolation_after_cbiq_calculation"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        result_path = os.path.join(results_path, dir_name, res_dir)
        cbiq_accuracy_lists.append(get_online_filtered_cbiq(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    timestamp = list(range(0, 10000, 1))
    i = 1
    for cbiq_accuracy_list in cbiq_accuracy_lists:
        plt.subplot(1, 5, i)
        plt.plot(timestamp, cbiq_accuracy_list)
        i = i + 1
    axes = plt.gca()
    axes.set(xlabel='cbiq calculation', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plot_name = "online_filtered_cbiq_graphs"
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_f1_vs_online_filtering(results_path, txt_filename, plot_name):
    accuracy_list = []
    graph_legend = ["deepcci", "cbiq", "throughput"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        result_path = os.path.join(results_path, dir_name, res_dir)
        accuracy_list.append(get_f1_result_for_online_filtering(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(accuracy_list)):
        accuracy = sorted(accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in accuracy]
        y_axis = [x[1] for x in accuracy]
        plt.plot(x_axis, y_axis)
    axes = plt.gca()
    axes.set(xlabel='filter [%]', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def get_f1_result_for_online_filtering(results_path, txt_filename):
    accuracy_list = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        if "old" in res_dir:
            continue
        x_axis = re.findall(r'\d+', res_dir)
        res_file = os.path.join(res_dir, txt_filename)
        try:
            with open(res_file) as f:
                accuracy = f.readlines()
                if txt_filename == 'validation_accuracy_per_type':
                    accuracy_string = []
                    for line in accuracy:
                        accuracy_string.append((re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", line)))
                    accuracy_float = []
                    for line in accuracy_string:
                        accuracy_float.append([float(i) for i in line])
                    acc_float = []
                    for index in range(len(accuracy_float[0])):
                        # acc_float.append(([a[index] for a in accuracy_float][-1]))
                        """
                        if "2500" in res_file:
                            acc_float.append(max([a[index] for a in accuracy_float]))
                        else:
                        """
                        acc_float.append(max([a[index] for a in accuracy_float]))
                    acc_float[1] , acc_float[2] = acc_float[2], acc_float[1]
                    accuracy_list.append((int(x_axis[-1]), acc_float))
                else:
                    accuracy_list.append((int(x_axis[-1]), float(accuracy[-1])))
        except:
            continue
    return accuracy_list


def get_accuracy_result_for_online_filtering(results_path, txt_filename):
    accuracy_list = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        if "old" in res_dir:
            continue
        x_axis = re.findall(r'\d+', res_dir)
        res_file = os.path.join(res_dir, txt_filename)
        try:
            with open(res_file) as f:
                accuracy = f.readlines()
                accuracy_list.append((int(x_axis[-1]), float(accuracy[-1])))
        except:
            continue
    return accuracy_list


def create_online_vs_offline_graph(results_path, txt_filename, plot_name):
    f1_list = []
    graph_legend = ["CBIQ", "Throughput", "Deepcci"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir in res_dir:
            continue
        f1 = []
        for sub_dir in os.listdir(os.path.join(results_path, dir_name, res_dir)):
            for graph_type in graph_legend:
                if graph_type in sub_dir:
                    graph_legend_aligned.append(graph_type)
            result_path = os.path.join(results_path, dir_name, res_dir, sub_dir)
            f1.append(get_f1_result(result_path, txt_filename))
        f1_list.append(f1)
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    offline = [x[0][1] for x in f1_list[0]]
    online = [x[0][1] for x in f1_list[1]]

    plt.figure(figsize=(10, 5))
    ind = np.arange(len(offline))
    width = 0.3
    plt.bar(ind, offline, width)
    plt.bar(ind + width, online, width)
    plt.xticks(ind, graph_legend_aligned)

    axes = plt.gca()
    axes.set(xlabel='Parameter', ylabel='F1')
    axes.grid()
    plt.legend(("online", "offline"), loc="best")
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_physical_f1_vs_online_filtering(results_path, txt_filename, plot_name):
    accuracy_list = []
    graph_legend = ["Deepcci", "CBIQ", "Throughput"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        result_path = os.path.join(results_path, dir_name, res_dir)
        accuracy_list.append(get_f1_result_for_online_filtering(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(accuracy_list)):
        accuracy = sorted(accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in accuracy]
        y_axis = [x[1] for x in accuracy]
        plt.plot(x_axis, y_axis)
    axes = plt.gca()
    axes.set(xlabel='filter [%]', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_physical_f1_vs_chunk_size(results_path, txt_filename, plot_name):
    accuracy_list = []
    graph_legend = ["Deepcci", "CBIQ", "Capture Arrival Time"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir or "MyDeepcci" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        result_path = os.path.join(results_path, dir_name, res_dir)
        accuracy_list.append(get_f1_result_for_online_filtering(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(accuracy_list)):
        accuracy = sorted(accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in accuracy]
        y_axis = [x[1] for x in accuracy]
        # plt.xlim(1.1 * max(x_axis), 0)
        plt.plot(x_axis, y_axis)
    axes = plt.gca()
    axes.set(xlabel='chunk size [ms]', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_physical_f1_vs_background_flows(results_path, txt_filename, plot_name):
    accuracy_list = []
    graph_legend = ["Deepcci", "CBIQ"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        result_path = os.path.join(results_path, dir_name, res_dir)
        accuracy_list.append(get_f1_result_for_online_filtering(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(accuracy_list)):
        accuracy = sorted(accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in accuracy]
        y_axis = [x[1] for x in accuracy]
        plt.plot(x_axis, y_axis)
    axes = plt.gca()
    axes.set(xlabel='background flows', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_physical_full_session_vs_sesion_sample(results_path, txt_filename, plot_name):
    f1_list = []
    graph_legend = ["CBIQ", "Deepcci"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir in res_dir:
            continue
        f1 = []
        for sub_dir in os.listdir(os.path.join(results_path, dir_name, res_dir)):
            for graph_type in graph_legend:
                if graph_type in sub_dir:
                    graph_legend_aligned.append(graph_type)
            result_path = os.path.join(results_path, dir_name, res_dir, sub_dir)
            f1.append(get_f1_result(result_path, txt_filename))
        f1_list.append(f1)
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    full_session = [x[0][1] for x in f1_list[0]]
    session_sample = [x[0][1] for x in f1_list[1]]

    plt.figure(figsize=(10, 5))
    ind = np.arange(len(full_session))
    width = 0.3
    plt.bar(ind, full_session, width)
    plt.bar(ind + width, session_sample, width)
    plt.xticks(ind, graph_legend_aligned)

    axes = plt.gca()
    axes.set(xlabel='Parameter', ylabel='F1')
    axes.grid()
    plt.legend(("full_session", "session_sample"), loc="best")
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_physical_f1_vs_small_chunk_size(results_path, txt_filename, plot_name):
    accuracy_list = []
    graph_legend = ["Deepcci", "CBIQ"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        result_path = os.path.join(results_path, dir_name, res_dir)
        accuracy_list.append(get_f1_result_for_online_filtering(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(accuracy_list)):
        accuracy = sorted(accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in accuracy]
        y_axis = [x[1] for x in accuracy]
        # plt.xlim(1.1 * max(x_axis), 0)
        plt.plot(x_axis, y_axis)
    axes = plt.gca()
    axes.set(xlabel='chunk size [ms]', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_physical_f1_for_each_cc_vs_chunk_size(results_path, txt_filename, plot_name):
    accuracy_list = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir or "Deepcci" in res_dir or "MyDeepcci" in res_dir:
            continue
        result_path = os.path.join(results_path, dir_name, res_dir)
        accuracy_list.append(get_f1_result_for_online_filtering(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(accuracy_list)):
        accuracy = sorted(accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in accuracy]
        y_axis = [x[1] for x in accuracy]
    for i in range(len(y_axis)):
        try:
            plt.plot(x_axis, [y[i] for y in y_axis])
        except:
            continue
    axes = plt.gca()
    axes.set(xlabel='chunk size', ylabel='F1')
    axes.grid()
    plt.legend(["bbr", "cubic", "reno"])  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_physical_f1_vs_physical_filtering(results_path, txt_filename, plot_name):
    accuracy_list = []
    graph_legend = ["Deepcci", "CBIQ", "MyDeepcci", "Capture Arrival Time"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type == dir_name:
                graph_legend_aligned.append(graph_type)
        result_path = os.path.join(results_path, dir_name, res_dir)
        accuracy_list.append(get_f1_result_for_online_filtering(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(accuracy_list)):
        accuracy = sorted(accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in accuracy]
        y_axis = [x[1] for x in accuracy]
        plt.plot(x_axis, y_axis)
    axes = plt.gca()
    axes.set(xlabel='filter [%]', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def get_bottleneck_result(results_path, txt_filename):
    my_net_all_parameters_accuracy_list = []
    if not os.path.isdir(results_path):
        return
    x_axis = re.findall(r'\d+', results_path)
    res_file = os.path.join(results_path, "100", txt_filename)
    try:
        with open(res_file) as f:
            accuracy = f.readlines()
            my_net_all_parameters_accuracy_list.append((int(x_axis[0]), float(accuracy[-1])))
    except:
        pass
    return my_net_all_parameters_accuracy_list


def create_bottleneck_comparison_graph(results_path, txt_filename, plot_name):
    f1_list = []
    graph_legend = ["All Parameters", "Capture Arrival Time", "CBIQ", "Deepcci", "Throughput", "In Throughput",
                    "Out Throughput"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        f1_list.append(get_bottleneck_result(res_dir, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    plt.figure(figsize=(10, 5))
    f1 = [x[0][1] for x in f1_list]
    ind = np.arange(len(f1))
    width = 0.3
    plt.bar(ind, f1, width)
    plt.xticks(ind, graph_legend_aligned)
    axes = plt.gca()
    axes.set(xlabel='Parameter', ylabel='F1')
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_cbiq_throughput_graph(results_path, txt_filename, plot_name):
    f1_list = []
    graph_legend = ["All Parameters", "Capture Arrival Time", "CBIQ", "Deepcci", "Throughput", "In Throughput",
                    "Out Throughput"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        f1_list.append(get_bottleneck_result(res_dir, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    plt.figure(figsize=(10, 5))
    f1 = [x[0][1] for x in f1_list]
    ind = np.arange(len(f1))
    width = 0.3
    plt.bar(ind, f1, width)
    plt.xticks(ind, graph_legend_aligned)
    axes = plt.gca()
    axes.set(xlabel='Parameter', ylabel='F1')
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


# New folder architecture:

def get_f1_vs_session_duration_results(results_path, txt_filename):
    x_axis = re.findall(r'\d+', results_path)
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir or "not_in_use" in res_dir:
            continue
    res_file = os.path.join(res_dir, txt_filename)
    with open(res_file) as f:
        accuracy = (int(x_axis[-1]), float(f.readlines()[-1]))
    return accuracy


def create_f1_vs_session_duration_graph(results_path, txt_filename, plot_name):
    accuracy_list = []
    graph_legend = ["CBIQ"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        result_path = os.path.join(results_path, dir_name, res_dir)
        accuracy_list.append(get_f1_vs_session_duration_results(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    accuracy = sorted(accuracy_list, key=lambda tup: tup[0])
    x_axis = [x[0] for x in accuracy]
    y_axis = [x[1] for x in accuracy]
    # plt.xlim(1.1 * max(x_axis), 0)
    plt.plot(x_axis, y_axis)
    axes = plt.gca()
    axes.set(xlabel='Sub- Interval [ms]', ylabel='F1', fontsize=16)
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def get_f1_vs_background_flows_results(results_path, txt_filename):
    x_axis = re.findall(r'\d+', results_path)
    res_file = os.path.join(results_path, txt_filename)
    with open(res_file) as f:
        accuracy = (int(x_axis[1]), float(f.readlines()[-1]))
    return accuracy


def create_f1_vs_background_flows_graph(results_path, txt_filename, plot_name):
    accuracy_list = []
    graph_legend = ["Final Algorithmm, Deepcci"]
    graph_legend_aligned = []
    dirs_names = os.listdir(results_path)
    for dir_name in dirs_names:
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "not_in_use" in res_dir:
            continue
        while os.path.isdir(res_dir):
            dir_name = os.listdir(res_dir)[0]
            if os.path.isdir(os.path.join(res_dir, dir_name)):
                res_dir = os.path.join(res_dir, dir_name)
            else:
                break
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        result_path = os.path.join(results_path, dir_name, res_dir)
        accuracy_list.append(get_f1_vs_background_flows_results(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    accuracy = sorted(accuracy_list, key=lambda tup: tup[0])
    x_axis = [x[0] for x in accuracy]
    y_axis = [x[1] for x in accuracy]
    # plt.xlim(1.1 * max(x_axis), 0)
    plt.plot(x_axis, y_axis)
    axes = plt.gca()
    axes.set(xlabel='background flows', ylabel='F1')
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def get_cbiq_vs_parameters_session_duration_results(results_path, txt_filename):
    accuracy_list = []
    x_axis = re.findall(r'\d+', results_path)
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir or "not in use" in res_dir:
            continue
        res_file = os.path.join(res_dir, txt_filename)
        x_axis = re.findall(r'\d+', res_file)
        with open(res_file) as f:
            accuracy_list.append((int(x_axis[-1]), float(f.readlines()[-1])))
    return accuracy_list


# Results31:
def create_cbiq_vs_parameters_session_sample_graph(results_path, txt_filename, plot_name):
    f1_list = []
    # graph_legend = ["All Parameters", "Capture Arrival Time", "CBIQ", "Deepcci", "In Throughput"]
    graph_legend = ["Dragonfly", "Dragonfly with only CBIQ", "Deepcci"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir or "not in use" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type == dir_name:
                graph_legend_aligned.append(graph_type)
        f1_list.append(get_cbiq_vs_parameters_session_duration_results(res_dir, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    plt.figure(figsize=(10, 5))
    for i in range(len(f1_list)):
        accuracy = sorted(f1_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in accuracy]
        y_axis = [x[1] for x in accuracy]
        if graph_legend_aligned[i] == "Dragonfly with only CBIQ":
            plt.plot(x_axis, y_axis, linestyle='dashed')
        else:
            plt.plot(x_axis, y_axis)
        plt.legend(graph_legend_aligned)
    axes = plt.gca()
    plt.xlabel('Sub- Interval [ms]', fontsize=16)
    plt.ylabel('F1', fontsize=16)
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=700)


def get_bottleneck_vs_no_bottelneck_result(results_path, txt_filename):
    my_net_all_parameters_accuracy_list = []
    inner_dir = os.listdir(results_path)[0]
    x_axis = re.findall(r'\d+', inner_dir)
    res_file = os.path.join(results_path, inner_dir, txt_filename)
    try:
        with open(res_file) as f:
            accuracy = f.readlines()
            my_net_all_parameters_accuracy_list.append((int(x_axis[0]), float(accuracy[-1])))
    except:
        return
    return my_net_all_parameters_accuracy_list


# Results30.1- 30.2:
def create_bottleneck_vs_no_bottleneck_graph(results_path, txt_filename, plot_name):
    f1_list = []
    # graph_legend = ["All Parameters", "Capture Arrival Time", "CBIQ", "Deepcci", "In Throughput"]
    graph_legend = ["All  Parameters", "CBIQ  + In Throughput", "Capture  Time Gap", "CBIQ", "In  Throughput", "Out  Throughput"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir or "not in use" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type == dir_name:
                graph_legend_aligned.append(graph_type)
        f1 = get_bottleneck_vs_no_bottelneck_result(res_dir, txt_filename)
        if f1 is not None:
            f1_list.append(get_bottleneck_vs_no_bottelneck_result(res_dir, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    plt.figure(figsize=(10, 5))
    f1 = [x[0][1] for x in f1_list]
    ind = np.arange(len(f1))
    width = 0.3
    f1, graph_legend_aligned = sort_lists(f1, graph_legend_aligned)
    plt.bar(ind, f1, width)
    graph_legend_aligned_new_lines = []
    for str in graph_legend_aligned:
        graph_legend_aligned_new_lines.append(str.replace('  ', '\n'))
    plt.xticks(ind, graph_legend_aligned_new_lines, fontsize=12)
    axes = plt.gca()
    axes.set(ylabel='F1')
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=500)


def sort_lists(list1, list2):
    zipped_lists = zip(list1, list2)
    sorted_pairs = sorted(zipped_lists, reverse=False)
    tuples = zip(*sorted_pairs)
    list1, list2 = [list(tuple) for tuple in tuples]
    return list1, list2


def create_f1_vs_background_flows2(results_path, txt_filename, plot_name):
    my_net_all_parameters_accuracy_list = []
    my_net_all_parameters_scatter = []
    graph_legend = ["Deepcci", "Dragonfly", "Dragonfly with only CBIQ"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type == dir_name:
                graph_legend_aligned.append(graph_type)
        result_path = os.path.join(results_path, dir_name, res_dir)
        my_net_all_parameters_accuracy_list.append(
            get_f1_result_for_subfolders_from_online_accuracy(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(my_net_all_parameters_accuracy_list)):
        my_net_all_parameters_accuracy = sorted(my_net_all_parameters_accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in my_net_all_parameters_accuracy]
        y_axis = [x[1] for x in my_net_all_parameters_accuracy]
        if graph_legend_aligned[i] == "Dragonfly with only CBIQ":
            plt.plot(x_axis, y_axis, linestyle='dashed')
        else:
            plt.plot(x_axis, y_axis)
    for i in range(len(my_net_all_parameters_scatter)):
        my_net_all_parameters_accuracy = sorted(my_net_all_parameters_scatter[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in my_net_all_parameters_accuracy]
        y_axis = [x[1] for x in my_net_all_parameters_accuracy]
        plt.scatter(x_axis, y_axis, color="red")
    axes = plt.gca()
    plt.xlabel('Number of Flows', fontsize=16)
    plt.ylabel('F1', fontsize=16)
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def get_filtered_results(results_path, txt_filename):
    accuracy_list = []
    x_axis = re.findall(r'\d+', results_path)
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir or "not in use" in res_dir:
            continue
        res_file = os.path.join(res_dir, txt_filename)
        x_axis = re.findall(r'\d+', res_file)
        with open(res_file) as f:
            accuracy_list.append((int(x_axis[-1]), float(f.readlines()[-1])))
    return accuracy_list


def create_physical_filtering_graph(results_path, txt_filename, plot_name):
    f1_list = []
    # graph_legend = ["All Parameters", "Capture Arrival Time", "CBIQ", "Deepcci", "In Throughput"]
    graph_legend = ["Dragonfly", "Dragonfly with only CBIQ", "Deepcci"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir or "not in use" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type == dir_name:
                graph_legend_aligned.append(graph_type)
        f1_list.append(get_filtered_results(res_dir, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    plt.figure(figsize=(10, 5))
    for i in range(len(f1_list)):
        accuracy = sorted(f1_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in accuracy]
        y_axis = [x[1] for x in accuracy]
        if graph_legend_aligned[i] == "Dragonfly with only CBIQ":
            plt.plot(x_axis, y_axis, linestyle='dashed')
        else:
            plt.plot(x_axis, y_axis)
        plt.legend(graph_legend_aligned)
    axes = plt.gca()
    plt.xlabel('Dropped % in Sampling', fontsize=16)
    plt.ylabel('F1', fontsize=16)
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_inputs_graph(result_path, input_path):
    stat_df = pd.read_csv(os.path.join(result_path, input_path),index_col=None, header=0)
    # stat_df = stat_df.iloc[::10, :]
    fig,ax = plt.subplots()
    # make a plot
    ax.scatter(stat_df['timestamp'], stat_df['CBIQ'], color="red", marker="*", s=0.5)
    # set x-axis label
    ax.set_xlabel("Timestamp [sec]", fontsize=16)
    # set y-axis label
    ax.set_ylabel("CBIQ [Bytes]", color="red", fontsize=8)
    ax2=ax.twinx()
    # make a plot with different y-axis using second axis object
    stat_df_throughput = stat_df['In Throughput'].groupby(stat_df.index // 1000).cumsum()
    stat_df_throughput = stat_df['In Throughput'].groupby(stat_df.index // 10).sum()
    ax2.scatter(stat_df.iloc[::10, :]["timestamp"], stat_df_throughput,color="blue", marker="*", s=0.5)
    ax2.set_ylabel("In Throughput [Mbps]", color="blue", fontsize=10)
    plt.savefig(os.path.join(result_path, "graph.png"), dpi=400)

def create_cbiq_vs_throughput_semliogx(results_path, txt_filename, plot_name):
    f1_list = []
    graph_legend = ["CBIQ", "In Throughput"]
    graph_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir or "not in use" in res_dir:
            continue
        for graph_type in graph_legend:
            if graph_type in dir_name:
                graph_legend_aligned.append(graph_type)
        f1_list.append(get_cbiq_vs_parameters_session_duration_results(res_dir, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    plt.figure(figsize=(10, 5))
    for i in range(len(f1_list)):
        accuracy = sorted(f1_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in accuracy]
        y_axis = [x[1] for x in accuracy]
        plt.plot(x_axis, y_axis)
    plt.legend(graph_legend_aligned)
    axes = plt.gca()
    plt.xlabel('Sub- Interval [ms]', fontsize=16)
    plt.ylabel('F1', fontsize=16)
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)

def create_background_flows_for_pre_trained_model(results_path, txt_filename, plot_name):
    my_net_all_parameters_accuracy_list = []
    my_net_all_parameters_scatter = []
    graph_legend = ["Dragonfly", "Dragonfly trained with only 0 Flows",
                    "Dragonfly trained with only 75 Flows"]
    scatter_legend = ["0", "15", "30", "75"]
    graph_legend_aligned = []
    scatter_legend_aligned = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        if "points" in res_dir:
            for scatter_type in scatter_legend:
                if scatter_type in dir_name:
                    scatter_legend_aligned.append(scatter_type)
            if "added_points" in res_dir:
                my_net_all_parameters_scatter.append(
                    get_pre_trained_model_result(os.path.join(results_path, dir_name), txt_filename, plot_name, True))
            else:
                my_net_all_parameters_scatter.append(
                    get_pre_trained_model_result(os.path.join(results_path, dir_name), txt_filename, plot_name, False))
        else:
            for graph_type in graph_legend:
                if graph_type == dir_name:
                    graph_legend_aligned.append(graph_type)
            result_path = os.path.join(results_path, dir_name, res_dir)
            my_net_all_parameters_accuracy_list.append(
                get_pre_trained_model_result(result_path, txt_filename, plot_name))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    my_net_all_parameters_accuracy_list[0], my_net_all_parameters_accuracy_list[1] = my_net_all_parameters_accuracy_list[1], my_net_all_parameters_accuracy_list[0]
    graph_legend_aligned[0], graph_legend_aligned[1] = graph_legend_aligned[1], graph_legend_aligned[0]

    my_net_all_parameters_accuracy_list[1], my_net_all_parameters_accuracy_list[2] = my_net_all_parameters_accuracy_list[2], my_net_all_parameters_accuracy_list[1]
    graph_legend_aligned[1], graph_legend_aligned[2] = graph_legend_aligned[2], graph_legend_aligned[1]
    for i in range(len(my_net_all_parameters_accuracy_list)):
        my_net_all_parameters_accuracy = sorted(my_net_all_parameters_accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in my_net_all_parameters_accuracy]
        y_axis = [x[1] for x in my_net_all_parameters_accuracy]
        plt.plot(x_axis, y_axis)
    for i in range(len(my_net_all_parameters_scatter)):
        my_net_all_parameters_accuracy = sorted(my_net_all_parameters_scatter[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in my_net_all_parameters_accuracy]
        y_axis = [x[1] for x in my_net_all_parameters_accuracy]
        plt.scatter(x_axis, y_axis, color="red")
    axes = plt.gca()
    plt.xlabel('Number of Flows', fontsize=16)
    plt.ylabel('F1', fontsize=16)
    axes.grid()
    plt.legend(graph_legend_aligned)  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_accuracy_vs_epoch_graph(results_path, txt_filename, plot_name):
    my_net_accuracy = []
    my_net_all_parameters_accuracy = []
    deepcci_net_accuracy = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir):
            continue
        res_file = os.path.join(res_dir, txt_filename)
        with open(res_file) as f:
            accuracy = f.readlines()
            accuracy = [x.strip() for x in accuracy]
            accuracy = [float(i) for i in accuracy]
            if "Dragonfly with" in res_file:
                my_net_accuracy = accuracy
            else:
                if "Dragonfly" in res_file:
                    my_net_all_parameters_accuracy = accuracy
                else:
                    deepcci_net_accuracy = accuracy
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    p1, = plt.plot(my_net_accuracy[0:50], linestyle='dashed')
    p2, = plt.plot(my_net_all_parameters_accuracy[0:50])
    p3, = plt.plot(deepcci_net_accuracy[0:50])
    plt.legend((p2, p1, p3), ('Dragonfly', 'Dragonfly with only CBIQ', 'Deepcci'))
    axes = plt.gca()
    axes.set_ylim([0, 1])
    axes.set(xlabel='Epoch', ylabel='Accuracy')
    axes.grid()
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)


def create_f1_for_each_cc_vs_chunk_size(results_path, txt_filename, plot_name):
    accuracy_list = []
    for dir_name in os.listdir(results_path):
        res_dir = os.path.join(results_path, dir_name)
        if not os.path.isdir(res_dir) or "old" in res_dir or "Deepcci" in res_dir or "MyDeepcci" in res_dir:
            continue
        result_path = os.path.join(results_path, dir_name, res_dir)
        accuracy_list.append(get_f1_result_for_online_filtering(result_path, txt_filename))
    plt.cla()  # clear the current axes
    plt.clf()  # clear the current figure
    for i in range(len(accuracy_list)):
        accuracy = sorted(accuracy_list[i], key=lambda tup: tup[0])
        x_axis = [x[0] for x in accuracy]
        y_axis = [x[1] for x in accuracy]
    for i in range(len(y_axis)):
        try:
            plt.plot(x_axis, [y[i] / 100 for y in y_axis])
        except:
            continue
    axes = plt.gca()
    plt.xlabel('Sub- Interval [ms]', fontsize=16)
    plt.ylabel('F1', fontsize=16)
    axes.grid()
    plt.legend(["BBR", "CUBIC", "RENO"])  # , loc=(0.75,0.5))
    plt.savefig(os.path.join(results_path, plot_name), dpi=600)

if __name__ == '__main__':
    result_path = "/home/dean/PycharmProjects/cwnd_clgo_classifier/learning/result/0 background flows/example filter"
    create_cbiq_vs_parameters_session_sample_graph(result_path, "validation_accuracy", "f1 score")