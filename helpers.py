from datetime import datetime
from datetime import timedelta

from sqlalchemy.sql import text
from sqlalchemy import cast, Date

from config import config
from base import Session
from models import DailyConfig
from models import Order

session = Session()

def getNetProfitByDay():
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
        cast(Order.created_date, Date) == cast(today, Date)).filter(
            Order.marker_sell_price.isnot(None)).all()

    daily_profit = 0
    for item in all_daily_trades:
        net = ((item.marker_sell_price - item.price) / item.price )

        daily_profit = daily_profit + net

    return float(daily_profit)
    

def sleepTillNextDay(today):
    if today == None:
        today = datetime.today()
    date_ini = datetime(today.year, today.month, today.day)
    next_day = date_ini + timedelta(days=1)
    sleep_time = (next_day-today).total_seconds()
    time.sleep(sleep_time)


def checkBotPermit():
    if config.get("check_permit") == False:
        return

    daily_loss_margin = config.get("bot_permit").get("daily_loss_margin")
    daily_profit_margin = config.get("bot_permit").get("daily_profit_margin")
    daily_profit_stop_margin = config.get("bot_permit").get("daily_profit_stop_margin")

    today = datetime.today()
    get_daily_configs = session.query(DailyConfig).filter(cast(DailyConfig.trade_date, Date)==cast(today, Date)).all()
    daily_config = None
    current_daily_net_profit = getNetProfitByDay()

    if len(get_daily_configs) < 1:
        print("BOTPERMIT: Creating a new daily config record")
        new_config = DailyConfig(
            trade_date = today,
            daily_loss_margin = daily_loss_margin,
            daily_profit_margin = daily_profit_margin,
            daily_profit_stop_margin = daily_profit_stop_margin
        )
        session.add(new_config)
        session.commit()
        daily_config = new_config
    else:
        print("BOTPERMIT: Found daily config record")
        daily_config = get_daily_configs[0]


    if current_daily_net_profit < daily_loss_margin:
        print("BOTPERMIT: Daily loss margin exceeded, Sleeping a day!!!",current_daily_net_profit,daily_loss_margin)
        daily_config.bot_status = "SLEEPING"
        daily_config.daily_profit_stopped_value = current_daily_net_profit
        session.commit()
        sleepTillNextDay(today)
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
                print("BOTPERMIT: Sleeping now to maintain Profitibility till next day", current_daily_net_profit, old_daily_profit_stop_limit)
                daily_config.bot_status = "SLEEPING"
                daily_config.daily_profit_stopped_value = current_daily_net_profit
                session.commit()
                sleepTillNextDay(today)
            else:
                print("BOTPERMIT: Continue bot without new config changes: ", current_daily_net_profit)


        else:
            if current_daily_net_profit > daily_profit_margin:
                print("BOTPERMIT: Current Daily Net profit crossed Daily Profit Margin, store it in DB",current_daily_net_profit,daily_profit_margin)
                daily_config.daily_profit_limit_flag = True
                daily_config.daily_profit_stop_limit_percent = new_daily_profit_stop_limit
                session.commit()
            else:
                print("BOTPERMIT: Continue bot without new config changes: ", current_daily_net_profit)

