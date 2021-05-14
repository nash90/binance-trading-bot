"""
Binance Service
"""
import math
import json
from datetime import datetime

from binance.client import Client
from binance.enums import (
    ORDER_TYPE_LIMIT,
    SIDE_BUY,
    TIME_IN_FORCE_GTC,
    SIDE_SELL,
    ORDER_TYPE_STOP_LOSS_LIMIT,
    ORDER_TYPE_MARKET
    )
from configs.config import config
from configs.lotsize import lotsize

api_key = config["api_key"]
api_secret = config["api_secret"]
client = Client(api_key, api_secret)

def getFloor(num, places):
    """docstring"""
    floor = ((math.floor(num * (10 ** places))) / (10 ** places))
    return floor

def roundAssetAmount(amount=0, symbol=''):
    """docstring"""
    amount = float(amount)
    symbol_lotsize = lotsize.get(symbol)
    if symbol_lotsize is not None:
        return getFloor(amount, symbol_lotsize)

    return getFloor(amount, 6)

def roundAssetPrice(amount=0, symbol=''):
    """docstring"""
    amount = float(amount)
    if symbol == 'BTCUSDT':
        return round(amount, 2)
    elif symbol == 'DOGEUSDT':
        return round(amount, 6)
    elif symbol == 'DOGEBTC':
        return round(amount, 8)

    return round(amount, 8)


def getMyAsset(asset_name="BTC"):
    """docstring"""
    asset = client.get_asset_balance(asset=asset_name)
    print("getMyAsset: " + asset_name +" : "+ json.dumps(asset))
    return asset


def getCurrentAssetRate(asset="BTCUSDT"):
    """docstring"""
    rate = 0
    order_book = client.get_order_book(symbol=asset)
    rate = order_book.get("asks")[0][0]
    return float(rate)


def buyAsset(exchange, quantity, price):
    """docstring"""
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
    """docstring"""
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
    """docstring"""
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
    """docstring"""
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
    """docstring"""
    order = client.get_all_orders(symbol=symbol, limit=limit)
    print("LOG: Fetched ALL Order")
    return order


def getOpenOrders(exchange):
    """docstring"""
    order = client.get_open_orders(symbol=exchange)
    print("LOG: Fetched All Open Order")
    return order


def getMyPortfolio(check_list):
    """docstring"""
    my_assets = client.get_account()
    assets = []
    for asset in my_assets["balances"]:
        if any(asset["asset"] == item["asset"] for item in check_list):
            assets.append(asset)
    print("LOG: GOT MY Portfolio")
    return assets


def setStopLoss(exchange, quantity, sell_price):
    """docstring"""
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

def cancelOrder(exchange, order_id):
    """docstring"""
    order = client.cancel_order(
    symbol=exchange,
    orderId=order_id)
    print("LOG: Order was Canceled ", order_id)
    return order
