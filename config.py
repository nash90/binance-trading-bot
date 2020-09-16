import os

config = {
"db":"",
"api_key":os.environ["BI_KEY"],
"api_secret":os.environ["BI_SEC"],
"crypto_list":[
    {"asset":"BTC", "exchange":"BTCUSDT", "min_limit":"0.005"}
],
"stop_loss":0.03,
"profit_rate":0.05,
"stop_profit_rate":0.03,
"stop_script":0
}
