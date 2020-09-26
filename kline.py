import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
import pytz
import time

from binance.client import Client
from binance.enums import *
from datetime import datetime

from base import Session
from config import config
from models import Candle
from dbutility import addDataToDB

session = Session()

api_key = config["api_key"]
api_secret = config["api_secret"]
client = Client(api_key, api_secret)
symbol = config.get("crypto_list")[0]["exchange"] 
#candle_names = talib.get_function_groups()['Pattern Recognition']


KLINE_INTERVAL_5MINUTE = Client.KLINE_INTERVAL_15MINUTE
KLINE_INTERVAL_15MINUTE = Client.KLINE_INTERVAL_15MINUTE
FETCH_LENGTH = "1 day ago JST"
LOG_ELEMENTS = ["Open_time_str", "Open", "Close", "candle_pattern", "candle_score", "candle_cumsum", "signal2"]
INVALID_CANDLE_SLEEP = config.get("bot_permit").get("invalid_candlestick_sleep")

DATETIME_FORMAT = "'%Y-%m-%d %H:%M:%S'"

REJECT_DOJI = config.get("bot_permit").get("reject_candles").get("doji")
REJECT_EVENING_STAR = config.get("bot_permit").get("reject_candles").get("evening_star")
REJECT_MORNING_STAR = config.get("bot_permit").get("reject_candles").get("morning_star")
REJECT_SHOOTING_STAR_BEARISH = config.get("bot_permit").get("reject_candles").get("shooting_Star_bearish")
REJECT_SHOOTING_STAR_BULLISH = config.get("bot_permit").get("reject_candles").get("shooting_Star_bullish")
REJECT_HAMMER = config.get("bot_permit").get("reject_candles").get("hammer")
REJECT_INVERTED_HAMMER = config.get("bot_permit").get("reject_candles").get("inverted_hammer")
REJECT_BEARISH_HARAMI = config.get("bot_permit").get("reject_candles").get("bearish_harami")
REJECT_BULLISH_HARAMI = config.get("bot_permit").get("reject_candles").get("Bullish_Harami")
REJECT_BEARISH_ENGULFING = config.get("bot_permit").get("reject_candles").get("Bearish_Engulfing")
REJECT_BULLISH_ENGULFING = config.get("bot_permit").get("reject_candles").get("Bullish_Engulfing")
REJECT_BULLISH_REVERSAL = config.get("bot_permit").get("reject_candles").get("bullish_reversal")
REJECT_BEARISH_REVERSAL = config.get("bot_permit").get("reject_candles").get("bearish_reversal")
REJECT_PIERCING_LINE_BULLISH = config.get("bot_permit").get("reject_candles").get("Piercing_Line_bullish")
REJECT_HANGING_MAN_BEARISH = config.get("bot_permit").get("reject_candles").get("Hanging_Man_bearish")
REJECT_HANGING_MAN_BULLISH = config.get("bot_permit").get("reject_candles").get("Hanging_Man_bullish")
REJECT_LAST_2_NEGETIVES = config.get("bot_permit").get("reject_candles").get("Last_2_Negetives")
REJECT_UNIDENTIFIED = config.get("bot_permit").get("reject_candles").get("Unidentified")

def getCandleStick(symbol = "BTCUSDT", interval=Client.KLINE_INTERVAL_5MINUTE, length =FETCH_LENGTH):
  #candles = client.get_klines(symbol=symbol, interval=interval)
  candles = client.get_historical_klines(symbol,interval,length)

  return candles

def candle_score(lst_0,lst_1,lst_2, lst3):    
    
    O_0,H_0,L_0,C_0=lst_0[0],lst_0[1],lst_0[2],lst_0[3]
    O_1,H_1,L_1,C_1=lst_1[0],lst_1[1],lst_1[2],lst_1[3]
    O_2,H_2,L_2,C_2=lst_2[0],lst_2[1],lst_2[2],lst_2[3]
    
    DojiSize = 0.1
    
    doji=(abs(O_0 - C_0) <= (H_0 - L_0) * DojiSize)
    
    hammer=(((H_0 - L_0)>3*(O_0 -C_0)) &  ((C_0 - L_0)/(.001 + H_0 - L_0) > 0.6) & ((O_0 - L_0)/(.001 + H_0 - L_0) > 0.6))
    
    inverted_hammer=(((H_0 - L_0)>3*(O_0 -C_0)) &  ((H_0 - C_0)/(.001 + H_0 - L_0) > 0.6) & ((H_0 - O_0)/(.001 + H_0 - L_0) > 0.6))
    
    bullish_reversal= (O_2 > C_2)&(O_1 > C_1)&doji
    
    bearish_reversal= (O_2 < C_2)&(O_1 < C_1)&doji
    
    evening_star=(C_2 > O_2) & (min(O_1, C_1) > C_2) & (O_0 < min(O_1, C_1)) & (C_0 < O_0 )
    
    morning_star=(C_2 < O_2) & (min(O_1, C_1) < C_2) & (O_0 > min(O_1, C_1)) & (C_0 > O_0 )
    
    shooting_Star_bearish=(O_1 < C_1) & (O_0 > C_1) & ((H_0 - max(O_0, C_0)) >= abs(O_0 - C_0) * 3) & ((min(C_0, O_0) - L_0 )<= abs(O_0 - C_0)) & inverted_hammer
    
    shooting_Star_bullish=(O_1 > C_1) & (O_0 < C_1) & ((H_0 - max(O_0, C_0)) >= abs(O_0 - C_0) * 3) & ((min(C_0, O_0) - L_0 )<= abs(O_0 - C_0)) & inverted_hammer
    
    bearish_harami=(C_1 > O_1) & (O_0 > C_0) & (O_0 <= C_1) & (O_1 <= C_0) & ((O_0 - C_0) < (C_1 - O_1 ))
    
    Bullish_Harami=(O_1 > C_1) & (C_0 > O_0) & (C_0 <= O_1) & (C_1 <= O_0) & ((C_0 - O_0) < (O_1 - C_1))
    
    Bearish_Engulfing=((C_1 > O_1) & (O_0 > C_0)) & ((O_0 >= C_1) & (O_1 >= C_0)) & ((O_0 - C_0) > (C_1 - O_1 ))
    
    Bullish_Engulfing=(O_1 > C_1) & (C_0 > O_0) & (C_0 >= O_1) & (C_1 >= O_0) & ((C_0 - O_0) > (O_1 - C_1 ))
    
    Piercing_Line_bullish=(C_1 < O_1) & (C_0 > O_0) & (O_0 < L_1) & (C_0 > C_1)& (C_0>((O_1 + C_1)/2)) & (C_0 < O_1)

    Hanging_Man_bullish=(C_1 < O_1) & (O_0 < L_1) & (C_0>((O_1 + C_1)/2)) & (C_0 < O_1) & hammer

    Hanging_Man_bearish=(C_1 > O_1) & (C_0>((O_1 + C_1)/2)) & (C_0 < O_1) & hammer

    Last_2_Negetives = REJECT_LAST_2_NEGETIVES & (O_1 > C_1) & (O_2 > C_2)

    strCandle=''
    candle_score=0
    
    if doji:
        strCandle='doji'
    if Last_2_Negetives:
        strCandle=strCandle+'/ '+'Last_2_Negetives'    
    if evening_star:
        strCandle=strCandle+'/ '+'evening_star'
        candle_score=candle_score-1
    if morning_star:
        strCandle=strCandle+'/ '+'morning_star'
        candle_score=candle_score+1
    if shooting_Star_bearish:
        strCandle=strCandle+'/ '+'shooting_Star_bearish'
        candle_score=candle_score-1
    if shooting_Star_bullish:
        strCandle=strCandle+'/ '+'shooting_Star_bullish'
        candle_score=candle_score-1
    if    hammer:
        strCandle=strCandle+'/ '+'hammer'
    if    inverted_hammer:
        strCandle=strCandle+'/ '+'inverted_hammer'
    if    bearish_harami:
        strCandle=strCandle+'/ '+'bearish_harami'
        candle_score=candle_score-1
    if    Bullish_Harami:
        strCandle=strCandle+'/ '+'Bullish_Harami'
        candle_score=candle_score+1
    if    Bearish_Engulfing:
        strCandle=strCandle+'/ '+'Bearish_Engulfing'
        candle_score=candle_score-1
    if    Bullish_Engulfing:
        strCandle=strCandle+'/ '+'Bullish_Engulfing'
        candle_score=candle_score+1
    if    bullish_reversal:
        strCandle=strCandle+'/ '+'bullish_reversal'
        candle_score=candle_score+1
    if    bearish_reversal:
        strCandle=strCandle+'/ '+'bearish_reversal'
        candle_score=candle_score-1
    if    Piercing_Line_bullish:
        strCandle=strCandle+'/ '+'Piercing_Line_bullish'
        candle_score=candle_score+1
    if    Hanging_Man_bearish:
        strCandle=strCandle+'/ '+'Hanging_Man_bearish'
        candle_score=candle_score-1
    if    Hanging_Man_bullish:
        strCandle=strCandle+'/ '+'Hanging_Man_bullish'
        candle_score=candle_score+1

        
    #return candle_score
    return candle_score,strCandle

def classifyCandles(df):
    #df_candle=first_letter_upper(df)
    df_candle=df.copy()
    df_candle['candle_score']=0
    df_candle['candle_pattern']=''


    for c in range(2,len(df_candle)):
        cscore,cpattern=0,''
        lst_3=[df_candle['Open'].iloc[c-3],df_candle['High'].iloc[c-3],df_candle['Low'].iloc[c-3],df_candle['Close'].iloc[c-3]]
        lst_2=[df_candle['Open'].iloc[c-2],df_candle['High'].iloc[c-2],df_candle['Low'].iloc[c-2],df_candle['Close'].iloc[c-2]]
        lst_1=[df_candle['Open'].iloc[c-1],df_candle['High'].iloc[c-1],df_candle['Low'].iloc[c-1],df_candle['Close'].iloc[c-1]]
        lst_0=[df_candle['Open'].iloc[c],df_candle['High'].iloc[c],df_candle['Low'].iloc[c],df_candle['Close'].iloc[c]]
        cscore,cpattern=candle_score(lst_0,lst_1,lst_2, lst_3)    
        df_candle['candle_score'].iat[c]=cscore
        df_candle['candle_pattern'].iat[c]=cpattern
    
    df_candle['candle_cumsum']=df_candle['candle_score'].rolling(3).sum()
    
    return df_candle


def getCandleAndClassify(symbol = symbol, interval = KLINE_INTERVAL_5MINUTE):
  candles = getCandleStick(symbol, interval)
  df = pd.DataFrame(candles,
    columns=['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_Time', 'Quote_Asset_Volume', 'Number_Of_Trades', 'Taker_Buy_Base_Asset_Volume', 'Taker_Buy_Quote_Asset_Volume', 'Ignore'],
    dtype='float64')
  # extract OHLC 
  df=classifyCandles(df)
  df['signal']=np.where(df['candle_cumsum']>1,1,-1)
  df['signal2']=np.where(df['signal']==df['signal'].shift(1),0,df['signal']) 
  df['Open_time'] = (df['Open_time'].astype(int))/1000
  df['Close_Time'] = (df['Close_Time'].astype(int))/1000
  #print(df["Open_time"])
  df['Open_time'] = pd.to_datetime(df['Open_time'],unit="s")
  df['Close_Time'] = pd.to_datetime(df['Close_Time'],unit="s")
  jst = pytz.timezone('Asia/Tokyo')
  df['Open_time'] = df['Open_time'].dt.tz_localize(pytz.utc).dt.tz_convert(jst)
  df['Close_Time'] = df['Close_Time'].dt.tz_localize(pytz.utc).dt.tz_convert(jst)
  
  df['Open_time_str'] = df['Open_time'].apply(lambda x: x.strftime(DATETIME_FORMAT))
  df['Close_Time_str'] = df['Close_Time'].apply(lambda x: x.strftime(DATETIME_FORMAT))
  #print(df["Open_time"])

  return df


def runValidations(current, return_data):
  if REJECT_DOJI and "doji" in current.candle_pattern:
    print("KLINE_LOG: STOP doji Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False
  elif REJECT_EVENING_STAR and "evening_star" in current.candle_pattern:
    print("KLINE_LOG: STOP evening_star Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False  
  elif REJECT_MORNING_STAR and "morning_star" in current.candle_pattern:
    print("KLINE_LOG: STOP morning_star Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False 
  elif REJECT_SHOOTING_STAR_BEARISH and "shooting_Star_bearish" in current.candle_pattern:
    print("KLINE_LOG: STOP shooting_Star_bearish Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False 
  elif REJECT_SHOOTING_STAR_BULLISH and "shooting_Star_bullish" in current.candle_pattern:
    print("KLINE_LOG: STOP shooting_Star_bullish Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False 
  elif REJECT_HAMMER and "hammer" in current.candle_pattern:
    print("KLINE_LOG: STOP hammer Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False  
  elif REJECT_INVERTED_HAMMER and "inverted_hammer" in current.candle_pattern:
    print("KLINE_LOG: STOP inverted_hammer Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False 
  elif REJECT_BEARISH_HARAMI and "bearish_harami" in current.candle_pattern:
    print("KLINE_LOG: STOP bearish_harami Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False
  elif REJECT_BULLISH_HARAMI and "Bullish_Harami" in current.candle_pattern:
    print("KLINE_LOG: STOP Bullish_Harami Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False
  elif REJECT_BEARISH_ENGULFING and "Bearish_Engulfing" in current.candle_pattern:
    print("KLINE_LOG: STOP Bearish_Engulfing Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False 
  elif REJECT_BULLISH_ENGULFING and "Bullish_Engulfing" in current.candle_pattern:
    print("KLINE_LOG: STOP Bullish_Engulfing Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False 
  elif REJECT_BULLISH_REVERSAL and "bullish_reversal" in current.candle_pattern:
    print("KLINE_LOG: STOP bullish_reversal Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False 
  elif REJECT_BEARISH_REVERSAL and "bearish_reversal" in current.candle_pattern:
    print("KLINE_LOG: STOP bearish_reversal Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False 
  elif REJECT_PIERCING_LINE_BULLISH and "Piercing_Line_bullish" in current.candle_pattern:
    print("KLINE_LOG: STOP bullish_reversal Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False 
  elif REJECT_HANGING_MAN_BEARISH and "Hanging_Man_bearish" in current.candle_pattern:
    print("KLINE_LOG: STOP Hanging_Man_bearish Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False 
  elif REJECT_HANGING_MAN_BULLISH and "Hanging_Man_bullish" in current.candle_pattern:
    print("KLINE_LOG: STOP Hanging_Man_bullish Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False 
  elif REJECT_UNIDENTIFIED and current.candle_pattern == "":
    print("KLINE_LOG: STOP Unidentified Candle Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False
  elif REJECT_LAST_2_NEGETIVES and "Last_2_Negetives" in current.candle_pattern:
    print("KLINE_LOG: STOP Last 2 Negetives Pattern Detected!!", return_data)
    time.sleep(INVALID_CANDLE_SLEEP)
    return False

  return True


def saveCandles(return_data):
  for item in return_data:
    new = Candle(
      Open_time_str = item.get("Open_time_str"),
      Open = item.get("Open"),
      High = item.get("High"),
      Low = item.get("Low"),
      Close = item.get("Close"),
      Volume = item.get("Volume"),
      Close_Time_str = item.get("Close_Time_str"),
      Quote_Asset_Volume = item.get("Quote_Asset_Volume"),
      Number_Of_Trades = item.get("Number_Of_Trades"),
      Taker_Buy_Base_Asset_Volume = item.get("Taker_Buy_Base_Asset_Volume"),
      Taker_Buy_Quote_Asset_Volume = item.get("Taker_Buy_Quote_Asset_Volume"),
      Ignore = item.get("Ignore"),
      candle_pattern = item.get("candle_pattern"),
      candle_score = item.get("candle_score"),
      candle_cumsum = item.get("candle_cumsum"),
      signal = item.get("signal"),
      signal2 = item.get("signal2")
    )

    addDataToDB(session, new)
    item["id"] = new.id

  return return_data




def permitCandleStick():
  df = getCandleAndClassify()

  latest_signals = df.nlargest(5,"Open_time")
  current = latest_signals.iloc[0]

  #return_data = latest_signals[LOG_ELEMENTS]
  return_data = latest_signals.to_dict('records')

  return_data = saveCandles(return_data)

  if runValidations(current, return_data) == False:
    return [False, return_data]
  pattern = return_data[0]["candle_pattern"] if return_data[0]["candle_pattern"] != "" else "N/A"
  print("KLINE_LOG: latest_signals[LOG_ELEMENTS]", pattern,latest_signals[LOG_ELEMENTS].to_dict('records'))

  return [True, return_data]

  


