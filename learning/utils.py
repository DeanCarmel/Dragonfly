import torch
import numpy
import torch.utils as torch_utils
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
import matplotlib.pyplot as plt
from learning.results_manager import *

TRAINING_VALIDATION_RATIO = 0.3
BATCH_SIZE = 32
IS_SHUFFLE = False

def reshape_deepcci_data(input_data, validation_data, input_labeling, validation_labeling, chunk_size, deepcci_num_of_time_samples):
    reshape_vector = numpy.ones(deepcci_num_of_time_samples)
    labeling_size = len(input_labeling)
    input_labeling = numpy.kron(input_labeling, reshape_vector)
    input_labeling = input_labeling.reshape(labeling_size, deepcci_num_of_time_samples)
    validation_size = len(validation_data)
    validation_labeling = numpy.kron(validation_labeling, reshape_vector)
    validation_labeling = validation_labeling.reshape(validation_size, deepcci_num_of_time_samples)
    # converting training dataframes into torch format
    input_data = torch.from_numpy(input_data)
    input_data = input_data.reshape(len(input_data), 1, chunk_size)
    # converting the target into torch format
    input_labeling = torch.from_numpy(input_labeling)
    # converting validation dataframes into torch format
    validation_data = torch.from_numpy(validation_data)
    validation_data = validation_data.reshape(len(validation_data), 1, chunk_size)
    # converting the target into torch format
    validation_labeling = torch.from_numpy(validation_labeling)
    return input_data, validation_data, input_labeling, validation_labeling

def reshape_my_data(input_data, validation_data, input_labeling, validation_labeling, chunk_size, num_of_classification_parameters):
    # converting training dataframes into torch format
    input_data = input_data.reshape(len(input_data), 1, chunk_size, num_of_classification_parameters)
    input_data = torch.from_numpy(input_data)  # convert to tensor
    # converting the target into torch format
    input_labeling = torch.from_numpy(input_labeling)
    # converting validation dataframes into torch format
    validation_data = validation_data.reshape(len(validation_data), 1, chunk_size, num_of_classification_parameters)
    validation_data = torch.from_numpy(validation_data)
    # converting the target into torch format
    validation_labeling = torch.from_numpy(validation_labeling)
    return input_data, validation_data, input_labeling, validation_labeling

def create_dataloader(data, labeling, is_batch):
    dataset = torch_utils.data.TensorDataset(data, labeling)
    if is_batch:
        dataloader = torch_utils.data.DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=IS_SHUFFLE)#batch_size=int(len(data) / NUM_OF_BATCHES))
    else:
        dataloader = torch_utils.data.DataLoader(dataset, batch_size=len(data))
    return dataloader

def create_data(sim_params, model_params, normalization_type, is_deepcci, is_batch):
    result_manager = ResultsManager(sim_params, model_params, normalization_type, is_deepcci)
    training_labeling = result_manager.get_train_df()
    input_dataframe = result_manager.get_normalized_df_list()
    # converting the list to numpy array after pre- processing
    input_numpy_dataframe = [dataframe.to_numpy() for dataframe in input_dataframe]
    input_data = np.array(input_numpy_dataframe)
    # defining the target
    input_labeling = np.array(training_labeling['label'].values)
    # creating validation set
    input_data, validation_data, input_labeling, validation_labeling = train_test_split(input_data, input_labeling, test_size=TRAINING_VALIDATION_RATIO)
    if is_deepcci:
        input_data, validation_data, input_labeling, validation_labeling = reshape_deepcci_data(input_data, validation_data, input_labeling, validation_labeling, model_params.chunk_size, model_params.net_type.get_deepcci_num_of_time_samples())
    else:
        input_data, validation_data, input_labeling, validation_labeling = reshape_my_data(input_data, validation_data, input_labeling, validation_labeling, model_params.chunk_size,  model_params.net_type.get_num_of_classification_parameters())
    # creating dataloaders:
    train_loader = create_dataloader(input_data, input_labeling, is_batch)
    val_loader = create_dataloader(validation_data, validation_labeling, is_batch)
    return train_loader, val_loader

def accuracy_aux(output, target, topk=(1,), is_f1=True):
    """Computes the accuracy over the k top predictions for the specified values of k"""
    maxk = max(topk)

    curr_output = output
    curr_target = target

    with torch.no_grad():
        batch_size = curr_target.size(0)
        _, pred = curr_output.topk(maxk, 1, True, True)
        pred = pred.t()
        correct = pred.eq(curr_target.view(1, -1).expand_as(pred))
        if len(topk) == 1:
            if is_f1:
                return f1_score(target.cpu(), np.argmax(output.cpu(), axis=1), average='macro')
            correct_k = correct[:1].view(-1).float().sum(0, keepdim=True)
            return correct_k.mul_(100.0 / batch_size)
        res = []
        for k in topk:
            correct_k = correct[:k].view(-1).float().sum(0, keepdim=True)
            res.append(correct_k.mul_(100.0 / batch_size))
    return res


def accuracy(output, target, topk, is_deepcci):
    """Computes the accuracy over the k top predictions for the specified values of k"""
    last_dim_size = output.size(-1)
    result = []
    maxk = max(topk)
    if not is_deepcci:
        curr_output = output
        curr_target = target
        return accuracy_aux(curr_output, curr_target, topk)
    else:
        for i in range(last_dim_size):
            curr_output = output[:, :, i:i + 1]
            curr_output = curr_output.squeeze(-1)
            curr_target = target[:, i:i + 1]
            curr_target = curr_target.squeeze(-1)
            res = accuracy_aux(curr_output, curr_target, topk)
            result.append(res)
    if len(topk) == 1:
        return torch.mean(torch.FloatTensor(result))
    result_summary = []
    for i in range(2):
        result_summary.append([])
    for i in range(last_dim_size):
        for j, elem in enumerate(result[i]):
            result_summary[j].append(elem)
    for i in range(2):
        result_summary[i] = torch.FloatTensor(result_summary[i])
        result_summary[i] = [torch.mean(result_summary[i], -1)]
    return result_summary

def accuracy_per_type(output, target, topk=(1,)):
    maxk = max(topk)
    curr_output = output
    curr_target = target
    num_of_classes = len(output[0])
    with torch.no_grad():
        batch_size = curr_target.size(0)
        _, pred = curr_output.topk(maxk, 1, True, True)
        pred = pred.t()
        acc = [0 for c in range(num_of_classes)]
        for c in range(num_of_classes):
            num_of_traget = curr_target == c
            correct = pred.eq(curr_target.view(1, -1).expand_as(pred)) * num_of_traget
            acc[c] = correct[:1].view(-1).float().sum(0, keepdim=True).mul_(100.0 / (num_of_traget.sum())).item()
    return acc


class Graph_Creator:
    def __init__(self, loss, accuracy, accuracy_per_type, num_of_epochs, is_batch, plot_file_name="Graph.png", plot_fig_name="Statistics"):
        # clear plt before starting new statistics, otherwise it add up to the previous one
        self.is_batch = is_batch
        self.loss = loss
        self.accuracy = accuracy
        self.accuracy_per_type = accuracy_per_type
        plt.cla()  # clear the current axes
        plt.clf()  # clear the current figure
        fig1, (ax1, ax2, ax3) = plt.subplots(3, constrained_layout=True)
        fig1.suptitle(plot_fig_name)
        ax1.set(xlabel='epoch', ylabel='loss')
        ax1.set_xlim([0, num_of_epochs])
        #ax1.set_ylim([0, numpy.amax(loss)])
        ax2.set(xlabel='epoch', ylabel='accuracy')
        ax2.set_xlim([0, num_of_epochs])
        self.fig1 = fig1
        self.loss_ax = ax1
        self.accuracy_ax = ax2
        self.accuracy_per_type_ax = ax3
        if self.is_batch:
            self.average_loss = numpy.mean(loss, axis=1)
            self.average_accuracy = numpy.mean(accuracy, axis=1)
            self.average_accuracy_per_type = numpy.mean(accuracy_per_type, axis=1)
            fig2, (ax4, ax5) = plt.subplots(2, constrained_layout=True)
            fig2.suptitle(plot_fig_name)
            ax4.set(xlabel='epoch', ylabel='loss')
            ax4.set_xlim([0, num_of_epochs])
            ax5.set(xlabel='epoch', ylabel='accuracy')
            ax5.set_xlim([0, num_of_epochs])
            self.fig2 = fig2
            self.batches_loss_ax = ax4
            self.batches_accuracy_ax = ax5
        self.plot_file_name = plot_file_name

    def create_loss_plot(self, loss, ax):
        loss_df = pd.DataFrame(loss)
        loss_df.plot(kind='line', ax=ax, title='loss')
        self.write_to_file("loss", loss)

    def create_accuracy_plot(self, accuracy, ax):
        accuracy_df = pd.DataFrame(accuracy)
        accuracy_df.plot(kind='line', ax=ax, title='accuracy')
        self.write_to_file("accuracy", accuracy)

    def create_accuracy_per_type_plot(self, accuracy_per_type, ax):
        accuracy_per_type_df = pd.DataFrame(accuracy_per_type)
        for type in range(accuracy_per_type_df.shape[1]):
            accuracy_per_type_df[type].plot(kind='line', ax=ax, title='accuracy per type')
        ax.legend(["bbr", "cubic", "reno"])
        self.write_to_file("accuracy_per_type.csv", accuracy_per_type)

    def create_graphs(self):
        if self.is_batch:
            self.create_loss_plot(self.average_loss, self.loss_ax)
            self.create_accuracy_plot(self.average_accuracy, self.accuracy_ax)
            self.create_accuracy_per_type_plot(self.average_accuracy_per_type, self.accuracy_per_type_ax)
            self.loss_ax.grid()
            self.accuracy_ax.grid()
            self.accuracy_per_type_ax.grid()
            self.save_and_show(self.fig1)
            self.plot_file_name = self.plot_file_name.replace('.png', ('_batches_figures.png'))
            self.create_loss_plot(self.loss, self.batches_loss_ax)
            self.create_accuracy_plot(self.accuracy, self.batches_accuracy_ax)
            # self.create_accuracy_per_type_plot(self.accuracy_per_type, self.batches_accuracy_per_type_ax)
            self.batches_loss_ax.grid()
            self.batches_accuracy_ax.grid()
            self.save_and_show(self.fig2)
        else:
            self.create_loss_plot(self.loss, self.loss_ax)
            self.create_accuracy_plot(self.accuracy, self.accuracy_ax)
            self.create_accuracy_per_type_plot(self.average_accuracy_per_type, self.accuracy_per_type_ax)
            self.loss_ax.grid()
            self.accuracy_ax.grid()
            self.save_and_show(self.fig1)

    def write_to_file(self, type, list):
        with open(self.plot_file_name.replace('.png', ('_' + type)), 'w') as f:
            for item in list:
                f.write("%s\n" % item)

    def save_and_show(self, fig):
        fig.savefig(self.plot_file_name, dpi=600)
        plt.close(fig)

