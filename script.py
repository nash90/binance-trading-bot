from config import config
from binance.client import Client
from binance.enums import *
import json

import os
import time

from base import Base
from base import engine
from base import Session
from models import Order

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

session = Session()
# APP constants

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


def marketBuy(exchange, quantity):

    params = {
        "symbol": exchange,
        "quantity": quantity
    }

    print(param)
    order = client.order_market_buy(
        symbol=params.get("symbol"),
        quantity=params.get("quantity")
    )
    print("LOG: Market Buy Asset",order)

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

def marketSell(exchange, quantity):

    params = {
        "symbol": exchange,
        "quantity": quantity
    }

    print(param)
    order = client.order_market_sell(
        symbol=params.get("symbol"),
        quantity=params.get("quantity")
    )
    print("LOG: Market Sell Asset",order)

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
    stop_limit_profit = "N/A"
    
    if current_price > limit_profit:
        stop_limit_profit = current_price - (current_price * stop_profit_rate)

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
        session.rollback()
    #print(e)
    raise e


begin_asset = float(getMyAsset(config.get("root_asset"))["free"])
my_portfolio = getMyPortfolio(crypto_list)

total_root_asset = config.get("principle_amount") # test purpose
buy_size = total_root_asset / len(crypto_list)
buy_size = round(buy_size, 4)


def start():
    #print("LOG: New Cycle)
    global run_count
    asset = crypto_list[0]
    asset_status = '' ## necessary?
    exchange = asset["exchange"]
    root_asset_min_limit = float(asset["min_limit"])

    ## get order of unsold asset from DB
    orders = session.query(Order).filter(Order.bought_flag == True).filter(Order.sold_flag == False).all()
    
    order = None
    if len(orders) > 0
        order = orders[0]
    
    target_asset = getMyAsset(asset["asset"]) ## improve place?
    target_asset_num = round(float(target_asset.get("free")),6) ## might not need here?
    current_price = getCurrentAssetRate(exchange)

    ###################
    ###################
    ###################

    if order == None:
        print("LOG: Create New Fresh Order for Target: ", current_price)
        run_count = run_count+ 1
        ammount = buy_size / current_price
        ammount = round(ammount, 6)
        order = marketBuy(exchange, ammount)   

        db_order = Order(
            symbol = order.get("symbol"),
            order_id = order.get("order_id"),
            client_order_id = order.get("client_order_id"),
            side = order.get("side"),
            type=order.get("type"),
            price= round(float(order.get("price")), 2),
            orig_quantity=round(float(order.get("origQty")),6),
            orig_quantity=round(float(order.get("executedQty")),6),
            server_side_status= order.get("status")
        )

        addDataToDB(db_order)

    else:
        bought_price = order.price
        quantity = order.executed_quantity
        prices = getPrices(exchange, bought_price, current_price)
        order_id = order.order_id

        if order.profit_sale_process_flag == False:
            
            if current_price < prices.get("stop_loss"):
                
                sold = marketSell(exchange, quantity)
                order.market_sell_txn_id = sold.get("orderId")
                order.sold_flag = true
                sessionCommit()

            elif current_price > prices.get("limit_profit"):
                stop_limit_profit = current_price - (current_price * stop_profit_rate)
                profit_sell_stop_limit = setStopLoss(exchange, quantity, round(stop_limit_profit,2))
                order.profit_sale_txn_id = profit_sell_stop_limit.get("orderId")
                order.profit_sale_stop_loss_price = profit_sell_stop_limit.get("price")
                order.profit_sale_process_flag = true
                sessionCommit()

            else:
                print("LOG: Observing Market for Selling Opprtunity", prices) 

        else:
            old_profit_sale_stop_loss_price = order.profit_sale_stop_loss_price

            new_profit_sale_stop_loss_price = current_price - (current_price * stop_profit_rate)

            if old_profit_sale_stop_loss_price < new_profit_sale_stop_loss_price:
                cancel_order =cancelOrder(exchange, order_id)
                order.profit_sale_process_flag = false
                order.profit_sale_txn_id = ""
                order.profit_sale_stop_loss_price = ""
                sessionCommit()

            elif current_price < prices.get("stop_limit_profit"):
                cancel_order =cancelOrder(exchange, order_id)
                time.sleep(5)
                sold = marketSell(exchange, quantity)
                order.market_sell_txn_id = sold.get("orderId")
                order.sold_flag = true
                sessionCommit()


    ###################
    ###################
    ###################


def runBatch():
    global begin_asset
    run = True
    while run:
        current_asset = getMyAsset(config.get("root_asset"))
        #begin_asset = config.get("day_start_amount")
        
        daily_loss_limit = begin_asset - (begin_asset* config["day_stop"]["loss"])
        if float(current_asset["free"]) < daily_loss_limit:
            run = False
            print("LOG: Shut down bot coz of daily loss limit triggered", begin_asset, daily_loss_limit, current_asset)
            break

        if run_count > config.get("stop_script"):
            run = False
            print("LOG: Shut down bot coz batch trade loop count limit triggered", run_count)
            break
        start()
        time.sleep(5)

    session.close()
    
runBatch()
