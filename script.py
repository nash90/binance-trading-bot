"""
Entry point of script
"""
#import os
import argparse
import time
import logging
from datetime import datetime
import json
import requests
import pandas as pd
import binance

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

from services.BinanceService import (
    getFloor,
    roundAssetAmount,
    roundAssetPrice,
    getMyAsset,
    getCurrentAssetRate,
    buyAsset,
    marketBuy,
    sellAsset,
    marketSell,
    getOrders,
    getOpenOrders,
    getMyPortfolio,
    setStopLoss,
    cancelOrder,
)

CRYPTO_LIST = config["crypto_list"]
STOP_LOSS_RATE = config["stop_loss"]
# stop_loss = 10
PROFIT_RATE = config["profit_rate"]
STOP_PROFIT_RATE = config["stop_profit_rate"]
RUN_COUNT = 1
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
STOPLOSS_HISTORY = {}
MAX_STOPLOSS_HRS = 2
PARTIAL_STOP_LOSS_COUNT = config.get("partial_stop_loss_count")
PARTIAL_STOP_LOSS_RATE = config.get("partial_stop_loss_rate")
DB_BUY_PRICE = None
DB_CONFIG = None
DB_SELL_PRICE = None

session = Session()
# APP constants

parser = argparse.ArgumentParser(description = "Description for my parser")
parser.add_argument(
    "-a",
    "--asset",
    help = "Example: select specific asset",
    required = False,
    default = "1"
    )
argument = parser.parse_args()

def createTableIfNotExit():
    """docstring"""
    return Base.metadata.create_all(engine)
createTableIfNotExit()

def getConfigFromDB(asset="1"):
    """docstring"""
    global DB_BUY_PRICE, DB_SELL_PRICE, STOP_LOSS_RATE, PROFIT_RATE, STOP_PROFIT_RATE, BUY_SIZE
    global DB_CONFIG, STOP_COUNT, BOT_FREQUENCY, PROFIT_SLEEP, LOSS_SLEEP, ERROR_SLEEP, MOCK_TRADE
    global PAUSE_BUY, PAUSE_SELL, TRADE_ASSET, TRADE_EXCHANGE, TRADE_ASSET2, TRADE_EXCHANGE2, TRADE_ASSET3, TRADE_EXCHANGE3
    global MAX_STOPLOSS_HRS, PARTIAL_STOP_LOSS_COUNT, PARTIAL_STOP_LOSS_RATE
    if config["use_db_config"] == True:
        db_configs = session.query(TradeConfig).filter(
            TradeConfig.trade_asset == asset
        ).all()
        db_config = None if len(db_configs) < 1 else db_configs[0]

        if db_config is not None:
            DB_CONFIG = db_config.__dict__
            DB_BUY_PRICE = db_config.buy_price
            DB_SELL_PRICE = db_config.stop_loss_price
            STOP_LOSS_RATE = db_config.stop_loss_rate
            PROFIT_RATE = db_config.profit_rate
            STOP_PROFIT_RATE = db_config.profit_stop_loss_rate
            BUY_SIZE = db_config.principle_amount
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
            MAX_STOPLOSS_HRS = db_config.max_stoploss_hrs
            PARTIAL_STOP_LOSS_COUNT = db_config.partial_stop_loss_count
            PARTIAL_STOP_LOSS_RATE = db_config.partial_stop_loss_rate

def setDBLogging():
    """docstring"""
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


def getPrices(exchange, buy_price, current_price):
    """docstring"""
    if current_price is None:
        current_price = getCurrentAssetRate(exchange)
    if buy_price is None:
        buy_price = float(current_price)

    buy_price = float(buy_price)
    stop_loss = buy_price - (buy_price *  STOP_LOSS_RATE)
    partial_stop_loss_price = buy_price - (buy_price * STOP_LOSS_RATE * PARTIAL_STOP_LOSS_RATE)
    limit_profit =  buy_price + (buy_price * PROFIT_RATE)
    stop_limit_profit = None

    if current_price > limit_profit:
        stop_limit_profit = current_price - (current_price * STOP_PROFIT_RATE)
        stop_limit_profit = float(stop_limit_profit)

    prices = {
        "current_price": current_price,
        "buy_price": buy_price,
        "stop_loss": stop_loss,
        "limit_profit": limit_profit,
        "stop_limit_profit":stop_limit_profit,
        "partial_stop_loss_price": partial_stop_loss_price,
    }
    return prices


def addDataToDB(obj):
    """docstring"""
    session.add(obj)
    sessionCommit()


def sessionCommit():
    """docstring"""
    try:
        session.commit()
    except Exception as ex:
        #print(ex)
        session.rollback()
        raise ex


begin_asset = float(getMyAsset(config.get("root_asset"))["free"])
my_portfolio = getMyPortfolio(CRYPTO_LIST)

total_root_asset = config.get("principle_amount") # test purpose
BUY_SIZE = total_root_asset / len(CRYPTO_LIST)
BUY_SIZE = roundAssetAmount(BUY_SIZE, "")


def executeStopLoss(exchange, quantity, order, prices):
    """docstring"""
    if MOCK_TRADE:
        sold = getMarketSellMock(exchange, prices["current_price"], quantity, quantity, BUY_SIZE)
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
    """docstring"""
    ammount = BUY_SIZE / current_price
    ammount = roundAssetAmount(ammount, exchange)

    if MOCK_TRADE:
        new_order = getMarketBuyMock(exchange, current_price, ammount, ammount, BUY_SIZE)
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
    """docstring"""
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
    df_candel = pd.DataFrame([arranged_candel_data])
    #print("LOG: Data Frame of arranged Candle Data", df)
    scaled_data = scaler.transform(df_candel)
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
    """docstring"""
    global RUN_COUNT
    executeStopLoss(exchange, quantity, order, prices)
    if STOP_COUNT > 0:
        RUN_COUNT += 1
    #checkBotPermit(DB_CONFIG)


def doStopLossSell(exchange, quantity, order, prices):
    """docstring"""
    global STOPLOSS_HISTORY
    date_hour = datetime.now().strftime("%Y-%m-%d-%H")
    STOPLOSS_HISTORY[date_hour] = 1
    history_size = len(STOPLOSS_HISTORY.keys())
    print(datetime.now(), "LOG: stop loss sell called with STOPLOSS_HISTORY: ", STOPLOSS_HISTORY)
    if history_size > PARTIAL_STOP_LOSS_COUNT:
        print(datetime.now(), "LOG: Setting partial stop loss flag on: ", STOPLOSS_HISTORY, PARTIAL_STOP_LOSS_COUNT)
        order.partial_stop_loss_on = True

    if history_size > MAX_STOPLOSS_HRS:
        doSell(exchange, quantity, order, prices)
        time.sleep(LOSS_SLEEP)
        STOPLOSS_HISTORY = {}


def getTradeAssetInfo():
    """docstring"""
    asset = CRYPTO_LIST[0]
    print("argument asset", argument.asset)
    if TRADE_EXCHANGE is not None and TRADE_EXCHANGE != "":
        asset["exchange"] = TRADE_EXCHANGE
        asset["asset"] = TRADE_ASSET

    print(datetime.now(), "LOG: current asset and exchange: ", asset)
    return asset

def start():
    """docstring"""
    #print("LOG: New Cycle)
    global RUN_COUNT
    asset = getTradeAssetInfo()
    exchange = asset["exchange"]

    ## get order of unsold asset from DB
    orders = session.query(Order).filter(
        Order.bought_flag).filter(
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

    if order is None:
        if PAUSE_BUY:
            print(datetime.now(), "LOG: Pause Buy Flag is ON!!!", current_price)
            return

        print(datetime.now(), "LOG: Try to Create New Fresh Order for Target with Validation checks: ", current_price)
        validated = True
        validated = checkBotPermit(DB_CONFIG)
        latest_candels = []
        if validated:
            [validated, latest_candels] = permitCandleStick(exchange, DB_CONFIG)

        if validated and ml_config.get("enable_ml_trade"):
            validated = validateMLTrade(latest_candels, validated)

        # If fixed buy price set, buy and return
        if DB_BUY_PRICE is not None and current_price < DB_BUY_PRICE:
            print(datetime.now(),"LOG: DB BUY Price Set, Buying at fixed price", DB_BUY_PRICE, current_price)
            createFreshOrder(exchange, current_price, latest_candels)
            return

        if validated:
            print(datetime.now(), "LOG: ALL Candle Validation Passed!!")
            createFreshOrder(exchange, current_price, latest_candels)
        else:
            print(datetime.now(), "LOG: One of the Validation Failed!!")

    else:
        print(datetime.now(), "LOG: An Asset to Sell is Found", current_price, order.id)
        if PAUSE_SELL:
            print(datetime.now(), "LOG: Pause Sell Flag is ON!!!")
            return
        bought_price = order.price
        quantity = roundAssetAmount(order.executed_quantity,exchange)
        #order_id = order.order_id

        prices = getPrices(exchange, bought_price, current_price)

        price_order_stop_loss = prices.get("stop_loss")
        price_profit_margin = prices.get("limit_profit")
        #price_profit_stop_loss = prices.get("stop_limit_profit")
        partial_stop_loss_price = prices.get("partial_stop_loss_price")

        # If fixed sell price set, sell and return
        if DB_SELL_PRICE is not None and current_price > DB_SELL_PRICE:
            print(datetime.now(),"LOG: DB Sell Price Set, Selling at fixed price", DB_SELL_PRICE, current_price)
            doSell(exchange, quantity, order, prices)
            time.sleep(PROFIT_SLEEP)
            return

        if not order.profit_sale_process_flag:
            print(datetime.now(), "LOG: Not Open Sale Stop loss Order ", prices)

            if current_price < price_order_stop_loss:
                print(datetime.now(), "LOG: Stop Loss value triggered", current_price, price_order_stop_loss)
                #doSell(exchange, quantity, order, prices)
                #time.sleep(LOSS_SLEEP)
                doStopLossSell(exchange, quantity, order, prices)

            elif current_price > price_profit_margin:
                print(datetime.now(), "LOG: Current prices exceeded price_profit_margin; proceed profit stop loss order", current_price, price_order_stop_loss)
                stop_limit_profit = current_price - (current_price * STOP_PROFIT_RATE)
                #profit_sell_stop_limit = setStopLoss(exchange, quantity, roundAssetPrice(stop_limit_profit,exchange))
                #order.profit_sale_txn_id = profit_sell_stop_limit.get("orderId")
                #order.profit_sale_stop_loss_price = profit_sell_stop_limit.get("price")
                order.profit_sale_stop_loss_price = stop_limit_profit ## bot handles stop loss instead of server
                order.profit_sale_process_flag = True
                sessionCommit()

            elif order.partial_stop_loss_on and current_price > partial_stop_loss_price:
                print(datetime.now(), "LOG: Partial Stop Loss value triggered", current_price, price_order_stop_loss)
                doSell(exchange, quantity, order, prices)
                time.sleep(LOSS_SLEEP)

            else:
                print(datetime.now(), "LOG: Keep Observing Market for Selling Opprtunity", prices)

        else:
            print(datetime.now(), "LOG: Open Sale Stop loss Order Found ", order.id, prices)
            old_profit_sale_stop_loss_price = order.profit_sale_stop_loss_price

            new_profit_sale_stop_loss_price = current_price - (current_price * STOP_PROFIT_RATE)

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
    """docstring"""
    global begin_asset
    global RUN_COUNT
    run = True
    if config.get("reset_db"):
        session.query(Order).filter(Order.sold_flag == False).update({Order.sold_flag:True})

    while run:
        getConfigFromDB(argument.asset)
        if STOP_COUNT > 0 and RUN_COUNT > STOP_COUNT:
            run = False
            print(datetime.now(), "LOG: Shut down bot coz batch trade loop count limit triggered", RUN_COUNT)
            break

        try:
            start()
        except (binance.exceptions.BinanceAPIException, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as ex:
            print(datetime.now(), "Got an ConnectionError exception:" + "\n" + str(ex.args) + "\n" + "Ignoring to repeat the attempt later.")
            print(ex)
            time.sleep(ERROR_SLEEP)

        time.sleep(BOT_FREQUENCY)

    session.close()


if config.get("start_bot"):
    runBatch()
