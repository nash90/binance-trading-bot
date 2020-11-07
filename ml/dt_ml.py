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
import matplotlib.pyplot as plt


from sklearn.tree import DecisionTreeClassifier # Import Decision Tree Classifier
from sklearn.model_selection import train_test_split # Import train_test_split function
from sklearn import metrics #Import scikit-learn metrics module for accuracy calculation


### visualizing DT
from sklearn import tree
from sklearn.tree import export_graphviz
from six import StringIO 
#from IPython.display import Image  
import pydotplus

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

from ml_common import getCategoricData
from ml_common import arrangeCategoricalData
from ml_common import dataProcessingForCategoricClassifier
from ml_common import dataProcessingForDT


def DT(X_train, y_train):
  # Create Decision Tree classifer object
  clf = DecisionTreeClassifier(criterion="entropy", max_depth=4)
  # Train Decision Tree Classifer
  clf = clf.fit(X_train,y_train)
  return clf


def initOrdinalCategoricDT():
  db_data = getCategoricData()

  formatted_data = arrangeCategoricalData(db_data)

  ml_data = pd.DataFrame(formatted_data)

  [X_train, X_test, y_train, y_test] = dataProcessingForCategoricClassifier(ml_data)

  model = DT(X_train, y_train)

  predictions = model.predict(X_test)

  print(confusion_matrix(y_test,predictions))
  print(classification_report(y_test,predictions))
  return model


def initNonOrdinalCategoricDT():
  db_data = getCategoricData()

  formatted_data = arrangeCategoricalData(db_data)

  ml_data = pd.DataFrame(formatted_data)

  [X_train, X_test, y_train, y_test] = dataProcessingForDT(ml_data)

  clf = DT(X_train, y_train)

    #Predict the response for test dataset
  predictions = clf.predict(X_test)

  print(confusion_matrix(y_test,predictions))
  print(classification_report(y_test,predictions))

  print("Accuracy:",metrics.accuracy_score(y_test, predictions))
  return clf

def drawTree(clf, fn=None, cn = None):
  fig, axes = plt.subplots(nrows = 1,ncols = 1,figsize = (4,4), dpi=300)
  tree.plot_tree(clf, feature_names = fn, class_names = cn, filled = True);
  fig.savefig('tree.png')


def drawGraph(clf):
  dot_data = StringIO()
  export_graphviz(clf, out_file=dot_data,  
                  filled=True, rounded=True,
                  special_characters=True,class_names=['0','1'])
  graph = pydotplus.graph_from_dot_data(dot_data.getvalue())  
  graph.write_png('tree.png')
  #Image(graph.create_png())