'''
策略描述：
布林策略：
参数包括： 1条中轴线，上轨的距离，下轨的距离，追踪止损的百分比
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader.analyzers as btanalyzers
import pandas as pd
import numpy as np
import backtrader as bt
from collections import deque

# Create a Stratey
class Bolinger(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        time = self.datas[0].datetime.time(0)
        # print('%s, %s ,%s' % (dt.isoformat(), time, txt))

    def __init__(self, period_long=200, dev_long = 2, dev_short = 2, trail_stop_long =0.1):
        # Dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.dataopen = self.datas[0].open
        self.datavolume = self.datas[0].volume

        # Parameters
        self.period_long = period_long #ma140根k线
        self.dev_long = dev_long #高位标准差倍数
        self.dev_short = dev_short #地位标准差倍数
        self.trail_stop_percentage_long = trail_stop_long #移动止损

        # Orders and Trades
        self.order_buy_stop = None
        self.order_sell_stop = None
        self.order_sell = None
        self.order_buy = None
        self.order_sell_trail = None
        self.order_buy_trail = None
        self.trade_amount = None
        self.trade_amount_percentage = 0.5
        self.diff = 0


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f, Amount %.3f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm, order.executed.value / order.executed.price))
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f, Amount %.3f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm, order.executed.value / order.executed.price))

            self.bar_executed = len(self)

        elif order.status in [order.Margin, order.Rejected]:
            self.log('Order Margin/Rejected ----')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
        self.log(self.cerebro.broker.getvalue())

    def cancel_all_order(self):
        if self.order_buy is True:
            self.cancel(self.order_buy)
            self.order_buy = None
        if self.order_sell:
            self.cancel(self.order_sell)
            self.order_sell = None
        if self.order_sell_stop:
            self.cancel(self.order_sell_stop)
            self.order_sell_stop = None
        if self.order_buy_stop:
            self.cancel(self.order_buy_stop)
            self.order_buy_stop = None
        if self.order_buy_trail:
            self.cancel(self.order_buy_trail)
            self.order_buy_trail = None
        if self.order_sell_trail:
            self.cancel(self.order_sell_trail)
            self.order_sell_trail = None

    def get_Bollinger(self):
        close_set = []
        for i in range(-self.period_long + 1 , 1):
            close_set.append(self.dataclose[i])
        mean = np.mean(close_set)
        std = np.std(close_set)
        self.up_track = mean + self.dev_long * std

        close_set = []
        for i in range(-self.period_long + 1, 1):
            close_set.append(self.dataclose[i])
        mean = np.mean(close_set)
        std = np.std(close_set)
        self.down_track = mean - self.dev_long * std

    def get_double_EMA(self):
        if len(self) > 500:
            ema_1 = []
            ema_2 = []
            ema_1.append(self.dataclose[-500+1])
            ema_2.append(self.dataclose[-500+1])
            for i in range (-500+2,1):
                ema_1.append(ema_1[-1] * (1 - 2 / (60 + 1)) + self.dataclose[i] * (2 / (60 + 1)))
                ema_2.append(
                    ema_2[-1] * (1 - 2 / (244 + 1)) + self.dataclose[i] * (2 / (244 + 1)))
            self.diff = ema_1[-1]-ema_2[-1]

    def next(self):
        if len(self) > self.period_long:
            if self.position.size == 0 and self.datas[0].datetime.time().hour == 0:
                self.cancel_all_order()
                self.get_Bollinger()

                self.get_double_EMA()
                if self.diff > 0:
                    aa = 1
                elif self.diff < 0:
                    aa = 1
                else:
                    aa = 1
                self.trade_amount = round(self.cerebro.broker.getvalue() / self.dataopen[0] * self.trade_amount_percentage)
                # print('trade amount is ',self.trade_amount)
                self.order_buy  = self.buy(size=self.trade_amount*aa,price=self.up_track,exectype=bt.Order.Stop)
                self.order_sell = self.sell(size=self.trade_amount*aa,price=self.down_track,exectype=bt.Order.Stop)

            elif self.position.size > 0:
                if self.order_buy_trail == None:
                    self.cancel_all_order()
                    self.order_buy_trail = self.sell(size=abs(self.position.size),
                                                     exectype=bt.Order.StopTrail,
                                                     trailpercent=self.trail_stop_percentage_long)
                # if self.order_buy_trail.status not in [1, 2]:
                #     self.cancel_all_order()
                #     self.order_buy_trail =self.sell(size=abs(self.position.size),
                #                                     exectype=bt.Order.StopTrail,
                #                                     trailpercent=self.trail_stop_percentage_long)

            elif self.position.size < 0:
                if self.order_sell_trail == None:
                    self.cancel_all_order()
                    self.order_sell_trail = self.buy(size=abs(self.position.size),
                                                     exectype=bt.Order.StopTrail,
                                                     trailpercent=self.trail_stop_percentage_long)
                # if self.order_sell_trail.status not in [1, 2]:
                #     self.cancel_all_order()
                #     self.order_sell_trail = self.buy(size=abs(self.position.size),
                #                                      exectype=bt.Order.StopTrail,
                #                                      trailpercent=self.trail_stop_percentage_long)



if __name__ == '__main__':

    cerebro = bt.Cerebro()

    cerebro.addstrategy(Bolinger)

    # dataframe = pd.read_csv('xbtusd_data_201701-201712.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('xbtusd_data_201801-201812.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('data/xbtusd_data_201901-201905.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('data/xbtusd_data_201701-201905.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('data/ethusd_hour_2018-2019.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('data/BTC_bitfinex_17_19_minutes.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('data/bitmex_XBTUSD_2017_2019_1h.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('data/bitfinex_BTCUSD_2017_2019_1h.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('data/bitfinex_ETHUSD_2017_2019_1h.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('hour_data/bitmex_xbtusd_hour_2018_1-12.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('data/bitfinex_LTCUSD_2017_2019_1h.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('data/bitfinex_BTCUSD_2013_2016_1h.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('data/bitmex_XBTUSD_201701_201908_1h.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('data/bitfinex_EOSBTC_2018_2019_1H.csv', index_col=0, parse_dates=[0])

    # dataframe = pd.read_csv('测试数据/hour_data/bitmex_ethusd_hour_2018_1-12.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('测试数据/hour_data/bitmex_ethusd_hour_2019_1-12.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('测试数据/hour_data/bitmex_ethusd_hour_2020_1-12.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('测试数据/hour_data/bitmex_xbtusd_hour_2017_1-12.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('测试数据/hour_data/bitmex_xbtusd_hour_2018_1-12.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('测试数据/hour_data/bitmex_xbtusd_hour_2019_1-12.csv', index_col=0, parse_dates=[0])
    dataframe = pd.read_csv('测试数据/hour_data/bitmex_xbtusd_hour_2020_1-12.csv', index_col=0, parse_dates=[0])

    data = bt.feeds.PandasData(dataname = dataframe)

    cerebro.adddata(data)

    cerebro.broker.setcash(1000000.0)

    cerebro.broker.setcommission(commission=0.001)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='mysharpe', timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='mydrawdown')

    thestrats = cerebro.run()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print('Sharpe Ratio:', thestrats[0].analyzers.mysharpe.get_analysis())
    print('DrawDown:', thestrats[0].analyzers.mydrawdown.get_analysis().max.drawdown)

    # cerebro.plot()