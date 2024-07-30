# FactorTest
换手率因子分层检验;低通胀时期历年行业因子、Fama-French SMB & HML 因子实证及表现对比

Project for liquidity factor decile test and Fama-French SMB & HML empirical analysis on China A share in low inflation eras
## 1. Data
功能使用范例数据

Sample data for function illustration
## 2. Utils
### 2.1 [get_wind_data.py](https://github.com/xinyue6688/ZLT-Project-1/blob/main/FactorTest/Utils/connect_wind.py)
从wind获取数据

Obtain data from wind API
### 2.2 [data_clean.py](https://github.com/xinyue6688/ZLT-Project-1/blob/main/FactorTest/Utils/data_clean.py)
跟踪指数成分股、分配行业、因子值市值中性化

Data processing class to follow index consitituent, assign industry, and calculate market value neutrailzed factor value
### 2.3 [factor_test.py](https://github.com/xinyue6688/ZLT-Project-1/blob/main/FactorTest/Utils/factor_test.py)
因子分层检验及FF因子构建

Factor decile test and construction of Fama-French factors
### 2.4 [plot_metrics.py](https://github.com/xinyue6688/ZLT-Project-1/blob/main/FactorTest/Utils/plot_metrics.py)
净值走势画图、收益率特性分析

Plot NAV, calculate return metrics
