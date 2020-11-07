from datetime import datetime
from sqlalchemy.orm import aliased
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn import preprocessing
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import GridSearchCV


from sklearn.tree import DecisionTreeClassifier # Import Decision Tree Classifier
from sklearn.model_selection import train_test_split # Import train_test_split function
from sklearn import metrics #Import scikit-learn metrics module for accuracy calculation

from models import Candle 
from models import Order 
from base import Session
from utility import createNumericCandleDict
from utility import createCategoricCandleList
from encoder import MultiColumnLabelEncoder
import joblib
from configs.ml_config import ml_config
from utility import saveObject
from utility import loadObject



from ml_common import getNumericData
from ml_common import arrangeNumericData
from ml_common import dataProcessingForNumericClassifier

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
HIDDEN_LAYER = (50, 50, 50)
MODEL_FILE = 'mlp_model.txt'
SCALE_FILE = 'mlp_scale.txt'

PARAM_MLP = {
    'hidden_layer_sizes': [(50,50,50), (50,100,50), (100,)],
    'activation': ['tanh', 'relu'],
    'solver': ['sgd', 'adam'],
    'alpha': [0.0001, 0.05],
    'learning_rate': ['constant','adaptive'],
}



def mlpClassifier(X_train, y_train):
  
  mlp = MLPClassifier(hidden_layer_sizes=HIDDEN_LAYER, max_iter=MAX_ITER)
  #mlp = MLPClassifier(hidden_layer_sizes=(20,20,), max_iter=100000, alpha=1e-4,
  #                    solver='adam', verbose=0, tol=1e-8, random_state=1,
  #                    learning_rate_init=.01)
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

  [X_train, X_test, y_train, y_test] = dataProcessingForNumericClassifier(ml_data)

  if findBest == True:
    print("ML_LOG: Find best MLP")
    model = bestMLPClassifier(X_train, y_train)
  else:
    model = mlpClassifier(X_train, y_train)

  predictions = model.predict(X_test)

  print(confusion_matrix(y_test,predictions))
  print(classification_report(y_test,predictions))

  saveObject(model, MODEL_FILE)

  return model


def initCategoricML():
  db_data = getCategoricData()

  formatted_data = arrangeCategoricalData(db_data)

  ml_data = pd.DataFrame(formatted_data)

  [X_train, X_test, y_train, y_test] = dataProcessingForCategoricClassifier(ml_data)


  model = mlpClassifier(X_train, y_train)

  predictions = model.predict(X_test)

  print(confusion_matrix(y_test,predictions))
  print(classification_report(y_test,predictions))
  return model

