import os
import argparse
import time
import logging
import json
import requests
import pandas as pd
import binance
import math

from binance.client import Client
from binance.enums import *
from datetime import datetime

from configs.config import config
from models.base import Base
from models.base import engine
from models.base import Session
from models.models import Order
from models.models import TradeConfig
from models.mock import getMarketBuyMock
from models.mock import getMarketSellMock
from services.service import checkBotPermit
from services.kline import permitCandleStick
from configs.ml_config import ml_config
from util.utility import loadObject
from util.utility import createNumericCandleDictFromDict


api_key = config["api_key"]
api_secret = config["api_secret"]
client = Client(api_key, api_secret)

crypto_list = config["crypto_list"]
stop_loss_rate = config["stop_loss"]
# stop_loss = 10
profit_rate = config["profit_rate"]
stop_profit_rate = config["stop_profit_rate"]
run_count = 1
STOP_COUNT = config.get("stop_script")
BOT_FREQUENCY = config.get("bot_freqency")
PROFIT_SLEEP = config.get("profit_sleep")
LOSS_SLEEP = config.get("loss_sleep")
ERROR_SLEEP = config.get("error_sleep")
MIN_PROFIT_PROBA = ml_config.get("min_profitable_probablity")
MAX_LOSS_PROBA = ml_config.get("max_loss_probablity")
CHECK_PROFITABLE_PREDICTION = ml_config.get("check_profitable_prediction")
CHECK_LOSS_PREDICTION = ml_config.get("check_loss_prediction")
MOCK_TRADE = config.get("mock_trade")
PAUSE_BUY = False
PAUSE_SELL = False

session = Session()
# APP constants

parser = argparse.ArgumentParser(description = "Description for my parser")
parser.add_argument("-e", "--exchange", help = "Example: select specific exchange", required = False, default = "")
argument = parser.parse_args()

def createTableIfNotExit():
    return Base.metadata.create_all(engine)
createTableIfNotExit()

def getConfigFromDB(exchange=""):
    global db_buy_price, db_sell_price, stop_loss_rate, profit_rate, stop_profit_rate
    global DB_CONFIG, STOP_COUNT, BOT_FREQUENCY, PROFIT_SLEEP, LOSS_SLEEP, ERROR_SLEEP, MOCK_TRADE
    global PAUSE_BUY, PAUSE_SELL, TRADE_ASSET, TRADE_EXCHANGE, TRADE_ASSET2, TRADE_EXCHANGE2, TRADE_ASSET3, TRADE_EXCHANGE3
    if config["use_db_config"] == True:
        db_configs = session.query(TradeConfig).filter(
            TradeConfig.trade_exchange == exchange
        ).all()
        db_config = None if len(db_configs) < 1 else db_configs[0]

        if db_config != None:
            DB_CONFIG = db_config.__dict__
            db_buy_price = db_config.buy_price
            db_sell_price = db_config.stop_loss_price
            stop_loss_rate = db_config.stop_loss_rate
            profit_rate = db_config.profit_rate
            stop_profit_rate = db_config.profit_stop_loss_rate
            STOP_COUNT = db_config.stop_script
            BOT_FREQUENCY = db_config.bot_freqency
            PROFIT_SLEEP = db_config.profit_sleep
            LOSS_SLEEP = db_config.loss_sleep
            ERROR_SLEEP = db_config.error_sleep
            MOCK_TRADE = db_config.mock_trade
            PAUSE_BUY = db_config.pause_buy
            PAUSE_SELL = db_config.pause_sell 
            TRADE_ASSET = db_config.trade_asset
            TRADE_EXCHANGE = db_config.trade_exchange
            TRADE_ASSET2 = db_config.trade_asset2
            TRADE_EXCHANGE2 = db_config.trade_exchange2
            TRADE_ASSET3 = db_config.trade_asset3
            TRADE_EXCHANGE3 = db_config.trade_exchange3

def setDBLogging():
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

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

def roundAssetPrice(amount=0, symbol=''):
    amount = float(amount)
    if symbol == 'BTCUSDT':
        return round(amount, 2)
    elif symbol == 'DOGEUSDT':
        return round(amount, 6)

    return round(amount, 2)

def getMyAsset(assetName="BTC"):
    asset = client.get_asset_balance(asset=assetName)
    print("getMyAsset: " + assetName +" : "+ json.dumps(asset))
    return asset


def getCurrentAssetRate(asset="BTCUSDT"):
    rate = 0
    order_book = client.get_order_book(symbol=asset)
    rate = order_book.get("asks")[0][0]
    return float(rate)


def buyAsset(exchange, quantity, price):
    params = {
        "symbol":exchange,
        "side":SIDE_BUY,
        "type":ORDER_TYPE_LIMIT,
        "timeInForce":TIME_IN_FORCE_GTC,
        "quantity":quantity,
        "price":price
    }
    print(params)
    order = client.create_order(
        symbol=params.get("symbol"),
        side=params.get("side"),
        type=params.get("type"),
        timeInForce=params.get("timeInForce"),
        quantity=params.get("quantity"),
        price=params.get("price"))
    print("LOG: Bought Asset",order)
    return order


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


def sellAsset(exchange, quantity, price):
    order = client.create_order(
        symbol=exchange,
        side=SIDE_SELL,
        type=ORDER_TYPE_MARKET,
        timeInForce=TIME_IN_FORCE_GTC,
        quantity=quantity,
        price=price)
    print(datetime.now(), "LOG: SOLD Asset", order)
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


def getOrders(symbol,limit=1):
    order = client.get_all_orders(symbol=symbol, limit=limit)
    print("LOG: Fetched ALL Order")
    return order


def getOpenOrders(exchange):
    order = client.get_open_orders(symbol=exchange)
    print("LOG: Fetched All Open Order")
    return order


def getMyPortfolio(check_list=crypto_list):
    my_assets = client.get_account()
    assets = []
    for asset in my_assets["balances"]:
        if any(asset["asset"] == item["asset"] for item in check_list):
            assets.append(asset)
    print("LOG: GOT MY Portfolio")
    return assets


def setStopLoss(exchange, quantity, sell_price):
    params = {
        "symbol":exchange,
        "side":SIDE_SELL,
        "type":ORDER_TYPE_STOP_LOSS_LIMIT,
        "timeInForce":TIME_IN_FORCE_GTC,
        "quantity":quantity,
        "price":sell_price
    }
    print(params)

    order = client.create_order(
        symbol=params.get("symbol"),
        side=params.get("side"),
        type=params.get("type"),
        timeInForce=TIME_IN_FORCE_GTC,
        quantity=params.get("quantity"),
        price=params.get("price"),
        stopPrice=params.get("price"))
    print("LOG: Stop Loss was Set",order)
    return order


def getPrices(exchange, buy_price, current_price):
    if current_price == None:
        current_price = getCurrentAssetRate(exchange)
    if buy_price == None:
        buy_price = float(current_price)

    buy_price = float(buy_price)
    stop_loss = buy_price - (buy_price *  stop_loss_rate)
    limit_profit =  buy_price + (buy_price * profit_rate)
    stop_limit_profit = None
    
    if current_price > limit_profit:
        stop_limit_profit = current_price - (current_price * stop_profit_rate)
        stop_limit_profit = float(stop_limit_profit)

    prices = {
        "current_price": current_price,
        "buy_price": buy_price,
        "stop_loss": stop_loss,
        "limit_profit": limit_profit,
        "stop_limit_profit":stop_limit_profit
    }
    return prices


def cancelOrder(exchange, orderId):
    order = client.cancel_order(
    symbol=exchange,
    orderId=orderId)
    print("LOG: Order was Canceled ", orderId)
    return order


def addDataToDB(obj):
  session.add(obj)
  sessionCommit()


def sessionCommit():
    try:  
        session.commit()
    except Exception as e:
        #print(e)
        session.rollback()
        raise e


begin_asset = float(getMyAsset(config.get("root_asset"))["free"])
my_portfolio = getMyPortfolio(crypto_list)

total_root_asset = config.get("principle_amount") # test purpose
buy_size = total_root_asset / len(crypto_list)
buy_size = roundAssetAmount(buy_size, "")


def executeStopLoss(exchange, quantity, order, prices):

    if MOCK_TRADE == True:
        sold = getMarketSellMock(exchange, prices["current_price"], quantity, quantity, buy_size)
    else:
        sold = marketSell(exchange, quantity)
    order.market_sell_txn_id = sold.get("orderId")
    order.sold_flag = True
    order.all_prices = json.dumps(prices)
    order.sold_cummulative_quote_qty = sold.get("cummulativeQuoteQty")
    order.completed_date = datetime.now()

    price_ms = roundAssetPrice(float(sold.get("price")), exchange)
    fills = sold.get("fills")
    if len(fills) > 0:
        price_ms = float(fills[0]["price"])
        price_ms = roundAssetPrice(price_ms, exchange)
    order.marker_sell_price = price_ms

    sessionCommit()   


def createFreshOrder(exchange, current_price, latest_candels):
    ammount = buy_size / current_price
    ammount = roundAssetAmount(ammount, exchange)

    if MOCK_TRADE == True:
        new_order = getMarketBuyMock(exchange, current_price, ammount, ammount, buy_size)
    else:
        new_order = marketBuy(exchange, ammount)  
 
    price_mb = roundAssetPrice(float(new_order.get("price")), exchange)
    fills = new_order.get("fills")
    if len(fills) > 0:
        price_mb = float(fills[0]["price"])
        price_mb = roundAssetPrice(price_mb, exchange)
    candle0 = latest_candels[0].get("id")
    candle1 = latest_candels[1].get("id")
    candle2 = latest_candels[2].get("id")
    candle3 = latest_candels[3].get("id")
    candle4 = latest_candels[4].get("id")

    candle_pattern0 = latest_candels[0].get("candle_pattern")
    candle_pattern1 = latest_candels[1].get("candle_pattern")
    candle_pattern2 = latest_candels[2].get("candle_pattern")
    candle_pattern3 = latest_candels[3].get("candle_pattern")
    candle_pattern4 = latest_candels[4].get("candle_pattern")
    db_order = Order(
        symbol = new_order.get("symbol"),
        order_id = new_order.get("orderId"),
        client_order_id = new_order.get("clientOrderId"),
        side = new_order.get("side"),
        type=new_order.get("type"),
        price= price_mb,
        orig_quantity=roundAssetAmount(float(new_order.get("origQty")),exchange),
        executed_quantity=roundAssetAmount(float(new_order.get("executedQty")),exchange),
        server_side_status= new_order.get("status"),
        bought_flag=True,
        fills = json.dumps(fills)[:499],
        created_date = datetime.now(),
        buy_cummulative_quote_qty = new_order.get("cummulativeQuoteQty"),
        #logs = json.dumps(latest_candels)[:2000],
        candle_pattern0 = candle_pattern0,
        candle_pattern1 = candle_pattern1,
        candle_pattern2 = candle_pattern2,
        candle_pattern3 = candle_pattern3,
        candle_pattern4 = candle_pattern4,
        candle0 = candle0,
        candle1 = candle1,
        candle2 = candle2,
        candle3 = candle3,
        candle4 = candle4
    )

    addDataToDB(db_order)

def validateMLTrade(latest_candels, validated):
    ml_file = ml_config.get("model_file")
    scale_file = ml_config.get("scale_file")
    model = loadObject(ml_file)
    scaler = loadObject(scale_file)

    print(datetime.now(), "LOG: ML model Loaded", model)
    arranged_candel_data = createNumericCandleDictFromDict(
        c0=latest_candels[0],
        c1=latest_candels[1], 
        c2=latest_candels[2], 
        c3=latest_candels[3], 
        c4=latest_candels[4],   
    )
    print(datetime.now(), "LOG: Candle Data arranged before ML check", arranged_candel_data)
    df = pd.DataFrame([arranged_candel_data])
    #print("LOG: Data Frame of arranged Candle Data", df)
    scaled_data = scaler.transform(df)
    probab = model.predict_proba(scaled_data)
    print(datetime.now(), "LOG: Profitability Predictions", probab)
    if CHECK_PROFITABLE_PREDICTION:
        profitable_probablity = probab[0][1]
        if profitable_probablity > MIN_PROFIT_PROBA:
            validated = True 
        else:
            print(datetime.now(), "LOG: Simple Candle Validation Passed but PROFIT Prediction Validation Failed", MIN_PROFIT_PROBA, profitable_probablity)
            validated = False
    if CHECK_LOSS_PREDICTION:
        loss_probablity = probab[0][0]
        if loss_probablity > MAX_LOSS_PROBA:
            validated = False
            print(datetime.now(), "LOG: Simple Candle Validation Passed but LOSS Prediction Validation Failed", MAX_LOSS_PROBA, loss_probablity)
        else:
            validated = True
    return validated

def doSell(exchange, quantity, order, prices):
    executeStopLoss(exchange, quantity, order, prices)
    if STOP_COUNT > 0:
        run_count += 1
    checkBotPermit()

def getTradeAssetInfo():
    asset = crypto_list[0]
    print("argument exchange", argument.exchange)
    if TRADE_EXCHANGE != None and TRADE_EXCHANGE != "":
        asset["exchange"] = TRADE_EXCHANGE
        asset["asset"] = TRADE_ASSET

    print(datetime.now(), "LOG: current asset and exchange: ", asset)
    return asset

def start():
    #print("LOG: New Cycle)
    global run_count
    asset = getTradeAssetInfo()
    exchange = asset["exchange"]

    ## get order of unsold asset from DB
    orders = session.query(Order).filter(
        Order.bought_flag == True).filter(
        Order.sold_flag == False).filter(
        Order.symbol == exchange
        ).all()
    
    order = None
    if len(orders) > 0:
        order = orders[0]
    
    current_price = getCurrentAssetRate(exchange)

    ###################
    ###################
    ###################

    if order == None:
        if PAUSE_BUY:
            print(datetime.now(), "LOG: Pause Buy Flag is ON!!!", current_price)
            return
        print(datetime.now(), "LOG: Try to Create New Fresh Order for Target with Validation checks: ", current_price)
        validated = True
        latest_candels = []
        [validated, latest_candels] = permitCandleStick(exchange, DB_CONFIG)
        # If fixed buy price set, buy and return
        if db_buy_price != None and current_price < db_buy_price:
            print(datetime.now(),"LOG: DB BUY Price Set, Buying at fixed price", db_buy_price)
            createFreshOrder(exchange, current_price, latest_candels)
            return

        if validated == True and ml_config.get("enable_ml_trade") == True:
            validated = validateMLTrade(latest_candels, validated)

        if validated:
            print(datetime.now(), "LOG: ALL Candle Validation Passed!!")
            createFreshOrder(exchange, current_price, latest_candels)

    else:
        print(datetime.now(), "LOG: An Asset to Sell is Found", current_price, order.id)
        if PAUSE_SELL:
            print(datetime.now(), "LOG: Pause Sell Flag is ON!!!")
            return
        bought_price = order.price
        quantity = roundAssetAmount(order.executed_quantity,exchange)
        order_id = order.order_id

        prices = getPrices(exchange, bought_price, current_price)

        price_order_stop_loss = prices.get("stop_loss")
        price_profit_margin = prices.get("limit_profit")
        price_profit_stop_loss = prices.get("stop_limit_profit")

        # If fixed sell price set, sell and return
        if db_sell_price != None and current_price > db_sell_price:
            print(datetime.now(),"LOG: DB Sell Price Set, Selling at fixed price", db_sell_price)
            doSell(exchange, quantity, order, prices)
            time.sleep(PROFIT_SLEEP)
            return

        if order.profit_sale_process_flag == False:
            print(datetime.now(), "LOG: Not Open Sale Stop loss Order ", prices)
            
            if current_price < price_order_stop_loss:
                print(datetime.now(), "LOG: Stop Loss value triggered", current_price, price_order_stop_loss)
                doSell(exchange, quantity, order, prices)
                time.sleep(LOSS_SLEEP)

            elif current_price > price_profit_margin:
                print(datetime.now(), "LOG: Current prices exceeded price_profit_margin; proceed profit stop loss order", current_price, price_order_stop_loss)
                stop_limit_profit = current_price - (current_price * stop_profit_rate)
                #profit_sell_stop_limit = setStopLoss(exchange, quantity, roundAssetPrice(stop_limit_profit,exchange))
                #order.profit_sale_txn_id = profit_sell_stop_limit.get("orderId")
                #order.profit_sale_stop_loss_price = profit_sell_stop_limit.get("price")
                order.profit_sale_stop_loss_price = stop_limit_profit ## bot handles stop loss instead of server
                order.profit_sale_process_flag = True
                sessionCommit()

            else:
                print(datetime.now(), "LOG: Keep Observing Market for Selling Opprtunity", prices) 

        else:
            print(datetime.now(), "LOG: Open Sale Stop loss Order Found ", order.id, prices)
            old_profit_sale_stop_loss_price = order.profit_sale_stop_loss_price

            new_profit_sale_stop_loss_price = current_price - (current_price * stop_profit_rate)

            if old_profit_sale_stop_loss_price < new_profit_sale_stop_loss_price:
                print(datetime.now(), "LOG: More opportunity to Extend open Sale Stop loss Order ", old_profit_sale_stop_loss_price, new_profit_sale_stop_loss_price)
                #cancel_order =cancelOrder(exchange, order_id)
                #order.profit_sale_process_flag = false
                #order.profit_sale_txn_id = ""
                order.profit_sale_stop_loss_price = new_profit_sale_stop_loss_price
                sessionCommit()

            elif current_price < old_profit_sale_stop_loss_price:
                print(datetime.now(), "LOG: Current price dropped below present price_profit_stop_loss;  ", old_profit_sale_stop_loss_price, new_profit_sale_stop_loss_price)
                #cancel_order =cancelOrder(exchange, order_id)
                #time.sleep(5)
                print(datetime.now(), "LOG: Time to cash out .........", prices)
                doSell(exchange, quantity, order, prices)
                time.sleep(PROFIT_SLEEP)


    ###################
    ###################
    ###################


def runBatch():
    global begin_asset
    global run_count
    run = True
    if config.get("reset_db") == True:
        session.query(Order).filter(Order.sold_flag==False).update({Order.sold_flag:True})

    while run:
        getConfigFromDB(argument.exchange)
        if STOP_COUNT > 0 and run_count > STOP_COUNT:
            run = False
            print(datetime.now(), "LOG: Shut down bot coz batch trade loop count limit triggered", run_count)
            break

        try:
            start()
        except (binance.exceptions.BinanceAPIException, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            print(datetime.now(), "Got an ConnectionError exception:" + "\n" + str(e.args) + "\n" + "Ignoring to repeat the attempt later.")
            time.sleep(ERROR_SLEEP)

        time.sleep(BOT_FREQUENCY)

    session.close()


if config.get("start_bot"):      
    runBatch()

            





    
