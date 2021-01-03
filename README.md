# trading-bot
The repository consist of binance trading bots. There are two types of bot
1. Kline trading bot
2. 3 way arbitrage bot 

## Installation requirement
* Python 3+
* Pipenv
* Postgres (Not required if using sqlite)
## Kline trading bot: Bot that trades based on Kline pattern with option to train and use ML for trade decision
### how to run
#### Task 1 (Run without ML)
The task for the sample configuration is as follows
* Use sqlite database for simplicity and not to run extra db server
* Kline pattern selected to put market buy order are Bullish_Harami, Bullish_Engulfing, Piercing_Line_bullish, Hanging_Man_bullish
* profit_rate = 0.45% (Start considering Sell order when current market price exceeds 0.45% up of the buy price )
* stop_loss = 0.35% (Put a Sell order when current market price exceeds 0.35 down of the buy price in order to avoid further loss)
* stop_profit_rate = 0.15% ( Put a sell order at 0.15 percent down of profit rate ) A strategy to dynamically update the profit limit price on bullish engulfing. Set to 0 to sell at fixed profit rate
* principle_amount = 100 (Use 100 dollar at one trade)
* {"asset":"BTC", "exchange":"BTCUSDT", "min_limit":"0.005"} (Check BTC kline candle for trading (15 min order book used))

#### Steps
1. Make sure python and pipenv is installed and run ```pipenv install```
2. For above sample task, set configs/config.py as follows

```
import os

db_url = os.environ['PSQL_DB_HOST'] + ':5432/' + os.environ['PSQL_BINBOT_DB_NAME']

config = {
    "reset_db":False, # clear open order in Database if any with flag on
    "start_bot":True, # turn on to run bot, turn off on debug
    "mock_trade":False, # turn on to mock the binance trade transaction instead of a real one
    "db":{
        "db_type":"sqlite", # tested on sqlite and postgresql
        "file":"data.db", # for sqlite embedded db
        "db_url": db_url, # db server url
        "db_username": os.environ['PSQL_BINBOT_DB_USER'], # db username 
        "db_password": os.environ['PSQL_BINBOT_DB_PWD'], # db password
        # db_url, db_username, db_password is not necessary if db_type is set to sqlite
    },
    "api_key":os.environ["BI_KEY"], # set binance key directly here or in .env file
    "api_secret":os.environ["BI_SEC"], # set binance secret directly here on in .env file
    "crypto_list":[
        {"asset":"BTC", "exchange":"BTCUSDT", "min_limit":"0.005"} # min_limit is not used
    ],
    "stop_loss":0.0035, # If current market price drop from buy prices by  more than this rate, do market sell at current price
    "profit_rate":0.0045, # If current market price increase from buy prices by more than this rate, start processing for profit sale
    "stop_profit_rate":0.0015, # If current market pricess drops this rate from the profit_rate (after crossing profit_rate), do market sell at current price to take profit
    "stop_script":0, # run the buy sale for this number of times
    "principle_amount":100, # max amount used in single trading
    "day_start_amount":10000, # not used
    "root_asset": "USDT", # trading base asset
    "bot_freqency":6,
    "profit_sleep": 150, # sleep time on each profit transaction completion
    "loss_sleep": 300, # sleep time on each loss transaction completion
    "error_sleep":11, # sleep time on each unexpected error
    "bot_permit": {
        "check_permit":True, # turn on bot permit related to daily risk stoppage
        "daily_loss_margin": -0.02, # stop bot for a day if daily loss rated drops by this ammount
        "daily_profit_margin": 0.01, # Start considering daily profit dropout at this
        "daily_profit_stop_margin": 0.25, # Stop if daily profit margin was exceeded and then drop by this value
        "validate_candlestick":True, # Turn on to validate the kline candlestick pattern before considering trade
        "invalid_candlestick_sleep":20,
        "reject_candles": { # candles to reject for trading
            "doji": True,
            "evening_star": True,
            "morning_star": True,
            "shooting_Star_bearish": True,
            "shooting_Star_bullish": True,
            "hammer": True,
            "inverted_hammer": True,
            "bearish_harami": True,
            "Bullish_Harami": False, # dont reject bullish patterns
            "Bearish_Engulfing": True,
            "Bullish_Engulfing": False,
            "bullish_reversal": True,
            "bearish_reversal": True,
            "Piercing_Line_bullish": False,
            "Hanging_Man_bearish": True,
            "Hanging_Man_bullish": False,
            "Unidentified": True,
            "Last_2_Negetives":True
        }
    },
}
```
3. From project root run ```pipenv run python script.py ```

#### Task 2 (Run with machine learning enabled)
A sample model is included. The model included as low accuracy, on reason is due to less training dataset. 
To train and create a new model check functions in ml/ml.py
#### Steps
Steps to run the bot with ML model is same as Task 1 steps but need enable the config in config/ml_config
```
ml_config = {
  "enable_ml_trade": True, # flag to enable ML trade on kl bot
  "model_file": "ml/ml_models/mlp_model.txt", # model file
  "scale_file": "ml/ml_models/mlp_scale.txt", # data scaler used by the model
  "min_profitable_probablity": 0.999, # minimum profit probablity prediction to execute (set high if highly uneven dataset)
  "check_profitable_prediction": False, # base in profitable prediction
  "check_loss_prediction": True, # base on loss prediction when False Negetive are high
  "max_loss_probablity": 0.85 # loss probability prediction to consider
}
```
## 3 way arbitrage bot: 3 way trading rate based arbitrage bot
### how to run

1. Make sure python and pipenv is installed and run ```pipenv install```
2. For above sample task, set configs/arbit_config.py as follows
```
import os

arbit_config = {
  "CUT_RATE": 0.00075, # rate charged by binance for each transaction
  "PROMIT_LIMIT": 0.05, # arbitrage minimum profit rate to start trade, set slightly higher cause excution is MARKET SELL type and not limit
  "INIT_ASSET_AMOUNT": 100, # Asset amount size to use in each trade
  "PAUSE_AFTER_TRADE": 30, # time to pause bot after each trade 
  "BOT_CYCLE": 1, # number of cycles to run
  "PAUSE_AFTER_ERROR": 2, # time to pause after unknown error
  "ASSET_LIST": [ # list of asset to try
    ("XRPUSDT", "XRPBNB", "BNBUSDT"),
  ]
}

```
3. From project root run ```pipenv run python arbi_script.py```

