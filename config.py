import os

config = {
"db":{
    "type":"sqlite",
    "file":"data.db"
},
"api_key":os.environ["BI_KEY"],
"api_secret":os.environ["BI_SEC"],
"crypto_list":[
    {"asset":"BTC", "exchange":"BTCUSDT", "min_limit":"0.005"}
],
"stop_loss":0.001,
"profit_rate":0.001,
"stop_profit_rate":0.0005,
"stop_script":10,
"day_stop": {
    "loss": 0.03,
    "profit": 0.05
},
"principle_amount":100,
"day_start_amount":10000,
"root_asset": "USDT"
}
