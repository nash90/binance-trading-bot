from datetime import datetime
from sqlalchemy.orm import aliased
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import GridSearchCV
import tensorflow as tf
from tensorflow import keras
#from keras.layers.advanced_activations import LeakyReLU
from keras.models import Sequential
from keras.layers import Dense


from sklearn.tree import DecisionTreeClassifier # Import Decision Tree Classifier
from sklearn.model_selection import train_test_split # Import train_test_split function
from sklearn import metrics #Import scikit-learn metrics module for accuracy calculation

from models.models import Candle 
from models.models import Order 
from models.base import Session
from util.utility import createNumericCandleDict
from util.utility import createCategoricCandleList
from util.encoder import MultiColumnLabelEncoder
import joblib
from configs.ml_config import ml_config
from util.utility import saveObject
from util.utility import loadObject



from ml_common import getNumericData
from ml_common import arrangeNumericData
from ml_common import dataProcessingForNumericClassifier
from ml_common import dataProcessingForNumericClassifier2

from ml_common import getCategoricData
from ml_common import arrangeCategoricalData
from ml_common import dataProcessingForCategoricClassifier

C0_NUM_VARIABLES = ["c0_Open", "c0_High", "c0_Low", "c0_Close", "c0_Volume", "c0_Quote_Asset_Volume", "c0_Number_Of_Trades", "c0_Taker_Buy_Base_Asset_Volume", "c0_Taker_Buy_Quote_Asset_Volume" ]
C1_NUM_VARIABLES = ["c1_Open", "c1_High", "c1_Low", "c1_Close", "c1_Volume", "c1_Quote_Asset_Volume", "c1_Number_Of_Trades", "c1_Taker_Buy_Base_Asset_Volume", "c1_Taker_Buy_Quote_Asset_Volume" ]
C2_NUM_VARIABLES = ["c2_Open", "c2_High", "c2_Low", "c2_Close", "c2_Volume", "c2_Quote_Asset_Volume", "c2_Number_Of_Trades", "c2_Taker_Buy_Base_Asset_Volume", "c2_Taker_Buy_Quote_Asset_Volume" ]
C3_NUM_VARIABLES = ["c3_Open", "c3_High", "c3_Low", "c3_Close", "c3_Volume", "c3_Quote_Asset_Volume", "c3_Number_Of_Trades", "c3_Taker_Buy_Base_Asset_Volume", "c3_Taker_Buy_Quote_Asset_Volume" ]
C4_NUM_VARIABLES = ["c4_Open", "c4_High", "c4_Low", "c4_Close", "c4_Volume", "c4_Quote_Asset_Volume", "c4_Number_Of_Trades", "c4_Taker_Buy_Base_Asset_Volume", "c4_Taker_Buy_Quote_Asset_Volume" ]

X_NUM_VARIABLES = C0_NUM_VARIABLES + C1_NUM_VARIABLES + C2_NUM_VARIABLES + C3_NUM_VARIABLES + C4_NUM_VARIABLES
X_CAT_VARIABLES = ["candle_pattern0", "candle_pattern1", "candle_pattern2", "candle_pattern3", "candle_pattern4"]
Y_VARIABLE = ["profit_flag"]
DATA_PARTITION = 0.25

MAX_ITER = 10000000
HIDDEN_LAYER = (100, 100, 100)
MODEL_FILE = 'mlp_model.txt'
SCALE_FILE = 'mlp_scale.txt'

PARAM_MLP = {
    'hidden_layer_sizes': [(50,50,50), (50,100,50), (100,)],
    'activation': ['tanh', 'relu'],
    'solver': ['sgd', 'adam'],
    'alpha': [0.0001, 0.05],
    'learning_rate': ['constant','adaptive'],
}


def getEqualSample(df):
  nrows = len(df)
  total_sample_size = 1e4
  #df.groupby('profit_flag').\
  #    apply(lambda x: x.sample(int((x.count()/nrows)*total_sample_size)))
  #df.sample(n = 2000, weights = (df['profit_flag'].value_counts()/len(df['profit_flag']))**-1)

  df_true = df[df['profit_flag'] == 1]
  df_false = df[df['profit_flag'] == 0]
  df_true = df_true.sample(1000)
  df_false = df_false.sample(1000)
  df = df_true.append(df_false)
  df=df.sample(2000)
  len(df)
  
  return df

def mlpClassifier(X_train, y_train):
  
  mlp = MLPClassifier(hidden_layer_sizes=HIDDEN_LAYER, max_iter=MAX_ITER)
  #mlp = MLPClassifier(hidden_layer_sizes=HIDDEN_LAYER, max_iter=MAX_ITER, alpha=1e-7,
  #                    solver='sgd', verbose=0, tol=1e-8, random_state=1,
  #                    learning_rate_init=0.01, learning_rate='adaptive')
  mlp.fit(X_train, y_train.values.ravel())

  return mlp

def mlpClassifier2(X_train, y_train):
  mlp =MLPClassifier(activation='relu', alpha=0.0001, batch_size='auto', beta_1=0.9,
       beta_2=0.999, early_stopping=False, epsilon=1e-08,
       hidden_layer_sizes=(100,), learning_rate='constant',
       learning_rate_init=0.001, max_iter=10000, momentum=0.9,
       n_iter_no_change=10, nesterovs_momentum=True, power_t=0.5,
       random_state=None, shuffle=True, solver='adam', tol=0.0001,
       validation_fraction=0.1, verbose=False, warm_start=False)
  mlp.fit(X_train, y_train.values.ravel())
  return mlp

def bestMLPClassifier(X_train, y_train):
  mlp = MLPClassifier(max_iter=MAX_ITER)
  clf = GridSearchCV(mlp, PARAM_MLP)
  clf.fit(X_train, y_train.values.ravel())
  return clf


def initNumericML(findBest = False):
  db_data = getNumericData()

  formatted_data = arrangeNumericData(db_data)

  ml_data = pd.DataFrame(formatted_data)
  ml_data = getEqualSample(ml_data)

  [X_train, X_test, y_train, y_test] = dataProcessingForNumericClassifier(ml_data)

  if findBest == True:
    print("ML_LOG: Find best MLP")
    model = bestMLPClassifier(X_train, y_train)
  else:
    model = mlpClassifier2(X_train, y_train)

  predictions = model.predict(X_test)

  print(confusion_matrix(y_test,predictions))
  print(classification_report(y_test,predictions))

  saveObject(model, MODEL_FILE)

  return model


def initCategoricML(findBest = False):
  db_data = getCategoricData()

  formatted_data = arrangeCategoricalData(db_data)

  ml_data = pd.DataFrame(formatted_data)
  ml_data = getEqualSample(ml_data)

  [X_train, X_test, y_train, y_test] = dataProcessingForCategoricClassifier(ml_data)

  if findBest == True:
    print("ML_LOG: Find best MLP")
    model = bestMLPClassifier(X_train, y_train)
  else:
    model = mlpClassifier2(X_train, y_train)

  predictions = model.predict(X_test)

  print(confusion_matrix(y_test,predictions))
  print(classification_report(y_test,predictions))
  return model


def plotEpocs(clf):
  import matplotlib.pyplot as plt
  plt.title("Loss Curve")
  plt.plot(clf.loss_curve_)
  plt.xlabel("Iteration")
  plt.ylabel("Loss")
  plt.grid()
  plt.show()

def initTensor():
  db_data = getNumericData()

  formatted_data = arrangeNumericData(db_data)

  ml_data = pd.DataFrame(formatted_data)

  [X_train, X_test, y_train, y_test] = dataProcessingForNumericClassifier(ml_data)

  model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(10)
  ])
  loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
  model.compile(optimizer='adam',
              loss=loss_fn,
              metrics=["accuracy"])

  model.fit(X_train, y_train, epochs=500, class_weight={0:0.8, 1:1})

  model.evaluate(X_test,  y_test, verbose=2)
  predictions =  np.argmax(model.predict(X_test), axis=-1)
  print(confusion_matrix(y_test,predictions))
  print(classification_report(y_test,predictions))

  return model


def initCatTensor():
  db_data = getCategoricData()

  formatted_data = arrangeCategoricalData(db_data)

  ml_data = pd.DataFrame(formatted_data)

  [X_train, X_test, y_train, y_test] = dataProcessingForCategoricClassifier(ml_data)

  model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(10)
  ])
  loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
  model.compile(optimizer='adam',
              loss=loss_fn,
              metrics=["accuracy"])

  model.fit(X_train, y_train, epochs=55 , class_weight={0:0.5, 1:1})

  model.evaluate(X_test,  y_test, verbose=2)

  return model

def initTensor1():
  db_data = getNumericData()

  formatted_data = arrangeNumericData(db_data)

  ml_data = pd.DataFrame(formatted_data)

  [X_train, X_test, y_train, y_test] = dataProcessingForNumericClassifier(ml_data)
  #counts = np.bincount(y_train[:, 0])
  weight_for_0 = 1.0 / y_train[["profit_flag"]].value_counts()[0]
  weight_for_1 = 1.0 / y_train[["profit_flag"]].value_counts()[1] 

  model = keras.Sequential(
    [
        keras.layers.Dense(
            10, activation="relu", input_shape=(X_train.shape[-1],)
        ),
        keras.layers.Dense(10, activation="relu"),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(10, activation="relu"),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(1, activation="sigmoid"),
    ]
  )

  metrics = [
    keras.metrics.FalseNegatives(name="fn"),
    keras.metrics.FalsePositives(name="fp"),
    keras.metrics.TrueNegatives(name="tn"),
    keras.metrics.TruePositives(name="tp"),
    keras.metrics.Precision(name="precision"),
    keras.metrics.Recall(name="recall"),
  ]

  loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True) #"binary_crossentropy"
  model.compile(
    optimizer=keras.optimizers.Adam(1e-2), loss="binary_crossentropy", metrics='binary_accuracy'
  )

  class_weight = {0:weight_for_0, 1:weight_for_1}
  model.fit(
    X_train,
    y_train,
    #batch_size=2048,
    epochs=30,
    verbose=2,
    #callbacks=callbacks,
    validation_data=(X_test, y_test),
    class_weight=class_weight,
  )

  model.evaluate(X_test,  y_test, verbose=2)
  predictions =  np.argmax(model.predict(X_test), axis=-1)
  print(confusion_matrix(y_test,predictions))
  print(classification_report(y_test,predictions))

  return model



def initTensor2():
  db_data = getNumericData()

  formatted_data = arrangeNumericData(db_data)

  ml_data = pd.DataFrame(formatted_data)
  ml_data.to_csv('trade_data.csv', index=False)
  ml_data = getEqualSample(ml_data)

  [X_train, X_test, y_train, y_test] = dataProcessingForNumericClassifier2(ml_data)
  #counts = np.bincount(y_train[:, 0])
  weight_for_0 = 1.0 / y_train[["profit_flag"]].value_counts()[0]
  weight_for_1 = 1.0 / y_train[["profit_flag"]].value_counts()[1] 

  model = Sequential()

  model.add(Dense(5, activation='relu', input_shape=(X_train.shape[-1],)))

  model.add(Dense(5, activation='relu'))

  model.add(Dense(1, activation='sigmoid'))

  metrics = [
    keras.metrics.FalseNegatives(name="fn"),
    keras.metrics.FalsePositives(name="fp"),
    keras.metrics.TrueNegatives(name="tn"),
    keras.metrics.TruePositives(name="tp"),
    keras.metrics.Precision(name="precision"),
    keras.metrics.Recall(name="recall"),
  ]

  loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False) #"binary_crossentropy"
  loss=tf.keras.losses.BinaryCrossentropy(from_logits=False)
  sgd = keras.optimizers.SGD(lr=0.01, clipvalue=0.5)
  model.compile(
    optimizer=sgd,
    metrics=['accuracy'],
    loss=loss
  )

  class_weight = {0:weight_for_0, 1:weight_for_1}
  model.fit(
    X_train,
    y_train,
    #batch_size=2048,
    epochs=30,
    verbose=1,
    #callbacks=callbacks,
    #validation_data=(X_test, y_test),
    #validation_steps=5,
    class_weight=class_weight,
  )

  model.evaluate(X_test,  y_test, verbose=2)
  predictions =  np.argmax(model.predict(X_test), axis=-1)
  print(confusion_matrix(y_test,predictions))
  print(classification_report(y_test,predictions))

  return model

def tensor3():
  from pandas import read_csv
  from keras.models import Sequential
  from keras.layers import Dense
  from keras.wrappers.scikit_learn import KerasClassifier
  from sklearn.model_selection import cross_val_score
  from sklearn.preprocessing import LabelEncoder
  from sklearn.model_selection import StratifiedKFold
  from sklearn.preprocessing import StandardScaler
  from sklearn.pipeline import Pipeline
  db_data = getNumericData()

  formatted_data = arrangeNumericData(db_data)

  ml_data = pd.DataFrame(formatted_data)

  [X_train, X_test, y_train, y_test] = dataProcessingForNumericClassifier(ml_data)

  # encode class values as integers
  X = X_train
  Y = y_train
  encoder = LabelEncoder()
  encoder.fit(y_train)
  encoded_Y = encoder.transform(Y)
  
  # larger model
  def create_larger():
    # create model
    model = Sequential()
    model.add(Dense(20, input_dim=45, activation='relu'))
    model.add(Dense(20, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    # Compile model
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    return model
  estimators = []
  estimators.append(('standardize', StandardScaler()))
  estimators.append(('mlp', KerasClassifier(build_fn=create_larger, epochs=30, batch_size=5, verbose=0)))
  pipeline = Pipeline(estimators)
  kfold = StratifiedKFold(n_splits=10, shuffle=True)
  results = cross_val_score(pipeline, X, encoded_Y, cv=kfold)
  print("Larger: %.2f%% (%.2f%%)" % (results.mean()*100, results.std()*100))