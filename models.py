from sqlalchemy import Column, String, Boolean, Numeric, Integer, BigInteger, Date, Table, ForeignKey, DateTime, Sequence
from base import Base
from datetime import datetime
#from sqlalchemy.orm import relationship

class Order(Base):
  __tablename__ = 'orders'
  id = Column('id', BigInteger, primary_key=True)
  order_id = Column('order_id', BigInteger)
  client_order_id = Column('client_order_id', String(50), default="")
  transact_time = Column('transact_time', BigInteger)
  created_date = Column(DateTime, default=datetime.now())
  server_side_status = Column('server_side_status', String(10), default="")
  symbol = Column('symbol', String(10), default="")
  type = Column('type', String(50), default="")
  side = Column('side', String(50), default="")
  average = Column('average', Numeric)
  price = Column('price', Numeric)
  stop_price = Column('stop_price', Numeric)
  stop_limit_price = Column('stop_limit_price', Numeric)
  executed_quantity = Column('executed_quantity', Numeric)
  orig_quantity = Column('orig_quantity', Numeric)
  total = Column('total', Numeric)
  profit_sale_txn_id = Column('profit_sale_txn_id', String(50), default="")
  profit_sale_stop_loss_price = Column('profit_sale_stop_loss_price', Numeric)
  market_sell_txn_id = Column('market_sell_txn_id', String(50), default="")
  marker_sell_price = Column('marker_sell_price', Numeric)
  bought_flag = Column('bought_flag', Boolean, default=False)
  sold_flag = Column('sold_flag', Boolean, default=False)
  profit_sale_process_flag = Column('profit_sale_process_flag', Boolean, default=False)
  all_prices = Column('all_prices', String(200), default="")
  fills = Column('fills', String(500), default="")

class DailyConfig(Base):
  __tablename__ = 'daily_config'
  id = Column('id', BigInteger, primary_key=True)
  trade_date =  Column(Date)
  daily_profit_limit_flag = Column('daily_profit_limit_flag', Boolean, default=False)
  daily_profit_stop_limit_percent = Column('daily_profit_stop_limit_percent', Numeric)