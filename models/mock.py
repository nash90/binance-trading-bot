import os

market_sell_fills_sample = [
      {
         "price":"28986.90000000",
         "qty":"0.00346000",
         "commission":"0.00200700",
         "commissionAsset":"BNB",
         "tradeId":537214681
      }
   ]

market_sell_sample = {
   "symbol":"BTCUSDT",
   "orderId":9999999999,
   "orderListId":-1,
   "clientOrderId":"vUhAlb6sinPg0Uasi6H52w",
   "transactTime":1609485562047,
   "price":"0.00000000",
   "origQty":"0.00346000",
   "executedQty":"0.00346000",
   "cummulativeQuoteQty":"100.29467400",
   "status":"FILLED",
   "timeInForce":"GTC",
   "type":"MARKET",
   "side":"SELL",
   "fills": market_sell_fills_sample
}

market_buy_fills_sample = [
      {
         "price":"28900.17000000",
         "qty":"0.00346000",
         "commission":"0.00200711",
         "commissionAsset":"BNB",
         "tradeId":537201771
      }
   ]


market_buy_sample = {
   "symbol":"BTCUSDT",
   "orderId":9999999998,
   "orderListId":-1,
   "clientOrderId":"yXdQNlltMJMyGZ9KuBiINO",
   "transactTime":1609485044436,
   "price":"0.00000000",
   "origQty":"0.00346000",
   "executedQty":"0.00346000",
   "cummulativeQuoteQty":"99.99458820",
   "status":"FILLED",
   "timeInForce":"GTC",
   "type":"MARKET",
   "side":"BUY",
   "fills":market_buy_fills_sample
}

def getMarketBuyMock(symbol, price, qty, executedQty, cummulativeQuoteQty):
  market_buy_fills = market_buy_fills_sample
  market_buy_fills[0]["price"] = price
  market_buy_fills[0]["qty"] = qty

  market_buy = market_buy_sample
  market_buy["symbol"] = symbol
  market_buy["price"] = price
  market_buy["origQty"] = qty
  market_buy["executedQty"] = qty
  market_buy["cummulativeQuoteQty"] = cummulativeQuoteQty
  market_buy["fills"] = market_buy_fills
  print("LOG: Trade Mock: Market Buy", market_buy)
  return market_buy


def getMarketSellMock(symbol, price, qty, executedQty, cummulativeQuoteQty):
  cummulativeQuoteQty = price * qty
  market_sell_fills = market_sell_fills_sample
  market_sell_fills[0]["price"] = price
  market_sell_fills[0]["qty"] = qty

  market_sell = market_sell_sample
  market_sell["symbol"] = symbol
  market_sell["price"] = price
  market_sell["origQty"] = qty
  market_sell["executedQty"] = qty
  market_sell["cummulativeQuoteQty"] = cummulativeQuoteQty
  market_sell["fills"] = market_sell_fills
  print("LOG: Trade Mock: Market Sell", market_sell)
  return market_sell

  