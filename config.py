import os

config = {
"db":"",
"api_key":os.environ["BI_KEY"],
"api_secret":os.environ["BI_SEC"],
"crypto_list":["BTC"],
"stop_loss":0.3,
"profit_rate":0.5,
"stop_profit_rate":0.3,
}
