from sqlalchemy.orm import aliased

from models import Candle 
from models import Order 
from base import Session
session = Session()

C0_VARIABLES = ["c0_Open", "c0_High", "c0_Low", "c0_Close", "c0_Volume", "c0_Quote_Asset_Volume", "c0_Number_Of_Trades", "c0_Taker_Buy_Base_Asset_Volume", "c0_Taker_Buy_Quote_Asset_Volume" ]
C1_VARIABLES = ["c1_Open", "c1_High", "c1_Low", "c1_Close", "c1_Volume", "c1_Quote_Asset_Volume", "c1_Number_Of_Trades", "c1_Taker_Buy_Base_Asset_Volume", "c1_Taker_Buy_Quote_Asset_Volume" ]
C2_VARIABLES = ["c2_Open", "c2_High", "c2_Low", "c2_Close", "c2_Volume", "c2_Quote_Asset_Volume", "c2_Number_Of_Trades", "c2_Taker_Buy_Base_Asset_Volume", "c2_Taker_Buy_Quote_Asset_Volume" ]
C3_VARIABLES = ["c3_Open", "c3_High", "c3_Low", "c3_Close", "c3_Volume", "c3_Quote_Asset_Volume", "c3_Number_Of_Trades", "c3_Taker_Buy_Base_Asset_Volume", "c3_Taker_Buy_Quote_Asset_Volume" ]
C4_VARIABLES = ["c4_Open", "c4_High", "c4_Low", "c4_Close", "c4_Volume", "c4_Quote_Asset_Volume", "c4_Number_Of_Trades", "c4_Taker_Buy_Base_Asset_Volume", "c4_Taker_Buy_Quote_Asset_Volume" ]

X_VARIABLES = C0_VARIABLES + C1_VARIABLES + C2_VARIABLES + C3_VARIABLES + C4_VARIABLES

def getData():
  #data = session.query(Order).filter(Order.candle0.isnot(None)).all()
  c0 = aliased(Candle)
  c1 = aliased(Candle)
  c2 = aliased(Candle)
  c3 = aliased(Candle)
  c4 = aliased(Candle)

  data = session.query(Order, c0, c1, c2, c3, c4).join(
    c0, c0.id == Order.candle0).join(
    c1, c1.id == Order.candle1).join(
    c2, c2.id == Order.candle2).join(
    c3, c3.id == Order.candle3).join(
    c4, c4.id == Order.candle4).filter(
    Order.candle0.isnot(None)).all()

  return data

def arrangeData(tupleList):
  dictList = []
  for item in tupleList:
    (order, c0, c1, c2, c3, c4) = item
    new_dict = {}
    new_dict["c0_Open"] = c0.Open
    new_dict["c0_High"] = c0.High
    new_dict["c0_Low"] = c0.Low
    new_dict["c0_Close"] = c0.Close
    new_dict["c0_Volume"] = c0.Volume
    new_dict["c0_Quote_Asset_Volume"] = c0.Quote_Asset_Volume
    new_dict["c0_Number_Of_Trades"] = c0.Number_Of_Trades
    new_dict["c0_Taker_Buy_Base_Asset_Volume"] = c0.Taker_Buy_Base_Asset_Volume
    new_dict["c0_Taker_Buy_Quote_Asset_Volume"] = c0.Taker_Buy_Quote_Asset_Volume

    new_dict["c1_Open"] = c1.Open
    new_dict["c1_High"] = c1.High
    new_dict["c1_Low"] = c1.Low
    new_dict["c1_Close"] = c1.Close
    new_dict["c1_Volume"] = c1.Volume
    new_dict["c1_Quote_Asset_Volume"] = c1.Quote_Asset_Volume
    new_dict["c1_Number_Of_Trades"] = c1.Number_Of_Trades
    new_dict["c1_Taker_Buy_Base_Asset_Volume"] = c1.Taker_Buy_Base_Asset_Volume
    new_dict["c1_Taker_Buy_Quote_Asset_Volume"] = c1.Taker_Buy_Quote_Asset_Volume

    new_dict["c2_Open"] = c2.Open
    new_dict["c2_High"] = c2.High
    new_dict["c2_Low"] = c2.Low
    new_dict["c2_Close"] = c2.Close
    new_dict["c2_Volume"] = c2.Volume
    new_dict["c2_Quote_Asset_Volume"] = c2.Quote_Asset_Volume
    new_dict["c2_Number_Of_Trades"] = c2.Number_Of_Trades
    new_dict["c2_Taker_Buy_Base_Asset_Volume"] = c2.Taker_Buy_Base_Asset_Volume
    new_dict["c2_Taker_Buy_Quote_Asset_Volume"] = c2.Taker_Buy_Quote_Asset_Volume 

    new_dict["c3_Open"] = c3.Open
    new_dict["c3_High"] = c3.High
    new_dict["c3_Low"] = c3.Low
    new_dict["c3_Close"] = c3.Close
    new_dict["c3_Volume"] = c3.Volume
    new_dict["c3_Quote_Asset_Volume"] = c3.Quote_Asset_Volume
    new_dict["c3_Number_Of_Trades"] = c3.Number_Of_Trades
    new_dict["c3_Taker_Buy_Base_Asset_Volume"] = c3.Taker_Buy_Base_Asset_Volume
    new_dict["c3_Taker_Buy_Quote_Asset_Volume"] = c3.Taker_Buy_Quote_Asset_Volume   

    new_dict["c4_Open"] = c4.Open
    new_dict["c4_High"] = c4.High
    new_dict["c4_Low"] = c4.Low
    new_dict["c4_Close"] = c4.Close
    new_dict["c4_Volume"] = c4.Volume
    new_dict["c4_Quote_Asset_Volume"] = c4.Quote_Asset_Volume
    new_dict["c4_Number_Of_Trades"] = c4.Number_Of_Trades
    new_dict["c4_Taker_Buy_Base_Asset_Volume"] = c4.Taker_Buy_Base_Asset_Volume
    new_dict["c4_Taker_Buy_Quote_Asset_Volume"] = c4.Taker_Buy_Quote_Asset_Volume 

    marker_sell_price = order.marker_sell_price
    price = order.price
    profit = (marker_sell_price - price)/price
    new_dict["profit"] = profit
    profit_flag = 1 if profit > 0 else 0
    new_dict["profit_flag"] = profit_flag

    dictList.append(new_dict)
  return dictList

def initML():
  data = getData()

  data = arrangeData(data)