import time
from datetime import datetime
from datetime import timedelta

from sqlalchemy.sql import text
from sqlalchemy import cast, Date

from configs.config import config
from models.base import Session
from models.models import DailyConfig
from models.models import Order

session = Session()

def getNetProfitByDay(exchange):
    """
    conn = engine.connect()
    s = text(
        "SELECT SUM(((marker_sell_price - price)/price)*100) as NET_PROFIT "
        "FROM orders "
        "WHERE marker_sell_price IS NOT NULL "
        "AND " 
        "CAST(created_date AS DATE) = CAST(now() AS DATE)"
    )
    res = conn.execute(s).fetchall()
    """
    today = datetime.now()
    all_daily_trades = session.query(Order).filter(
        cast(Order.created_date, Date) == cast(today, Date)
    ).filter(
        Order.marker_sell_price.isnot(None)
    ).filter(
        Order.symbol == exchange
    ).all()

    TRADE_CUT_RATE = 0.00075
    daily_profit = 0
    for item in all_daily_trades:
        net_buy_price = item.price + (item.price * TRADE_CUT_RATE)
        net_sell_price = item.marker_sell_price - (item.marker_sell_price * TRADE_CUT_RATE)
        net = ((net_sell_price - net_buy_price) / net_buy_price )

        daily_profit = daily_profit + net

    return float(daily_profit)
    

def sleepTillNextDay(today):
    if today == None:
        today = datetime.today()
    date_ini = datetime(today.year, today.month, today.day)
    next_day = date_ini + timedelta(days=1)
    sleep_time = (next_day-today).total_seconds()
    time.sleep(sleep_time)


def checkBotPermit(db_config=None):

    daily_loss_margin = config.get("bot_permit").get("daily_loss_margin")
    daily_profit_margin = config.get("bot_permit").get("daily_profit_margin")
    daily_profit_stop_margin = config.get("bot_permit").get("daily_profit_stop_margin")
    daily_pause_enabled = config.get("bot_permit").get("check_permit")
    trade_asset = ""
    trade_exchange = ""

    if db_config != None:
        daily_loss_margin = db_config["daily_loss_margin"]
        daily_profit_margin = db_config["daily_profit_margin"]
        daily_profit_stop_margin = db_config["daily_profit_stop_margin"]
        daily_pause_enabled = db_config["daily_pause_permit"]
        trade_asset = db_config["trade_asset"]
        trade_exchange = db_config["trade_exchange"]

    if daily_pause_enabled == False:
        return True

    today = datetime.today()
    get_daily_configs = session.query(DailyConfig).filter(
        cast(DailyConfig.trade_date, Date) == cast(today, Date)
    ).filter(
        DailyConfig.trade_asset == trade_asset
    ).all()
    daily_config = None
    current_daily_net_profit = getNetProfitByDay(exchange=trade_exchange)

    if len(get_daily_configs) < 1:
        print("BOTPERMIT: Creating a new daily config record: asset_num ", trade_asset)
        new_config = DailyConfig(
            trade_date = today,
            daily_loss_margin = daily_loss_margin,
            daily_profit_margin = daily_profit_margin,
            daily_profit_stop_margin = daily_profit_stop_margin,
            trade_asset = db_config["trade_asset"],
        )
        session.add(new_config)
        session.commit()
        daily_config = new_config
    else:
        print("BOTPERMIT: Found daily config record: asset_num ", trade_asset)
        daily_config = get_daily_configs[0]


    if current_daily_net_profit < daily_loss_margin:
        print("BOTPERMIT: Daily loss margin exceeded, Skipping a day!!!",current_daily_net_profit,daily_loss_margin)
        daily_config.bot_status = "SKIPPING"
        daily_config.daily_profit_stopped_value = current_daily_net_profit
        session.commit()
        #sleepTillNextDay(today)
        return False
    else:
        new_daily_profit_stop_limit = current_daily_net_profit - (current_daily_net_profit * daily_profit_stop_margin)
        
        if daily_config.daily_profit_limit_flag:    
            print("BOTPERMIT: Bot daily profit limit setting is ON",current_daily_net_profit,new_daily_profit_stop_limit,daily_config.daily_profit_stop_limit_percent)
            old_daily_profit_stop_limit = daily_config.daily_profit_stop_limit_percent
            if new_daily_profit_stop_limit > old_daily_profit_stop_limit:
                print("BOTPERMIT: Potential to increase daily profit limit", new_daily_profit_stop_limit, old_daily_profit_stop_limit)
                daily_config.daily_profit_stop_limit_percent  = new_daily_profit_stop_limit
                session.commit()

            elif current_daily_net_profit < old_daily_profit_stop_limit:
                print("BOTPERMIT: Skipping now to maintain Profitibility till next day", current_daily_net_profit, old_daily_profit_stop_limit)
                daily_config.bot_status = "SKIPPING"
                daily_config.daily_profit_stopped_value = current_daily_net_profit
                session.commit()
                #sleepTillNextDay(today)
                return False
            else:
                print("BOTPERMIT: Continue bot without new config changes 2: ", current_daily_net_profit)


        else:
            if current_daily_net_profit > daily_profit_margin:
                print("BOTPERMIT: Current Daily Net profit crossed Daily Profit Margin, store it in DB",current_daily_net_profit,daily_profit_margin)
                daily_config.daily_profit_limit_flag = True
                daily_config.daily_profit_stop_limit_percent = new_daily_profit_stop_limit
                session.commit()
            else:
                print("BOTPERMIT: Continue bot without new config changes: ", current_daily_net_profit)
    return True

