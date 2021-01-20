from Bollinger_v1 import Bolinger
import time
import backtrader as bt
import backtrader.analyzers as btanalyzers
import pandas as pd
import numpy as np
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import logging

def my_run(arg):
    # 读取数据路径
    '''XBTUSD滚动调参 2020年'''
    # dataframe = pd.read_csv('滚动调参数据/XBTUSD_hour_level/2019-12.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('滚动调参数据/XBTUSD_hour_level/2020-01.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('滚动调参数据/XBTUSD_hour_level/2020-02.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('滚动调参数据/XBTUSD_hour_level/2020-03.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('滚动调参数据/XBTUSD_hour_level/2020-04.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('滚动调参数据/XBTUSD_hour_level/2020-05.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('滚动调参数据/XBTUSD_hour_level/2020-06.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('滚动调参数据/XBTUSD_hour_level/2020-07.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('滚动调参数据/XBTUSD_hour_level/2020-08.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('滚动调参数据/XBTUSD_hour_level/2020-09.csv', index_col=0, parse_dates=[0])
    # dataframe = pd.read_csv('滚动调参数据/XBTUSD_hour_level/2020-10.csv', index_col=0, parse_dates=[0])
    dataframe = pd.read_csv('滚动调参数据/XBTUSD_hour_level/2020-11.csv', index_col=0, parse_dates=[0])

    dataframe['openinterest'] = 0
    data = bt.feeds.PandasData(dataname=dataframe)

    # 实例化大脑
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(commission=0.0004)
    # cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='mysharpe',timeframe=bt.TimeFrame.Months)
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='mydrawdown')

    # 加入策略以及参数
    cerebro.addstrategy(Bolinger, *arg)
    threats=cerebro.run()

    # 建立输出文件的文件名
    # logging.basicConfig(filename='Bolinger_v1_Train201912_to_Test202001.csv', level=logging.DEBUG)
    # logging.basicConfig(filename='Bolinger_v1_Train202001_to_Test202002.csv', level=logging.DEBUG)
    # logging.basicConfig(filename='Bolinger_v1_Train202002_to_Test202003.csv', level=logging.DEBUG)
    # logging.basicConfig(filename='Bolinger_v1_Train202003_to_Test202004.csv', level=logging.DEBUG)
    # logging.basicConfig(filename='Bolinger_v1_Train202004_to_Test202005.csv', level=logging.DEBUG)
    # logging.basicConfig(filename='Bolinger_v1_Train202005_to_Test202006.csv', level=logging.DEBUG)
    # logging.basicConfig(filename='Bolinger_v1_Train202006_to_Test202007.csv', level=logging.DEBUG)
    # logging.basicConfig(filename='Bolinger_v1_Train202007_to_Test202008.csv', level=logging.DEBUG)
    # logging.basicConfig(filename='Bolinger_v1_Train202008_to_Test202009.csv', level=logging.DEBUG)
    # logging.basicConfig(filename='Bolinger_v1_Train202009_to_Test202010.csv', level=logging.DEBUG)
    # logging.basicConfig(filename='Bolinger_v1_Train202010_to_Test202011.csv', level=logging.DEBUG)
    logging.basicConfig(filename='Bolinger_v1_Train202011_to_Test202012.csv', level=logging.DEBUG)


    # 得到最终的净值
    final_value = cerebro.broker.getvalue()
    drawdown = threats[0].analyzers.mydrawdown.get_analysis().max.drawdown

    # 写入输出文档中的数字
    out_message = ',%s,%s,%s,%s,%.2f,%.2f' % (arg[0], arg[1], arg[2], arg[3],final_value,drawdown)
    print(out_message)
    logging.info(out_message)


if __name__ == '__main__':
    params = [] # 建立list 用来存放所有需要调参的参数

    # period_long = 200, dev_long = 2, dev_short = 2, trail_stop_long = 0.1
    for period_long in range(10,300,20):
        for dev_long in range(2,24,2):
            for dev_short in range(2,24,2):
                for trail_stop_long in range(1,30,4):
                    params.append([period_long,dev_long/10,dev_short/10,trail_stop_long/1000])
    print(len(params))



    pool = ProcessPoolExecutor(max_workers=35)
    pool.map(my_run, params)
    pool.shutdown(wait=True)
    pool = None
