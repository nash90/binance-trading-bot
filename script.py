from config import config
from binance.client import Client
from binance.enums import *

import os

api_key = config["api_key"]
api_secret = config["api_secret"]
client = Client(api_key, api_secret)

crypto_list = config["crypto_list"]
stop_loss_rate = config["stop_loss"]
stop_loss = 10
profit_rate = config["profit_rate"]
stop_profit_rate = config["stop_profit_rate"]
stop_profit = 0



def getTotalBTCAsset():
    pass

def getCurrentAssetRate(asset):
    pass

def buyAsset(asset, buy_rate):
    pass

def getMyPortfolio():
    pass

def setStopLoss():
    pass

def setProfitSale():
    pass

def save_transaction(db_log):
    pass

def get_transaction():
    pass

def buyAssets():
    global stop_loss_sell
    for asset in crypto_list:
        current_rate = getCurrentAssetRate(asset)
        buy_rate = current_rate
        stop_loss = buy_rate - (buy_rate *  stop_loss_rate)
        stop_profit =  buy_rate + (buy_rate * profit_rate)
        buy_txn = buyAsset(asset, buy_rate)

        stop_loss_txn = setStopLoss(asset)
        db_log = {
            "buy_txn":buy_txn,
            "stop_loss_txn":stop_loss_txn,
            "buy_rate":buy_rate,
            "stop_loss":stop_loss,
            "stop_profit":stop_profit,
            "stop_profit_rate":stop_profit_rate
            }
        save_transaction(db_log)


total_btc_asset =0 #getTotalBTCAsset()
my_portfolio = getMyPortfolio()

buy_size = total_btc_asset / len(crypto_list)
buy_size = round(buy_size, 4)

def start_bot():
    my_portfolio = getMyPortfolio()
    if my_portfolio > 1 == False:
        buyAssets()

    if my_portfolio > 1 == True:
        for asset in my_portfolio:
            transaction = get_transaction()
            current_rate = getCurrentAssetRate(asset)
            if current_rate > transaction["stop_profit"]:
                setProfitSale(asset)
