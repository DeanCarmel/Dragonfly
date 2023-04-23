from learning.utils import *
import math
from torch.nn import Linear, ReLU, Sequential, Conv2d, MaxPool2d, Module, BatchNorm2d

NUM_OF_CONV_FILTERS = 50
NUM_OF_HIDDEN_LAYERS = 100

class my_net(Module):
    def __init__(self, num_of_classification_parameters, chunk_size, num_of_congestion_controls, num_of_time_samples):
        super(my_net, self).__init__()
        self.cnn_layers = Sequential(
            Conv2d(1, NUM_OF_CONV_FILTERS, kernel_size=(3, num_of_classification_parameters), stride=1, padding=(1, 0)), # NUM_OF_CLASSIFICATION_PARAMETERS
            BatchNorm2d(NUM_OF_CONV_FILTERS),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=(2, 1), stride=1),
            Conv2d(NUM_OF_CONV_FILTERS, NUM_OF_CONV_FILTERS, kernel_size=(3, 1), stride=1, padding=(1, 0)),
            BatchNorm2d(NUM_OF_CONV_FILTERS),
            ReLU(inplace=True),
            MaxPool2d(kernel_size=(2, 1), stride=1),
        )

        self.linear_layers = Sequential(
            Linear(NUM_OF_CONV_FILTERS * 1 * (num_of_time_samples - 2) * 1, num_of_classification_parameters))
        self.num_of_congestion_controls = num_of_congestion_controls
        self.max_pool_size = math.floor(chunk_size ** 0.2)
        self.conv2d_layer1 = Conv2d(1, NUM_OF_CONV_FILTERS, kernel_size=(3, num_of_classification_parameters), stride=1, padding=(1, 0))
        self.BN_layer1 = BatchNorm2d(NUM_OF_CONV_FILTERS)
        self.Relu_layer1 = ReLU(inplace=True)
        self.maxpool_layer1 = MaxPool2d(kernel_size=(self.max_pool_size, 1), stride=self.max_pool_size)
        self.conv2d_layer2 = Conv2d(NUM_OF_CONV_FILTERS, NUM_OF_CONV_FILTERS, kernel_size=(3, 1), stride=1, padding=(1, 0))
        self.BN_layer2 = BatchNorm2d(NUM_OF_CONV_FILTERS)
        self.Relu_layer2 = ReLU(inplace=True)
        self.maxpool_layer2 = MaxPool2d(kernel_size=(self.max_pool_size, 1), stride=self.max_pool_size)
        self.conv2d_layer3 = Conv2d(NUM_OF_CONV_FILTERS, NUM_OF_CONV_FILTERS, kernel_size=(3, 1), stride=1, padding=(1, 0))
        self.BN_layer3 = BatchNorm2d(NUM_OF_CONV_FILTERS)
        self.Relu_layer3 = ReLU(inplace=True)
        self.maxpool_layer3 = MaxPool2d(kernel_size=(self.max_pool_size, 1), stride=self.max_pool_size)
        self.conv2d_layer4 = Conv2d(NUM_OF_CONV_FILTERS, NUM_OF_CONV_FILTERS, kernel_size=(3, 1), stride=1, padding=(1, 0))
        self.BN_layer4 = BatchNorm2d(NUM_OF_CONV_FILTERS)
        self.Relu_layer4 = ReLU(inplace=True)
        self.maxpool_layer4 = MaxPool2d(kernel_size=(self.max_pool_size, 1), stride=self.max_pool_size)
        self.conv2d_layer5 = Conv2d(NUM_OF_CONV_FILTERS, NUM_OF_CONV_FILTERS, kernel_size=(3, 1), stride=1, padding=(1, 0))
        self.BN_layer5 = BatchNorm2d(NUM_OF_CONV_FILTERS)
        self.Relu_layer5 = ReLU(inplace=True)
        self.maxpool_layer5 = MaxPool2d(kernel_size=(self.max_pool_size, 1), stride=self.max_pool_size)
        self.conv1d_layer5 = torch.nn.Conv1d(NUM_OF_CONV_FILTERS, NUM_OF_HIDDEN_LAYERS, kernel_size=3, padding=1)
        self.gru = torch.nn.GRU(input_size=NUM_OF_HIDDEN_LAYERS, hidden_size=NUM_OF_HIDDEN_LAYERS, num_layers=2)
        self.lstm = torch.nn.LSTM(input_size=NUM_OF_HIDDEN_LAYERS, num_layers=1, hidden_size=NUM_OF_HIDDEN_LAYERS)
        self.BN_final = torch.nn.BatchNorm1d(NUM_OF_HIDDEN_LAYERS)
        self.conv2d_final = Conv2d(NUM_OF_CONV_FILTERS, self.num_of_congestion_controls, kernel_size=(3, 1), stride=1, padding=(1, 0))
        self.linear = Linear(NUM_OF_CONV_FILTERS * 1 * (num_of_time_samples - 2) * 1, num_of_congestion_controls)

    # Defining the forward pass
    def forward(self, x):
        x = self.conv2d_layer1(x)
        x = self.BN_layer1(x)
        x = self.Relu_layer1(x)
        x = self.maxpool_layer1(x)
        x = self.conv2d_layer2(x)
        x = self.BN_layer2(x)
        x = self.Relu_layer2(x)
        x = self.maxpool_layer2(x)
        x = self.conv2d_layer3(x)
        x = self.BN_layer3(x)
        x = self.Relu_layer3(x)
        x = self.maxpool_layer3(x)
        x = self.conv2d_layer4(x)
        x = self.BN_layer4(x)
        x = self.Relu_layer4(x)
        x = self.maxpool_layer4(x)
        x = self.conv2d_layer5(x)
        x = self.BN_layer5(x)
        x = self.Relu_layer5(x)
        x = self.maxpool_layer5(x)

        x = self.conv2d_final(x)
        x = x.mean(2)
        x = x.squeeze(2)
        return x
