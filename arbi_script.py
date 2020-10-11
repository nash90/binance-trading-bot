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

from config import config
from base import Base
from base import engine
from base import Session
from models import Order
from models import Market_Arbi
from models import Trade_Arbi
from helpers import checkBotPermit
from dbutility import addDataToDB 
from dbutility import createTableIfNotExit

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


def saveMarket(asset_set, rate_set, conversion, costs, profits):
  session = Session()
  (ab_symbol, bc_symbol, ca_symbol) = asset_set
  (ab_rate, bc_rate, ca_rate) = rate_set
  (start_a, to_b, to_c, to_a, net_to_a) = conversion
  (cut_cost1, cut_cost2, cut_cost3, total_cost) = costs
  (profit_rate, net_profit_rate) = profits

  record_market_arbi = Market_Arbi(
    market_time = datetime.now(),
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
    net_profit_rate = net_profit_rate
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
  session.close()



def getRateFromFills(order):
    fills = order.get("fills")
    price = 0
    if len(fills) > 0:
        price = float(fills[0]["price"])
        price = round(price, 6)
    
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
    print("LOG: Market Buy Asset",order)

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
    print("LOG: Market Sell Asset",order)

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



def executeTripleTrade(asset_set, rate_set):
  (AB, BC, CA) = asset_set
  (price_ab, price_bc, price_ca) = rate_set

  quantityA = INIT_ASSET_AMOUNT
  buy_quantity_b = quantityA / price_ab
  buy_quantity_b = roundAssetAmount(buy_quantity_b, AB)
  order_b = marketBuy(AB, buy_quantity_b)
  quantityB = order_b.get("executedQty")
  rate_ab = getRateFromFills(order_b)

  #buy_quantity_c = quantityB / price_bc
  #buy_quantity_c = roundAssetAmount(buy_quantity_c, BC)
  sell_quantity_b = roundAssetAmount(quantityB, BC)
  order_c = marketSell(BC, sell_quantity_b)
  quantityC = order_c.get("cummulativeQuoteQty")
  rate_bc = getRateFromFills(order_c)

  sell_quantity_c = roundAssetAmount(quantityC, CA)
  order_a = marketSell(CA, sell_quantity_c)
  returned_quantity = roundAssetAmount(order_a.get("cummulativeQuoteQty"))
  rate_ca = getRateFromFills(order_a)

  executed_rates = (rate_ab, rate_bc, rate_ca)
  executed_quantity = (quantityA, quantityB, quantityC, returned_quantity)

  return (executed_rates, executed_quantity)


def checkProfitMargin(asset_set, profits, rate_set):
  net_profit = profits[1]
  if net_profit > PROMIT_LIMIT:
    (executed_rates, executed_quantity) = executeTripleTrade(asset_set, rate_set)
    saveTrade(asset_set, profits, rate_set, executed_rates, executed_quantity)
    return True 
  return False


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
  print(asset_set, profits, costs)
  trade_executed = checkProfitMargin(asset_set, profits, rate_set)
  saveMarket(asset_set, rate_set, conversion, costs, profits)
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
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
      print("Got an ConnectionError exception:" + "\n" + str(e.args) + "\n" + "Ignoring to repeat the attempt later.")
      time.sleep(PAUSE_AFTER_ERROR)

    time.sleep(BOT_CYCLE)

runBatch()