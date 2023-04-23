import torch.nn as nn
import math

class deepcci_net(nn.Module):
    def __init__(self, chunk_size, deepcci_num_of_time_samples):
        super(deepcci_net, self).__init__()
        self.deepcci_num_of_time_samples = deepcci_num_of_time_samples
        self.channels = 64
        self.num_layers = 100
        self.hidden_size = 64
        self.max_pool_size = math.floor((chunk_size / deepcci_num_of_time_samples) ** 0.2) # 4 * (CHUNK_SIZE / 60000)
        # 1
        self.conv1d_layer1_1 = nn.Conv1d(self.channels, self.channels, kernel_size=3, padding=1)
        self.BN_layer1_1 = nn.BatchNorm1d(self.channels)
        self.Relu_layer_1 = nn.ReLU(inplace=False)
        self.conv1d_layer2_1 = nn.Conv1d(self.channels, self.channels, kernel_size=3, padding=1)
        self.BN_layer2_1 = nn.BatchNorm1d(self.channels)
        self.Relu_layer_1 = nn.ReLU(inplace=False)
        self.maxpool_layer_1 = nn.MaxPool1d(kernel_size=self.max_pool_size, stride=self.max_pool_size, ceil_mode=False)
        # 2
        self.conv1d_layer1_2 = nn.Conv1d(self.channels, self.channels, kernel_size=3, padding=1)
        self.BN_layer1_2 = nn.BatchNorm1d(self.channels)
        self.Relu_layer_2 = nn.ReLU(inplace=False)
        self.conv1d_layer2_2 = nn.Conv1d(self.channels, self.channels, kernel_size=3, padding=1)
        self.BN_layer2_2 = nn.BatchNorm1d(self.channels)
        self.Relu_layer_2 = nn.ReLU(inplace=False)
        self.maxpool_layer_2 = nn.MaxPool1d(kernel_size=self.max_pool_size, stride=self.max_pool_size, ceil_mode=False)
        # 3
        self.conv1d_layer1_3 = nn.Conv1d(self.channels, self.channels, kernel_size=3, padding=1)
        self.BN_layer1_3 = nn.BatchNorm1d(self.channels)
        self.Relu_layer_3 = nn.ReLU(inplace=False)
        self.conv1d_layer2_3 = nn.Conv1d(self.channels, self.channels, kernel_size=3, padding=1)
        self.BN_layer2_3 = nn.BatchNorm1d(self.channels)
        self.Relu_layer_3 = nn.ReLU(inplace=False)
        self.maxpool_layer_3 = nn.MaxPool1d(kernel_size=self.max_pool_size, stride=self.max_pool_size, ceil_mode=False)
        # 4
        self.conv1d_layer1_4 = nn.Conv1d(self.channels, self.channels, kernel_size=3, padding=1)
        self.BN_layer1_4 = nn.BatchNorm1d(self.channels)
        self.Relu_layer_4 = nn.ReLU(inplace=False)
        self.conv1d_layer2_4 = nn.Conv1d(self.channels, self.channels, kernel_size=3, padding=1)
        self.BN_layer2_4 = nn.BatchNorm1d(self.channels)
        self.Relu_layer_4 = nn.ReLU(inplace=False)
        self.maxpool_layer_4 = nn.MaxPool1d(kernel_size=self.max_pool_size, stride=self.max_pool_size, ceil_mode=False)
        # 5
        self.conv1d_layer1_5 = nn.Conv1d(self.channels, self.channels, kernel_size=3, padding=1)
        self.BN_layer1_5 = nn.BatchNorm1d(self.channels)
        self.Relu_layer_5 = nn.ReLU(inplace=False)
        self.conv1d_layer2_5 = nn.Conv1d(self.channels, self.channels, kernel_size=3, padding=1)
        self.BN_layer2_5 = nn.BatchNorm1d(self.channels)
        self.Relu_layer_5 = nn.ReLU(inplace=False)
        self.maxpool_layer_5 = nn.MaxPool1d(kernel_size=self.max_pool_size, stride=self.max_pool_size, ceil_mode=False)

        # 1
        self.BN_layer_1 = nn.BatchNorm1d(100)
        self.lstm_layer_1 = nn.LSTM(input_size=self.channels, num_layers=1, hidden_size=100)
        # 2
        self.BN_layer_2 = nn.BatchNorm1d(100)
        self.lstm_layer_2 = nn.LSTM(input_size=100, num_layers=1, hidden_size=100)
        # 3
        self.BN_layer_3 = nn.BatchNorm1d(100)
        self.lstm_layer_3 = nn.LSTM(input_size=100, num_layers=1, hidden_size=100)

        self.init_fg_bias()

        self.conv1 = nn.Conv1d(1, self.channels, kernel_size=1)

        self.first_BN_layer = (nn.BatchNorm1d(self.channels))
        self.last_conv1d_layer = nn.Conv1d(100, 5, kernel_size=1, padding=1)
        self.last_BN_layer = nn.BatchNorm1d(5)

    def init_fg_bias(self):
        for names in self.lstm_layer_1._all_weights:
            for name in filter(lambda n: "bias" in n, names):
                bias = getattr(self.lstm_layer_1, name)
                n = bias.size(0)
                start, end = n // 4, n // 2
                bias.data[start:end].fill_(1.)
        for names in self.lstm_layer_2._all_weights:
            for name in filter(lambda n: "bias" in n, names):
                bias = getattr(self.lstm_layer_2, name)
                n = bias.size(0)
                start, end = n // 4, n // 2
                bias.data[start:end].fill_(1.)
        for names in self.lstm_layer_3._all_weights:
            for name in filter(lambda n: "bias" in n, names):
                bias = getattr(self.lstm_layer_3, name)
                n = bias.size(0)
                start, end = n // 4, n // 2
                bias.data[start:end].fill_(1.)

    # Defining the forward pass
    def forward(self, x):
        x = self.conv1(x)
        # 1
        residual = x
        x = self.conv1d_layer1_1(x)
        x = self.BN_layer1_1(x)
        x = self.Relu_layer_1(x)
        x = self.conv1d_layer2_1(x)
        x = self.BN_layer2_1(x)
        x = x + residual
        x = self.Relu_layer_1(x)
        x = self.maxpool_layer_1(x)
        # 2
        residual = x
        x = self.conv1d_layer1_2(x)
        x = self.BN_layer1_2(x)
        x = self.Relu_layer_2(x)
        x = self.conv1d_layer2_2(x)
        x = self.BN_layer2_2(x)
        x = x + residual
        x = self.Relu_layer_2(x)
        x = self.maxpool_layer_2(x)
        # 3
        residual = x
        x = self.conv1d_layer1_3(x)
        x = self.BN_layer1_3(x)
        x = self.Relu_layer_3(x)
        x = self.conv1d_layer2_3(x)
        x = self.BN_layer2_3(x)
        x = x + residual
        x = self.Relu_layer_3(x)
        x = self.maxpool_layer_3(x)
        # 4
        residual = x
        x = self.conv1d_layer1_4(x)
        x = self.BN_layer1_4(x)
        x = self.Relu_layer_4(x)
        x = self.conv1d_layer2_4(x)
        x = self.BN_layer2_4(x)
        x = x + residual
        x = self.Relu_layer_4(x)
        x = self.maxpool_layer_4(x)
        # 5
        residual = x
        x = self.conv1d_layer1_5(x)
        x = self.BN_layer1_5(x)
        x = self.Relu_layer_5(x)
        x = self.conv1d_layer2_5(x)
        x = self.BN_layer2_5(x)
        x = x + residual
        x = self.Relu_layer_5(x)
        x = self.maxpool_layer_5(x)

        x = self.first_BN_layer(x)
        if not self.max_pool_size > 1:
            x = x.mean(2, keepdims=True)

        # 1
        x = x.transpose(1, 2)
        x = x.transpose(0, 1)
        x, _ = self.lstm_layer_1(x)
        x = x.transpose(0, 1)
        x = x.transpose(1, 2)
        x = self.BN_layer_1(x)
        # 2
        x = x.transpose(1, 2)
        x = x.transpose(0, 1)
        x, _ = self.lstm_layer_2(x)
        x = x.transpose(0, 1)
        x = x.transpose(1, 2)
        x = self.BN_layer_2(x)
        # 3
        x = x.transpose(1, 2)
        x = x.transpose(0, 1)
        x, _ = self.lstm_layer_3(x)
        x = x.transpose(0, 1)
        x = x.transpose(1, 2)
        x = self.BN_layer_3(x)

        last_maxpool_layer = nn.MaxPool1d(kernel_size=math.floor(x.shape[2] / self.deepcci_num_of_time_samples), stride=math.floor(x.shape[2] / self.deepcci_num_of_time_samples), ceil_mode=False)
        x = last_maxpool_layer(x)
        x = self.last_conv1d_layer(x)
        x = self.last_BN_layer(x)

        x_variant = x[:, 0:3, 0:self.deepcci_num_of_time_samples]

        return x_variant
