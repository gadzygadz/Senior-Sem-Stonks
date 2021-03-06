import os
def clear_static():
    for root, dirs, files in os.walk('src/static'):
        for file in files:
            #append the file name to the list
            print(os.path.join(root,file))
            os.remove(os.path.join(root,file))

    for root, dirs, files in os.walk('static'):
        for file in files:
            #append the file name to the list
            print(os.path.join(root,file))
            os.remove(os.path.join(root,file))

import datetime as dt
import pandas_datareader as pdr
import pandas as pd

# https://cnvrg.io/pytorch-lstm/

def get_stock_data(tag: str, start_date: dt.datetime, end_date: dt.datetime) -> pd.core.frame.DataFrame:

    for i in ['data', 'img']:
        os.system(f'mkdir {i}')
    # forces tag into a list
    tag = [tag]
    # attempts to pull the data
    try:
        # get it from yahoo
        data = pdr.get_data_yahoo(tag, start=start_date, end=end_date)
        # generate a index
        data.reset_index(inplace=True,drop=True)
        """
        Date,Adj Close,Close,High,Low,Open,Volume
        """
        new_data = data
        
        # write it out in the og format
        data.to_csv(f'data/{tag[0]}.csv')

        # so that it can be read in 
        with open(f'data/{tag[0]}.csv', 'r') as in_file:
            lines = in_file.readlines()
        
        # and manipulated before being exported
        with open(f'data/{tag[0]}.csv', 'w+') as out_file:
            del lines[1]
            lines[0] = lines[0].replace('Attributes', 'Date')
            for i in lines:
                out_file.write(i)
        
        # and loaded in as a dataframe and exported out as the function
        return pd.read_csv(f'data/{tag[0]}.csv')

    except :
        # if the data is wrong, return a blank one
        return pd.DataFrame()


import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.pylab import rcParams
rcParams['figure.figsize']=8,8
from keras.models import Sequential
from keras.layers import LSTM,Dropout,Dense
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from platform import system as operating_system

import torch #pytorch
import torch.nn as nn
from torch.autograd import Variable
from flask import url_for

class LSTM1(nn.Module):
    def __init__(self, num_classes, input_size, hidden_size, num_layers, seq_length):
        super(LSTM1, self).__init__()
        self.num_classes = num_classes #number of classes
        self.num_layers = num_layers #number of layers
        self.input_size = input_size #input size
        self.hidden_size = hidden_size #hidden state
        self.seq_length = seq_length #sequence length

        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size,
                          num_layers=num_layers, batch_first=True) #lstm
        self.fc_1 =  nn.Linear(hidden_size, 128) #fully connected 1
        self.fc = nn.Linear(128, num_classes) #fully connected last layer

        self.relu = nn.ReLU()
    
    def forward(self,x):
        h_0 = Variable(torch.zeros(self.num_layers, x.size(0), self.hidden_size)) #hidden state
        c_0 = Variable(torch.zeros(self.num_layers, x.size(0), self.hidden_size)) #internal state
        # Propagate input through LSTM
        output, (hn, cn) = self.lstm(x, (h_0, c_0)) #lstm with input, hidden, and internal state
        hn = hn.view(-1, self.hidden_size) #reshaping the data for Dense layer next
        out = self.relu(hn)
        out = self.fc_1(out) #first Dense
        out = self.relu(out) #relu
        out = self.fc(out) #Final Output
        return out
 
def get_predictive_model(tag:str, start_date = pd.to_datetime('2020-01-01'), end_date = dt.datetime.today(), locs =[-2, [2,6]]):
    # pull in data from 
    df = get_stock_data(tag, start_date, end_date)


    # generate the index
    df.index = df["Date"]

    # parse through for the trimmed dataset   
    plt.style.use('ggplot')
    X = df.iloc[:, :locs[0]]
    y = df.iloc[:, locs[1]]

    mm = MinMaxScaler()
    ss = StandardScaler()

    X_ss = ss.fit_transform(X)
    y_mm = mm.fit_transform(y)

    size = int(len(X_ss) * .2) # replaces 200

    X_train = X_ss[:size, :]
    X_test = X_ss[size:, :]

    y_train = y_mm[:size, :]
    y_test = y_mm[size:, :]

    X_train_tensors = Variable(torch.Tensor(X_train))
    X_test_tensors = Variable(torch.Tensor(X_test))

    y_train_tensors = Variable(torch.Tensor(y_train))
    y_test_tensors = Variable(torch.Tensor(y_test))

    X_train_tensors_final = torch.reshape(X_train_tensors,   (X_train_tensors.shape[0], 1, X_train_tensors.shape[1]))
    X_test_tensors_final = torch.reshape(X_test_tensors,  (X_test_tensors.shape[0], 1, X_test_tensors.shape[1])) 

    num_epochs = 1000 #1000 epochs
    learning_rate = 0.001 #0.001 lr

    input_size = 5 #number of features
    hidden_size = 2 #number of features in hidden state
    num_layers = 1 #number of stacked lstm layers

    num_classes = 1 #number of output classes 

    lstm1 = LSTM1(num_classes, input_size, hidden_size, num_layers, X_train_tensors_final.shape[1]) #our lstm class 

    criterion = torch.nn.MSELoss()    # mean-squared error for regression
    optimizer = torch.optim.Adam(lstm1.parameters(), lr=learning_rate)    

    for epoch in range(num_epochs):
        outputs = lstm1.forward(X_train_tensors_final) #forward pass
        optimizer.zero_grad() #caluclate the gradient, manually setting to 0
        
        # obtain the loss function
        loss = criterion(outputs, y_train_tensors)
        
        loss.backward() #calculates the loss of the loss function
        
        optimizer.step() #improve from loss, i.e backprop
        if epoch % 100 == 0:
            print("Epoch: %d, loss: %1.5f" % (epoch, loss.item())) 

    df_X_ss = ss.transform(df.iloc[:, :-2]) #old transformers
    df_y_mm = mm.transform(df.iloc[:, -2:]) #old transformers

    df_X_ss = Variable(torch.Tensor(df_X_ss)) #converting to Tensors
    df_y_mm = Variable(torch.Tensor(df_y_mm))
    #reshaping the dataset
    df_X_ss = torch.reshape(df_X_ss, (df_X_ss.shape[0], 1, df_X_ss.shape[1])) 

    train_predict = lstm1(df_X_ss)#forward pass
    data_predict = train_predict.data.numpy() #numpy conversion
    dataY_plot = df_y_mm.data.numpy()

    try:
        data_predict = mm.inverse_transform(data_predict) #reverse transformation   
    except:
        None
    
    dataY_plot = mm.inverse_transform(dataY_plot)
    plt.figure(figsize=(10,6)) #plotting
    plt.axvline(x=200, c='r', linestyle='--') #size of the training set

    plt.plot(dataY_plot, label='Actual Data') #actual plot
    plt.plot(data_predict, label='Predicted Data') #predicted plot
    plt.title('Time-Series Prediction')
    plt.legend()
    

    save_loc = f'..\\img\\{tag}' if operating_system() == 'Windows' else f'../img/{tag}'

    try:
        plt.savefig(save_loc)
        plt.savefig(f'static\\{tag}' if operating_system() == 'Windows' else f'static/{tag}')
    except :
        save_loc = f'img\\{tag}' if operating_system() == 'Windows' else f'img/{tag}'
        plt.savefig(save_loc)
        plt.savefig(f'src\\static\\{tag}' if operating_system() == 'Windows' else f'src/static/{tag}')
    
    try:
        return url_for("static", filename=f'{tag}.png')
    except:
        return save_loc
if __name__ == '__main__':
    for i in range(0,6):
        print(
            get_predictive_model('VHC', pd.to_datetime('2018-01-01'), locs=[-2, [i,i]])
        )
        plt.savefig(f'{i}.png')
        for j in range(0,6):
            print(
                get_predictive_model('VHC', pd.to_datetime('2018-01-01'), locs=[-2, [i, j]])
            )
            plt.savefig(f'{i}|{j}.png')
    