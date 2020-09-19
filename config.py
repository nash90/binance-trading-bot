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
"day_stop": {
    "loss": 0.03,
    "profit": 0.05
},
"principle_amount":100,
"day_start_amount":10000,
"root_asset": "USDT",
}
