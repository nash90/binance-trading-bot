import os
import time
import logging
import json
import requests
import pandas as pd
import math

from binance.client import Client
from binance.enums import *
from datetime import datetime

from configs.config import config
from models.base import Base
from models.base import engine
from models.base import Session
from models.models import Order
from models.models import Market_Arbi
from models.models import Trade_Arbi
from services.service import checkBotPermit
from util.dbutility import addDataToDB 
from util.dbutility import createTableIfNotExit

from configs.arbit_config import arbit_config

api_key = config["api_key"]
api_secret = config["api_secret"]
client = Client(api_key, api_secret)

AB = "BTCUSDT"
BC = "BTCEUR"
CA = "EURUSDT"
CUT_RATE = arbit_config.get("CUT_RATE")
PROMIT_LIMIT = arbit_config.get("PROMIT_LIMIT")
INIT_ASSET_AMOUNT = arbit_config.get("INIT_ASSET_AMOUNT")
PAUSE_AFTER_TRADE = arbit_config.get("PAUSE_AFTER_TRADE")
BOT_CYCLE = arbit_config.get("BOT_CYCLE")
PAUSE_AFTER_ERROR = arbit_config.get("PAUSE_AFTER_ERROR")

def get_all_tikers():
  items = client.get_all_tickers()
  tik = {}
  for item in items:
    key = item.get("symbol")
    tik[key] = item
  return tik
  

def get_all_orderbook():
  items = client.get_orderbook_tickers()
  tik = {}
  for item in items:
    key = item.get("symbol")
    tik[key] = item
  return tik

def getCurrentRate(symbol):
  order_book_ab = client.get_order_book(symbol=symbol)
  rate_ab = order_book_ab.get("asks")[0][0]
  print(datetime.now(), "LOG: Get Current Rate ",symbol, rate_ab)
  return float(rate_ab)

def getCurrentAssetRates(asset_set):
  if asset_set == None:
    ab, bc, ca = AB, BC, CA
  else:
    (ab, bc, ca) = asset_set
    
  order_book_ab = client.get_order_book(symbol=ab)
  rate_ab = order_book_ab.get("asks")[0][0]
  order_book_bc = client.get_order_book(symbol=bc)
  rate_bc = order_book_bc.get("asks")[0][0]
  order_book_ca = client.get_order_book(symbol=ca)
  rate_ca = order_book_ca.get("asks")[0][0]

  #print(rate_ab, rate_bc, rate_ca)

  return (float(rate_ab), float(rate_bc), float(rate_ca))


def limitBuy(exchange, quantity, price):
  
    params = {
        "symbol": exchange,
        "quantity": quantity,
        "price": price
    }

    print(params)
    order = client.order_limit_buy(
        symbol=params.get("symbol"),
        quantity=params.get("quantity"),
        price=params.get("price")
    )
    print(datetime.now(), "LOG: Limit Buy Asset",order)

    return order    


def limitSell(exchange, quantity, price):

    params = {
        "symbol": exchange,
        "quantity": quantity,
        "price": price
    }

    print(params)
    order = client.order_limit_sell(
        symbol=params.get("symbol"),
        quantity=params.get("quantity"),
        price=params.get("price")
    )
    print(datetime.now(), "LOG: Limit Sell Asset",order)

    return order

def checkOrderStatus(exchange, orderId):
    params = {
      "symbol": exchange,
      "orderId": orderId
    }
    print(params)
    order = client.get_order(
      symbol=params.get("symbol"),
      orderId=params.get("orderId"))

    print(datetime.now(), "LOG: Got Order Status",order)

    return order

def checkProfitable(rate_set):
  if rate_set == None:
    (rate_ab, rate_bc, rate_ca) = getCurrentAssetRates()
  else:
    (rate_ab, rate_bc, rate_ca) = rate_set

  start_a = INIT_ASSET_AMOUNT
  #print(start_a)

  to_b = (start_a/rate_ab)
  #print("to_b", to_b)
  cut_cost1 = to_b * (rate_ab) * CUT_RATE
  
  to_c = float(to_b * rate_bc)
  #print("to_c", to_c)
  cut_cost2 = to_c * CUT_RATE * rate_ca
  
  to_a = float(to_c * rate_ca)
  #print("to_a", to_a)
  cut_cost3 = to_a * CUT_RATE
  total_cost = cut_cost1 + cut_cost2 + cut_cost3
  
  profit = ((to_a - start_a)/ start_a)*100
  profit = round(profit, 7)
  #print(profit)
  #print(cut_cost1, cut_cost2, cut_cost3)
  #print(total_cost)

  net_to_a = to_a - total_cost
  net_profit = ((net_to_a - start_a)/start_a)*100
  #print(profit, total_cost, net_profit)

  conversion = (start_a, to_b, to_c, to_a, net_to_a)
  costs = (cut_cost1, cut_cost2, cut_cost3, total_cost)
  profits = (profit, net_profit)
  res = (conversion, costs, profits)
  return res


def saveMarket(asset_set, rate_set, conversion, costs, profits, trade_id, market_time):
  session = Session()
  (ab_symbol, bc_symbol, ca_symbol) = asset_set
  (ab_rate, bc_rate, ca_rate) = rate_set
  (start_a, to_b, to_c, to_a, net_to_a) = conversion
  (cut_cost1, cut_cost2, cut_cost3, total_cost) = costs
  (profit_rate, net_profit_rate) = profits

  if market_time == None:
    market_time = datetime.now()

  record_market_arbi = Market_Arbi(
    market_time = market_time,
    ab_symbol = ab_symbol,
    bc_symbol = bc_symbol,
    ca_symbol = ca_symbol,
    ab_rate = ab_rate,
    bc_rate = bc_rate,
    ca_rate = ca_rate,
    start_a = start_a,
    to_b = to_b,
    to_c = to_c,
    to_a = to_a,
    cut_cost1 = cut_cost1,
    cut_cost2 = cut_cost2,
    cut_cost3 = cut_cost3,
    total_cost = total_cost,
    net_to_a = net_to_a,
    profit_rate = profit_rate,
    net_profit_rate = net_profit_rate,
    trade_id = trade_id
  )
  addDataToDB(session, record_market_arbi)
  session.close()


def saveTrade(asset_set, profits, rate_set, executed_rates, executed_quantity):
  (AB, BC, CA) = asset_set
  (profit_rate, net_profit_rate) = profits
  (ab_rate, bc_rate, ca_rate) = rate_set
  (real_rate_ab, real_rate_bc, real_rate_ca) = executed_rates
  [real_quantity_a, real_quantity_b, real_quantity_c, returned_quantity] = [float(x) for x in executed_quantity]

  session = Session()
  record_trade_arbi = Trade_Arbi(
    market_time = datetime.now(),
    ab_symbol = AB,
    bc_symbol = BC,
    ca_symbol = CA,
    ab_rate = ab_rate,
    bc_rate = bc_rate,
    ca_rate = ca_rate,
    real_rate_ab = real_rate_ab,
    real_rate_bc = real_rate_bc,
    real_rate_ca = real_rate_ca,    
    real_quantity_a = real_quantity_a,
    real_quantity_b = real_quantity_b,
    real_quantity_c = real_quantity_c,
    returned_quantity = returned_quantity,
    predicted_profit_rate = net_profit_rate
  )
  addDataToDB(session, record_trade_arbi)
  trade_id = record_trade_arbi.id
  session.close()
  return trade_id



def getRateFromFills(order):
    fills = order.get("fills")
    price = 0
    if fills != None and len(fills) > 0:
        price = float(fills[0]["price"])
        price = round(price, 6)
    else:
      price = order.get("price")
    return price

def marketBuy(exchange, quantity):
  
    params = {
        "symbol": exchange,
        "quantity": quantity
    }

    print(params)
    order = client.order_market_buy(
        symbol=params.get("symbol"),
        quantity=params.get("quantity")
    )
    print(datetime.now(), "LOG: Market Buy Asset",order)

    return order    


def marketSell(exchange, quantity):

    params = {
        "symbol": exchange,
        "quantity": quantity
    }

    print(params)
    order = client.order_market_sell(
        symbol=params.get("symbol"),
        quantity=params.get("quantity")
    )
    print(datetime.now(), "LOG: Market Sell Asset",order)

    return order


def getFloor(num, places):

  floor = ((math.floor(num * (10 ** places))) / (10 ** places))
  return floor

def roundAssetAmount(amount=0, symbol=''):
  amount = float(amount)

  if symbol == 'ADABNB':
    return getFloor(amount, 0)
  elif symbol == 'ADAUSDT':
    return getFloor(amount, 1)
  elif symbol == 'BTCUSDT':
    return getFloor(amount, 6)
  elif symbol == 'BNBETH':
    return getFloor(amount, 2) 
  elif symbol == 'BNBUSDT':
    return getFloor(amount, 3)
  elif symbol == 'BNBBTC':
    return getFloor(amount, 2)
  elif symbol == 'BNBEUR':
    return getFloor(amount, 3)        
  elif symbol == 'ETHBTC':
    return getFloor(amount, 3)
  elif symbol == 'ETHUSDT':
    return getFloor(amount, 5)
  elif symbol == 'EURUSDT':
    return getFloor(amount, 2)
  elif symbol == 'LINKETH':
    return getFloor(amount, 2)
  elif symbol == 'LINKUSDT':
    return getFloor(amount, 2)
  elif symbol == 'LINKBTC':
    return getFloor(amount, 1)          
  elif symbol == 'TRXXRP':
    return getFloor(amount, 1)
  elif symbol == 'TRXUSDT':
    return getFloor(amount, 1)         
  elif symbol == 'XRPUSDT':
    return getFloor(amount, 1)
  elif symbol == 'XRPBNB':
    return getFloor(amount, 1) 

  return getFloor(amount, 6)

def checkOrderProcessed(symbol, pending_order):
  orderId = pending_order.get("orderId")
  order_done = False
  limit_completed = False
  order = None
  while order_done == False:
    print(datetime.now(), "Log: check if order was processed ", symbol, orderId)
    try:
      order = checkOrderStatus(symbol, orderId)
      # print("Log: New Status Read ", symbol, order)
      if order.get("status") == "FILLED":
        order_done=True
        limit_completed = True
      elif order.get("status") == "CANCELED":
        order_done=True
        limit_completed = False
      else:
        current_rate = getCurrentRate(symbol)
        target_rate = float(order.get("price"))
        drop_per = ((target_rate - current_rate)/target_rate)*100
        print(datetime.now(), "Log: Limit Rate Drop percent: P", drop_per)
        if drop_per >  PROMIT_LIMIT:
          print(datetime.now(), "Log: Stop Loss Triggered: ", symbol, current_rate, " T: ", target_rate)
          
        time.sleep(2)
    except Exception as e:
      print(datetime.now(), "CheckOrder API fail, Try Again")
      time.sleep(2)
  return (limit_completed, order)

class OrderCancelledError(Exception):
    """Exception raised for errors in the input.

    """
    def __init__(self, message):
        self.message = message

def doLimitOrder(symbol, amount, rate, flow):
  limit_completed = False
  order = None
  if flow == "AB":
    order = limitBuy(symbol, amount, rate)
  elif flow == "BC":
    order = limitSell(symbol, amount, rate)
  elif flow == "CA":
    order = limitSell(symbol, amount, rate)

  if order.get("status") == "FILLED":
    limit_completed = True 
  else:
    (limit_completed, order) = checkOrderProcessed(symbol, order)
    if limit_completed == False:
      raise OrderCancelledError("Limit Order Cancelled ")
  return (limit_completed, order)
  

def executeTripleTrade(asset_set, rate_set):
  (AB, BC, CA) = asset_set
  (price_ab, price_bc, price_ca) = rate_set

  quantityA = INIT_ASSET_AMOUNT
  buy_quantity_b = quantityA / price_ab
  buy_quantity_b = roundAssetAmount(buy_quantity_b, AB)
  #order_b = marketBuy(AB, buy_quantity_b)
  (limit_completed, order_b) = doLimitOrder(AB, buy_quantity_b, price_ab, "AB")
  quantityB = order_b.get("executedQty")
  real_quantity_a = order_b.get("cummulativeQuoteQty")
  rate_ab = getRateFromFills(order_b)

  #buy_quantity_c = quantityB / price_bc
  #buy_quantity_c = roundAssetAmount(buy_quantity_c, BC)
  sell_quantity_b = roundAssetAmount(quantityB, BC)
  #order_c = marketSell(BC, sell_quantity_b)
  (limit_completed, order_c) = doLimitOrder(BC, sell_quantity_b, price_bc, "BC")
  quantityC = order_c.get("cummulativeQuoteQty")
  rate_bc = getRateFromFills(order_c)

  sell_quantity_c = roundAssetAmount(quantityC, CA)
  #order_a = marketSell(CA, sell_quantity_c)
  (limit_completed, order_a) = doLimitOrder(CA, sell_quantity_c, price_ca, "CA")
  returned_quantity = roundAssetAmount(order_a.get("cummulativeQuoteQty"))
  rate_ca = getRateFromFills(order_a)

  executed_rates = (rate_ab, rate_bc, rate_ca)
  executed_quantity = (real_quantity_a, sell_quantity_b, sell_quantity_c, returned_quantity)

  return (True, executed_rates, executed_quantity)


def checkProfitMargin(asset_set, profits, rate_set):
  net_profit = profits[1]
  if net_profit > PROMIT_LIMIT:
    (execution_flag, executed_rates, executed_quantity) = executeTripleTrade(asset_set, rate_set)
    if execution_flag:
      trade_id = saveTrade(asset_set, profits, rate_set, executed_rates, executed_quantity)
      return (True, trade_id)
    else:
      print("Trade Cancelled by executeTripleTrade Logic")
      return (False, None)
  return (False, None)


def process_asset(asset_set, tickers):
  if tickers == None:
    rate_set = getCurrentAssetRates(asset_set)
  else:
    (AB, BC, CA) = asset_set
    price_ab = float(tickers.get(AB).get("askPrice"))
    price_bc = float(tickers.get(BC).get("askPrice"))
    price_ca = float(tickers.get(CA).get("askPrice"))
    rate_set = (price_ab, price_bc, price_ca)
  #print(rate_set)
  (conversion, costs, profits) = checkProfitable(rate_set)
  market_time = datetime.now()
  print(market_time, asset_set, profits, costs)
  (trade_executed, trade_id) = checkProfitMargin(asset_set, profits, rate_set)
  saveMarket(asset_set, rate_set, conversion, costs, profits, trade_id, market_time)
  if trade_executed:
    return True
  
  return False



def main():
  asset_list = [
    (AB, BC, CA),
    ("XRPUSDT", "XRPBNB", "BNBUSDT"),
    ("BNBUSDT", "BNBEUR", "EURUSDT"),
    ("LINKUSDT", "LINKBTC", "BTCUSDT"),
    ("ADAUSDT", "ADABNB", "BNBUSDT"),
  ]

  book = get_all_orderbook()
  for asset_set in asset_list:
    trade_executed = process_asset(asset_set, book)
    if trade_executed:
      time.sleep(PAUSE_AFTER_TRADE)
      break


def runBatch():
  print("Starting batch ....")
  run = True
  while run:
    try:
      main()
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout, OrderCancelledError) as e:
      print("Got an ConnectionError exception:" + "\n" + str(e.args) + "\n" + "Ignoring to repeat the attempt later.")
      time.sleep(PAUSE_AFTER_ERROR)

    time.sleep(BOT_CYCLE)

runBatch()