import os

db_url = os.environ['PSQL_DB_HOST'] + ':5432/' + os.environ['PSQL_BINBOT_DB_NAME']

config = {
    "reset_db":False,
    "start_bot":True,    
    "db":{
        "db_type":"postgresql",
        "file":"data.db",
        "db_url": db_url,
        "db_username": os.environ['PSQL_BINBOT_DB_USER'],
        "db_password": os.environ['PSQL_BINBOT_DB_PWD'],    
    },
    "api_key":os.environ["BI_KEY"],
    "api_secret":os.environ["BI_SEC"],
    "crypto_list":[
        {"asset":"BTC", "exchange":"BTCUSDT", "min_limit":"0.005"}
    ],
    "stop_loss":0.001,
    "profit_rate":0.0009,
    "stop_profit_rate":0.0004,
    "stop_script":15,
    "principle_amount":100,
    "day_start_amount":10000,
    "root_asset": "USDT",
    "bot_freqency":6,
    "profit_sleep": 150,
    "loss_sleep": 300,
    "error_sleep":11,
    "bot_permit": {
        "check_permit":True,
        "daily_loss_margin": -0.003,
        "daily_profit_margin": 0.003,
        "daily_profit_stop_margin": 0.25,
        "validate_candlestick":True,
        "invalid_candlestick_sleep":20
    }
}
