from config import config
from binance.client import Client
from binance.enums import *
import json

import os
import time

api_key = config["api_key"]
api_secret = config["api_secret"]
client = Client(api_key, api_secret)

crypto_list = config["crypto_list"]
stop_loss_rate = config["stop_loss"]
stop_loss = 10
profit_rate = config["profit_rate"]
stop_profit_rate = config["stop_profit_rate"]
stop_profit = 0
run_count = 0


def getMyAsset(assetName="BTC"):
    asset = client.get_asset_balance(asset=assetName)
    print("getMyAsset: " + assetName +" : "+ json.dumps(asset))
    return asset

def getCurrentAssetRate(asset):
    rate = 0
    all_tickers = client.get_all_tickers()
    for item in all_tickers:
        if item["symbol"] == asset:
            rate = item["price"]
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

def sellAsset(exchange, quantity, price):
    order = client.create_order(
        symbol=exchange,
        side=SIDE_SELL,
        type=ORDER_TYPE_MARKET,
        timeInForce=TIME_IN_FORCE_GTC,
        quantity=quantity,
        price=price)
    print("LOG: SOLD Asset", order)
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
    stop_limit_profit = buy_price - (buy_price * stop_profit_rate)
    if current_price < limit_profit:
        stop_limit_profit = "N/A"
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

def setProfitSale():
    pass

def saveTransaction(db_log):
    pass

def getTransaction():
    pass

def buyAssets():
    global stop_loss_sell
    for asset in crypto_list:
        current_rate = getCurrentAssetRate(asset)
        buy_rate = float(current_rate)
        stop_loss = buy_rate - (buy_rate *  stop_loss_rate)
        stop_profit =  buy_rate + (buy_rate * profit_rate)
        buy_txn = buyAsset(round(asset,3), buy_rate)

        stop_loss_txn = setStopLoss(asset)
        db_log = {
            "buy_txn":buy_txn,
            "stop_loss_txn":stop_loss_txn,
            "buy_rate":buy_rate,
            "stop_loss":stop_loss,
            "stop_profit":stop_profit,
            "stop_profit_rate":stop_profit_rate
            }
        saveTransaction(db_log)


begin_asset = float(getMyAsset(config.get("root_asset"))["free"])
my_portfolio = getMyPortfolio(crypto_list)

total_root_asset = config.get("principle_amount") # test purpose
buy_size = total_root_asset / len(crypto_list)
buy_size = round(buy_size, 4)

def startBot():
    my_portfolio = getMyPortfolio()
    if my_portfolio > 1 == False:
        buyAssets()

    if my_portfolio > 1 == True:
        for asset in my_portfolio:
            transaction = getTransaction()
            current_rate = getCurrentAssetRate(asset)
            if current_rate > transaction["stop_profit"]:
                setProfitSale(asset)

def getOrderStatus(res):
    asset_status = ""
    if res["side"] == 'BUY' and res["status"] == "FILLED":
        asset_status = "BUY_FILLED"
    elif res["side"] == 'BUY' and res["status"] == "CANCELED":
        asset_status = "BUY_CANCELED"
    elif res["side"] == 'BUY' and res["status"] == "NEW":
        asset_status = "BUY_NEW"
    elif res["side"] == "SELL" and res["status"] == "FILLED":
        asset_status = "SELL_FILLED"
    elif res["side"] == "SELL" and res["status"] == "CANCELED":
        asset_status = "SELL_CANCELED"
    elif res["side"] == "SELL" and res["status"] == "NEW":
        asset_status = "SELL_NEW"
    else:
        asset_status = "OTHERS"
    return asset_status

def start2():
    #print("LOG: New Cycle)
    global run_count
    asset = crypto_list[0]
    asset_status = ''
    exchange = asset["exchange"]
    root_asset_min_limit = float(asset["min_limit"])
    orders = getOrders(exchange)
    order = orders[0]
    openOrders = getOpenOrders(exchange)
    asset_status = getOrderStatus(order)
    target_asset = getMyAsset(asset["asset"])
    
    target_asset_num = round(float(target_asset.get("free")),6) 
    current_price = getCurrentAssetRate(exchange)

    if openOrders == [] and (asset_status == "BUY_FILLED" or asset_status == "SELL_CANCELED") and target_asset_num > root_asset_min_limit:
        print("LOG: Target Asset Already Bought: ", current_price)
        quantity = target_asset_num
        bought_price = order["price"]
        prices = getPrices(exchange, bought_price, current_price)
        print("LOG: Prices", prices)
        if current_price < prices["stop_loss"]:
            print("LOG: Target Asset already exists and Risk Stop loss Exceeded; Run Sell")
            order = sellAsset(exchange, quantity, current_price)
        elif current_price > prices["limit_profit"]:
            print("LOG: Current price exceeds Profit limit; Run Profit stop loss")
            stop_limit_profit = current_price - (current_price * stop_profit_rate)
            order = setStopLoss(exchange, quantity, round(stop_limit_profit,2))
    elif openOrders == []:
        print("LOG: Create New Fresh Order for Target: ", current_price)
        run_count = run_count+ 1
        current_price = getCurrentAssetRate(exchange)
        ammount = buy_size / current_price
        ammount = round(ammount, 6)
        order = buyAsset(exchange, ammount, current_price)


    elif openOrders != [] and asset_status == "SELL_NEW":
        print("LOG: Open Sell Order Found ", current_price, openOrders)
        quantity = target_asset_num
        bought_price = order["price"]
        prices = getPrices(exchange, bought_price, current_price)

        if current_price < prices["stop_loss"]:
            print("LOG: Open Sell order found and exceeds Risk Stop Loss; retry sell again", prices)
            order =cancelOrder(exchange, order["orderId"])
            #order = sellAsset(exchange, quantity, current_price)
    
        elif order["type"] == "STOP_LOSS_LIMIT" and current_price > prices["limit_profit"]:
            print("LOG: Open STOP_LOSS_LIMIT order; Current Price is over Default Profit limit", prices)
            stop_limit_profit = current_price - (current_price * stop_profit_rate)
            if float(order["price"]) < stop_limit_profit:
                print("LOG: Open STOP_LOSS_LIMIT order; Found Potential to extend Profit Stop Limit")
                print("LOG: Cancel previos Sell Order")
                order =cancelOrder(exchange, order["orderId"])
                #print("LOG: Create New Sell Order Profit Stop Limit ")
                #order = setStopLoss(exchange, quantity, round(stop_limit_profit,2))
        
    elif openOrders != [] and asset_status == "BUY_NEW":
        print("LOG: BUY_NEW; Open Buy Order Found", current_price, openOrders)


def runBatch():
    global begin_asset
    run = True
    while run:
        current_asset = getMyAsset(config.get("root_asset"))
        #begin_asset = config.get("day_start_amount")
        
        daily_loss_limit = begin_asset - (begin_asset* config["day_stop"]["loss"])
        if float(current_asset["free"]) < daily_loss_limit:
            run = False
            print("LOG: Shut down bot coz of daily loss limit triggered")

        if run_count > config.get("stop_script"):
            run = False
            print("LOG: Shut down bot coz batch trade loop count limit triggered")
        start2()
        time.sleep(5)


runBatch()