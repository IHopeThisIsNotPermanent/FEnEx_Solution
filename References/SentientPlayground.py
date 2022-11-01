import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime, pytz, time, math, pickle

from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.decomposition import PCA

#Usual sentient stuff here

x_train = pd.read_pickle("x_train")
y_train = pd.read_pickle("y_train")

TEST1 = False

if TEST1:

    pca_test = PCA()
    
    pca_test.fit(x_train)
    dat = pca_test.explained_variance_ratio_
    plt.bar(x = list(range(len(dat))), height = dat)
    
    plt.title("x_train")
    plt.show()
    plt.figure()
    
    pca_test.fit(y_train)
    dat = pca_test.explained_variance_ratio_
    plt.bar(x = list(range(len(dat))), height = dat)
    
    plt.title("y_train")
    plt.show()
    plt.figure()


TEST2 = False

if TEST2:
    for x in range(16):
        for y in range(4):
            model = LinearRegression()
            plt.scatter(x_train[x_train.columns[x]], y_train[y_train.columns[y]])
            model.fit(np.array(x_train[x_train.columns[x]]).reshape(-1, 1), np.array(y_train[y_train.columns[y]]).reshape(-1, 1))
            x_points = [min(x_train[x_train.columns[x]]), max(x_train[x_train.columns[x]])]
            plt.plot(x_points,model.predict([[x_points[0],],[x_points[1],]]).reshape([1,-1])[0], color = "black")
            plt.title("x="+str(x)+"y="+str(y))
            plt.show()
            plt.figure()


#test with 1 layer
model_error = []
for layer_size in (4,16): #,32,64,128,256,512):
    print("layer_size=" + str(layer_size))
    model = MLPRegressor(hidden_layer_sizes=(layer_size,), max_iter = 600)
    cv =  KFold(6, shuffle=True)
    model_error.append(cross_val_score(model, x_train, y_train, cv = cv, scoring='r2'))
    print(model_error[len(model_error)-1].mean())


results_rev = []
for i in range(len(model_error[0])):
    results_rev.append([item[i] for item in model_error])
    
df = pd.DataFrame(results_rev, columns=[str(x) for x in (4,16,32,64,128,256,512)])
fig = plt.box(df)
fig.show()