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

def getNumericData():
  #data = session.query(Order).filter(Order.candle0.isnot(None)).all()
  c0 = aliased(Candle)
  c1 = aliased(Candle)
  c2 = aliased(Candle)
  c3 = aliased(Candle)
  c4 = aliased(Candle)

  #filter_case = Order.candle0.isnot(None)
  session = Session()

  data = session.query(Order, c0, c1, c2, c3, c4).join(
    c0, c0.id == Order.candle0).join(
    c1, c1.id == Order.candle1).join(
    c2, c2.id == Order.candle2).join(
    c3, c3.id == Order.candle3).join(
    c4, c4.id == Order.candle4).filter(
      #Order.candle0.isnot(None)
      Order.created_date >= datetime(2020, 10, 1)
    ).filter(
      Order.sold_cummulative_quote_qty.isnot(None)
    ).all()
  print(len(data))
  session.close()
  return data


def arrangeNumericData(tupleList):
  dictList = []
  for item in tupleList:
    (order, c0, c1, c2, c3, c4) = item
    new_dict = createNumericCandleDict(order, c0, c1, c2, c3, c4)
    dictList.append(new_dict)

  return dictList



def getCategoricData():
  #data = session.query(Order).filter(Order.candle_pattern0.isnot(None)).all()
  session = Session()
  data = session.query(Order).filter(
     Order.created_date >= datetime(2020, 10, 1)
  ).filter(
    Order.sold_cummulative_quote_qty.isnot(None)
  ).all()
  session.close()
  return data



def arrangeCategoricalData(itemList):
  dictList = []
  for item in itemList:
    new_dict = createCategoricCandleList(item)
    dictList.append(new_dict)
  
  return dictList



def getTestData():
  db_data = getNumericData()

  formatted_data = arrangeNumericData(db_data)

  ml_data = pd.DataFrame(formatted_data)

  [X_train, X_test, y_train, y_test] = dataProcessingForNumericClassifier(ml_data)

  return [X_train, X_test, y_train, y_test]


def dataProcessingForNumericClassifier(ml_data):
  X = ml_data[X_NUM_VARIABLES]
  y = ml_data[Y_VARIABLE]

  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = DATA_PARTITION)
  
  scaler = StandardScaler()
  scaler.fit(X_train)

  saveObject(scaler, SCALE_FILE)

  X_train = scaler.transform(X_train)
  X_test = scaler.transform(X_test)

  return [X_train, X_test, y_train, y_test]


def dataProcessingForCategoricClassifier(ml_data):
  X = ml_data[X_CAT_VARIABLES]
  y = ml_data[Y_VARIABLE]

  X = MultiColumnLabelEncoder(columns = ['candle_pattern0','candle_pattern1', 'candle_pattern2', 'candle_pattern3', 'candle_pattern4']).fit_transform(X)
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = DATA_PARTITION)
  
 
  #X_test = MultiColumnLabelEncoder(columns = ['candle_pattern0','candle_pattern1', 'candle_pattern2', 'candle_pattern3', 'candle_pattern4']).fit_transform(X_test)
  #le.transform(X_test)
  #scaler = StandardScaler()
  #scaler.fit(X_train)

  #X_train = scaler.transform(X_train)
  #X_test = scaler.transform(X_test)

  return [X_train, X_test, y_train, y_test]


def dataProcessingForDT(ml_data):
  X = ml_data[X_CAT_VARIABLES]
  y = ml_data[Y_VARIABLE]

  data = ml_data.values
  X = data[:, :-1].astype(str)
  y = data[:, -1].astype(str)

  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=1)

  # one-hot encode input variables
  onehot_encoder = OneHotEncoder()
  onehot_encoder.fit(X)
  X_train = onehot_encoder.transform(X_train)
  #onehot_encoder.fit(X_test)
  X_test = onehot_encoder.transform(X_test)
  # ordinal encode target variable
  label_encoder = LabelEncoder()
  label_encoder.fit(y_train)
  y_train = label_encoder.transform(y_train)
  y_test = label_encoder.transform(y_test)

  return [X_train, X_test, y_train, y_test]

