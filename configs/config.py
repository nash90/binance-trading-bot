import os

db_url = os.environ['PSQL_DB_HOST'] + ':5432/' + os.environ['PSQL_BINBOT_DB_NAME']

config = {
    "use_db_config":True,
    "reset_db":False,
    "start_bot":True,
    "mock_trade":True,    
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
    "stop_loss":0.0035,
    "profit_rate":0.0045,
    "stop_profit_rate":0.0015,
    "stop_script":0,
    "principle_amount":100,
    "day_start_amount":10000,
    "root_asset": "USDT",
    "bot_freqency":6,
    "profit_sleep": 150,
    "loss_sleep": 300,
    "error_sleep":11,
    "bot_permit": {
        "check_permit":False,
        "daily_loss_margin": -0.02,
        "daily_profit_margin": 0.01,
        "daily_profit_stop_margin": 0.25,
        "validate_candlestick":True,
        "validate_candle_rules": True,
        "invalid_candlestick_sleep":20,
        "reject_candles": {
            "doji": True,
            "evening_star": True,
            "morning_star": True,
            "shooting_Star_bearish": True,
            "shooting_Star_bullish": True,
            "hammer": True,
            "inverted_hammer": True,
            "bearish_harami": True,
            "Bullish_Harami": False,
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
