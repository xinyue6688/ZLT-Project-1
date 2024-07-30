# -*- coding = utf-8 -*-
# @Time: 2024/07/19
# @Author: Xinyue
# @File:main.py
# @Software: PyCharm

import datetime
import pandas as pd
from scipy.stats.mstats import winsorize
from scipy.stats import zscore
import matplotlib.pyplot as plt
from decimal import Decimal
import numpy as np
import statsmodels.api as sm

from Utils.get_wind_data import WindData
from Utils.data_clean import DataProcess
from Utils.factor_test import FactorDecileAnalysis, FamaFrenchFactor
from Utils.plot_metrics import FactorPerformanceYoY


'''Turnover Factor Test'''
start_time = '20100101'
end_time = datetime.datetime.now().strftime('%Y%m%d')
wind_data = WindData(start_time, end_time)

price_fields = ['S_INFO_WINDCODE','TRADE_DT','S_DQ_ADJPRECLOSE',
                'S_DQ_OPEN', 'S_DQ_ADJCLOSE','S_DQ_LIMIT','S_DQ_STOPPING', 'S_DQ_TRADESTATUS']
price = wind_data.get_prices(price_fields)
price['TRADE_DT'] = pd.to_datetime(price['TRADE_DT'].astype(str))
price = price[price['S_INFO_WINDCODE'].str.endswith(('SH', 'SZ'))]
price = price[price['S_DQ_TRADESTATUS'] != '停牌']
price = price[((price['S_DQ_OPEN'] != price['S_DQ_LIMIT']) &
                                     (price['S_DQ_OPEN'] != price['S_DQ_STOPPING']))]
price.reset_index(inplace=True, drop=True)
print(price.head())

data_processor = DataProcess(start_time, end_time)
price1000 = data_processor.filter_index_cons(price, '000852.SH')
price1000_withind = data_processor.assign_industry(price1000)

dev_fields = ['S_INFO_WINDCODE','TRADE_DT','S_VAL_MV','S_DQ_TURN']
indicators = wind_data.get_indicator(dev_fields)
indicators['TRADE_DT'] = pd.to_datetime(indicators['TRADE_DT'].astype(str))
price1000_withind = pd.merge(price1000_withind, indicators, on = ['S_INFO_WINDCODE', 'TRADE_DT'], how = 'left')
price1000_withind.fillna({'S_DQ_TURN':0}, inplace = True)

price1000_withrt = data_processor.add_future_rt(price1000_withind)
price1000_withrt['S_DQ_TURN_winsorized'] = price1000_withrt.groupby('TRADE_DT')['S_DQ_TURN'].transform(
    lambda x: winsorize(x, limits=[0.05, 0.05]))
price1000_withrt['S_DQ_TURN_norm'] = price1000_withrt.groupby('TRADE_DT')['S_DQ_TURN_winsorized'].transform(lambda x: zscore(x))

cleaned_df = price1000_withrt.groupby('TRADE_DT').apply(lambda x: data_processor.mv_neutralize(x))
cleaned_df.reset_index(inplace = True, drop = True)
sample_df = cleaned_df[(cleaned_df['TRADE_DT'] == '2010-01-04') | (cleaned_df['TRADE_DT'] == '2010-01-05')]
sample_df.to_csv('Data/sample_w_decile.csv', index = False)

liquidity = FactorDecileAnalysis(cleaned_df, group_num=5)
cleaned_df_decile = liquidity.industry_neutralize_and_group()
ew_date_decile = liquidity.calculate_average_daily_returns()
long_short_df = liquidity.long_short_NAV()
benchmark = wind_data.get_industry_index('8841388.WI')
benchmark['TRADE_DT'] = pd.to_datetime(benchmark['TRADE_DT'].astype(str))
benchmark['S_DQ_PCTCHANGE'] = benchmark['S_DQ_PCTCHANGE'].astype(float)
benchmark['S_DQ_PCTCHANGE'] = benchmark['S_DQ_PCTCHANGE'] * 0.01
benchmark['NAV'] = (1 + benchmark['S_DQ_PCTCHANGE']).cumprod()

if isinstance(long_short_df.columns, pd.MultiIndex):
    long_short_df.columns = ['_'.join(map(str, col)).strip() if type(col) is tuple else col for col in long_short_df.columns]
long_short_df.rename(columns={'TRADE_DT_': 'TRADE_DT',
                              'NAV_adj_': 'NAV_adj',
                              'long_short_rt_adj_': 'long_short_rt'}, inplace=True)

aligned_df = pd.merge(long_short_df[['TRADE_DT', 'NAV_adj']], benchmark[['TRADE_DT', 'NAV']], on='TRADE_DT', how='inner')
plt.figure(figsize=(12, 8))
plt.title('NAV')
plt.xlabel('Date')
plt.ylabel('Cumulative NAV')
plt.plot(aligned_df['TRADE_DT'], aligned_df['NAV_adj'], label='Long-Short Portfolio Adjusted (Exposure 1)')
plt.plot(aligned_df['TRADE_DT'], aligned_df['NAV'], label='EW A Index')
plt.legend()
plt.show()

icir_metrics = liquidity.calculate_ic_metrics()
print(icir_metrics)



'''Factor Analysis in Low Inflation Periods'''
time_intervals = [
        ('20000101', '20031031'),
        ('20081201', '20100301'),
        ('20120101', '20151231'),
        ('20200101', '20220930'),
        ('20230101', datetime.datetime.now().strftime('%Y%m%d'))  # 当前日期
    ]
dfs = []

for start_date, end_date in time_intervals:
    get_data = WindData(start_date, end_date)
    industry_data = get_data.get_all_industries()
    dfs.append(industry_data)

data = pd.concat(dfs, ignore_index=True)

data['TRADE_DT'] = pd.to_datetime(data['TRADE_DT'].astype(str))
data[['S_DQ_CLOSE', 'S_DQ_PRECLOSE']] = data[['S_DQ_CLOSE', 'S_DQ_PRECLOSE']].astype(float)
data['RETURN'] = data['S_DQ_CLOSE']/ data['S_DQ_PRECLOSE'] - 1

market = data[data['S_INFO_WINDCODE'] == '8841388.WI']
low_inflation_years = [2001, 2002, 2009, 2012, 2013, 2014, 2015, 2020, 2021, 2023, 2024]
market_py = FactorPerformanceYoY(market, low_inflation_years)
market_py.plot_nav_comparison('Market')
market_performance_metrics = market_py.performance_metrics()
print(market_performance_metrics)

mask = data['S_INFO_WINDCODE'] == '8841388.WI'
datawomarket = data[~mask]

windcodes = ['882010.WI', '882001.WI', '882008.WI']
labels = ['Utilities', 'Energy', 'Information Technology']
for windcode, label in zip(windcodes, labels):
    industry_analyzer = FactorPerformanceYoY(data, low_inflation_years, isindustry=True, windcode=windcode)
    industry_analyzer.plot_nav_comparison(label)
    print(f"{label} industry performance:")
    print(industry_analyzer.performance_metrics())

dfs_price = []
dfs_mvpb = []
price_fields = ['S_INFO_WINDCODE','TRADE_DT','S_DQ_ADJPRECLOSE','S_DQ_ADJCLOSE']
mvpb_fields = ['S_INFO_WINDCODE','TRADE_DT','S_VAL_MV','S_VAL_PB_NEW']

for start_date, end_date in time_intervals:
    get_data = WindData(start_date, end_date)
    price_data = get_data.get_prices(price_fields)
    mvpb_data = get_data.get_indicator(mvpb_fields)
    dfs_price.append(price_data)
    dfs_mvpb.append(mvpb_data)

price_data = pd.concat(dfs_price, ignore_index=True)
mvpb_data = pd.concat(dfs_mvpb, ignore_index=True)

data = pd.merge(price_data, mvpb_data, on=['S_INFO_WINDCODE', 'TRADE_DT'], how='left')
data[['S_DQ_ADJCLOSE', 'S_DQ_ADJPRECLOSE', 'S_VAL_MV','S_VAL_PB_NEW']] = data[['S_DQ_ADJCLOSE', 'S_DQ_ADJPRECLOSE', 'S_VAL_MV','S_VAL_PB_NEW']].astype(float)
data['RETURN'] = data['S_DQ_ADJCLOSE'] / data['S_DQ_ADJPRECLOSE'] - 1
data.sort_values(by='TRADE_DT', ascending=True, inplace=True)
data['RETURN_NXT'] = data.groupby('S_INFO_WINDCODE')['RETURN'].shift(-1)
data['BP'] = 1 / data['S_VAL_PB_NEW']
data.dropna(inplace=True)


#sample_ff = data[(data['TRADE_DT'] == '2010-01-04') | (data['TRADE_DT'] == '2010-01-05')]
#sample_df.to_csv('Data/sample_ff.csv', index = False)


ff3 = FamaFrenchFactor()
grouped_data = ff3.assign_ffgroup(data)
portfolio_return = ff3.calculate_portfolio_return()
SMB, HML = ff3.calculate_factors()
smb_py = FactorPerformanceYoY(SMB, low_inflation_years)
smb_py.plot_nav_comparison('SMB')
smb_performance_metrics = smb_py.performance_metrics()
print(smb_performance_metrics)

hml_py = FactorPerformanceYoY(HML, low_inflation_years)
hml_py.plot_nav_comparison('HML')
hml_performance_metrics = hml_py.performance_metrics()
print(hml_performance_metrics)
