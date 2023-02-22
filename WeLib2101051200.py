#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'weq.we@qq.com'

from datetime import datetime
import pandas as pd
import numpy as np
import math
import random
import os
from pyecharts.components import Table
from pyecharts.options import ComponentTitleOpts
from numba import jit
import tkinter.filedialog
from tkinter import Tk
import ast
import requests


'''
部分使用numpy实现并用numba加速的功能在循环外单独使用时可能会因为加速器编译消耗时间而比使用list实现的方法消耗更多时间
'''


# *-*-*-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-内部调用函数-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-

@jit()
def _Kline_numba(一分钟K线, K线级别, 小时列表, 是否跨日截断=True):  # 改为numpy生成并用numba加速

    n = 0  # 用于合成K线时的数量控制
    每根K线开始位置 = np.zeros_like(小时列表)
    每根K线结束位置 = np.zeros_like(小时列表)
    每根K线开始标记 = np.zeros_like(小时列表)
    合成了几根K线 = 0
    长度 = 小时列表.shape[0]
    当前K线起点 = 0

    for i in range(长度):
        if 一分钟K线[i, 4] != 0:
            n += 1
            每根K线结束位置[合成了几根K线] = i
            if n == 1:
                当前K线起点 = i
        # print(f"n值{n}")

        # 判断新K线是否属于新的交易日
        # 假设一个交易日的结束时间不晚于18点，即18点之前结束当前交易日
        # 那么，可将18点定义为0、19点定义为1、……、21点定义为3、……、9点定义为15、……、14点定义为20、15点定义为21、……
        # 两根相邻的1分钟K线，如果跨交易日，必然：后一K线的时小于前一K线的时。
        if n != 0:
            if n % K线级别 == 0:  # 添加一行，合成新的K线
                每根K线开始位置[合成了几根K线] = 当前K线起点
                合成了几根K线 += 1
                n = 0

            elif 是否跨日截断 and i < 小时列表.shape[0] - 1:
                if (小时列表[i] + 6) % 24 > (小时列表[i + 1] + 6) % 24:
                    每根K线开始位置[合成了几根K线] = 当前K线起点
                    合成了几根K线 += 1
                    n = 0

    # 处理最后一根可能没有走完的K线
    if n != 0:  # 即在最后一段时间里出现了成交量不为零的一分钟K线
        每根K线开始位置[合成了几根K线] = 当前K线起点
        合成了几根K线 += 1

    K线列表 = np.zeros((合成了几根K线, 7))

    for k in range(合成了几根K线):
        每根K线开始标记[每根K线开始位置[k]] = 1
        K线列表[k, 0] = 一分钟K线[每根K线开始位置[k], 0]
        K线列表[k, 1] = np.max(一分钟K线[每根K线开始位置[k]:每根K线结束位置[k] + 1, 0:4])
        K线列表[k, 2] = np.min(一分钟K线[每根K线开始位置[k]:每根K线结束位置[k] + 1, 0:4])
        K线列表[k, 3] = 一分钟K线[每根K线结束位置[k], 3]
        K线列表[k, 4] = np.sum(一分钟K线[每根K线开始位置[k]:每根K线结束位置[k] + 1, 4])
        K线列表[k, 5] = 一分钟K线[每根K线开始位置[k], 5]
        K线列表[k, 6] = 一分钟K线[每根K线结束位置[k], 6]

    # # 第 合成了几根K线 根K线的数据
    # 每根K线开始标记[每根K线开始位置[合成了几根K线 - 1]] = 1
    # K线列表[合成了几根K线 - 1, 0] = 一分钟K线[每根K线开始位置[合成了几根K线 - 1], 0]
    # K线列表[合成了几根K线 - 1, 1] = np.max(一分钟K线[每根K线开始位置[合成了几根K线-1]:每根K线结束位置[合成了几根K线-1]+1, 1])
    # K线列表[合成了几根K线 - 1, 2] = np.min(一分钟K线[每根K线开始位置[合成了几根K线-1]:每根K线结束位置[合成了几根K线-1]+1, 2])
    # K线列表[合成了几根K线 - 1, 3] = 一分钟K线[每根K线结束位置[合成了几根K线-1], 3]
    # K线列表[合成了几根K线 - 1, 4] = np.sum(一分钟K线[每根K线开始位置[合成了几根K线-1]:每根K线结束位置[合成了几根K线-1]+1, 4])
    # K线列表[合成了几根K线 - 1, 5] = 一分钟K线[每根K线结束位置[合成了几根K线-1], 5]
    # K线列表[合成了几根K线 - 1, 6] = 一分钟K线[每根K线结束位置[合成了几根K线-1], 6]
    #
    # K线列表 = K线列表[K线列表[:,0] != 0]

    return K线列表, 每根K线开始标记

def _Kline_list(一分钟K线, K线级别, 小时列表, 是否跨日截断=True):  # 改为numpy生成并用numba加速

    n = 0  # 用于合成K线时的数量控制
    长度 = len(小时列表)
    每根K线开始位置 = [0] * 长度
    每根K线结束位置 = [0] * 长度
    合成了几根K线 = 0
    当前K线起点 = 0

    for i in range(长度):
        if 一分钟K线[i][5] != 0:
            n += 1
            每根K线结束位置[合成了几根K线] = i
            if n == 1:
                当前K线起点 = i
        # print(f"n值{n}")

        # 判断新K线是否属于新的交易日
        # 假设一个交易日的结束时间不晚于18点，即18点之前结束当前交易日
        # 那么，可将18点定义为0、19点定义为1、……、21点定义为3、……、9点定义为15、……、14点定义为20、15点定义为21、……
        # 两根相邻的1分钟K线，如果跨交易日，必然：后一K线的时小于前一K线的时。
        if n != 0:
            if n % K线级别 == 0:  # 添加一行，合成新的K线
                每根K线开始位置[合成了几根K线] = 当前K线起点
                合成了几根K线 += 1
                n = 0

            elif 是否跨日截断 and i < 长度 - 1:
                if (小时列表[i] + 6) % 24 > (小时列表[i + 1] + 6) % 24:
                    每根K线开始位置[合成了几根K线] = 当前K线起点
                    合成了几根K线 += 1
                    n = 0

    # 处理最后一根可能没有走完的K线
    if n != 0:  # 即在最后一段时间里出现了成交量不为零的一分钟K线
        每根K线开始位置[合成了几根K线] = 当前K线起点
        合成了几根K线 += 1

    开始位置列表 = 每根K线开始位置[:合成了几根K线]
    结束位置列表 = 每根K线结束位置[:合成了几根K线]

    K线列表 = [[一分钟K线[开始][0], 一分钟K线[开始][1], max([一分钟K线[k][2] for k in range(开始, 结束 + 1)]),
             min([一分钟K线[k][3] for k in range(开始, 结束 + 1)]), 一分钟K线[结束][4],
             sum([一分钟K线[k][5] for k in range(开始, 结束 + 1)]), 一分钟K线[开始][6], 一分钟K线[结束][7], ] for 开始, 结束 in
            zip(开始位置列表, 结束位置列表)]

    # K线列表 = np.zeros((合成了几根K线, 7))
    #
    # for k in range(合成了几根K线):
    #     K线列表[k, 0] = 一分钟K线[每根K线开始位置[k], 0]
    #     K线列表[k, 1] = np.max(一分钟K线[每根K线开始位置[k]:每根K线结束位置[k] + 1, 0:4])
    #     K线列表[k, 2] = np.min(一分钟K线[每根K线开始位置[k]:每根K线结束位置[k] + 1, 0:4])
    #     K线列表[k, 3] = 一分钟K线[每根K线结束位置[k], 3]
    #     K线列表[k, 4] = np.sum(一分钟K线[每根K线开始位置[k]:每根K线结束位置[k] + 1, 4])
    #     K线列表[k, 5] = 一分钟K线[每根K线开始位置[k], 5]
    #     K线列表[k, 6] = 一分钟K线[每根K线结束位置[k], 6]

    # # 第 合成了几根K线 根K线的数据
    # 每根K线开始标记[每根K线开始位置[合成了几根K线 - 1]] = 1
    # K线列表[合成了几根K线 - 1, 0] = 一分钟K线[每根K线开始位置[合成了几根K线 - 1], 0]
    # K线列表[合成了几根K线 - 1, 1] = np.max(一分钟K线[每根K线开始位置[合成了几根K线-1]:每根K线结束位置[合成了几根K线-1]+1, 1])
    # K线列表[合成了几根K线 - 1, 2] = np.min(一分钟K线[每根K线开始位置[合成了几根K线-1]:每根K线结束位置[合成了几根K线-1]+1, 2])
    # K线列表[合成了几根K线 - 1, 3] = 一分钟K线[每根K线结束位置[合成了几根K线-1], 3]
    # K线列表[合成了几根K线 - 1, 4] = np.sum(一分钟K线[每根K线开始位置[合成了几根K线-1]:每根K线结束位置[合成了几根K线-1]+1, 4])
    # K线列表[合成了几根K线 - 1, 5] = 一分钟K线[每根K线结束位置[合成了几根K线-1], 5]
    # K线列表[合成了几根K线 - 1, 6] = 一分钟K线[每根K线结束位置[合成了几根K线-1], 6]
    #
    # K线列表 = K线列表[K线列表[:,0] != 0]

    return K线列表

@jit()
def _ATR_numba(K线, ATR参数):
    ATR = np.zeros(K线.shape[0])
    ATR[:ATR参数] = np.nan
    for i in range(ATR参数, K线.shape[0]):
        ATR计算 = 0
        for k in range(i - ATR参数 + 1, i + 1):
            TR = max(K线[k, 1], K线[k - 1, 3]) - min(K线[k, 2], K线[k - 1, 3])
            ATR计算 += TR / ATR参数
        ATR[i] = ATR计算
    return ATR

@jit()
def _tick_numba(K线, K线级别, 一分钟K线, 全部近似tick):
    一分钟K线位置标记 = 0
    for i in range(K线.shape[0]):
        近似tick = np.zeros(K线级别 * 4, dtype=np.float64)
        index = 0
        for k in range(一分钟K线位置标记, 一分钟K线.shape[0]):
            if 一分钟K线[k, 5] != 0:
                # print(k)
                if i < K线.shape[0] - 1:

                    if K线[i + 1, 0] <= 一分钟K线[k, 0] or index == K线级别 * 4:
                        一分钟K线位置标记 = k
                        break
                    # print(k, index, K线[i + 1, 0], 一分钟K线[k, 0])
                    # if K线[i + 1, 0] <= 一分钟K线[k, 0]:
                    #     一分钟K线位置标记 = k
                    #     break
                    elif K线[i, 0] <= 一分钟K线[k, 0]:
                        if 一分钟K线[k, 1] < 一分钟K线[k, 4]:
                            近似tick[index] = 一分钟K线[k, 1]
                            index += 1
                            近似tick[index] = 一分钟K线[k, 3]
                            index += 1
                            近似tick[index] = 一分钟K线[k, 2]
                            index += 1
                            近似tick[index] = 一分钟K线[k, 4]
                            index += 1
                        else:
                            近似tick[index] = 一分钟K线[k, 1]
                            index += 1
                            近似tick[index] = 一分钟K线[k, 2]
                            index += 1
                            近似tick[index] = 一分钟K线[k, 3]
                            index += 1
                            近似tick[index] = 一分钟K线[k, 4]
                            index += 1
                elif i == K线.shape[0] - 1 and not index == K线级别 * 4:
                    if 一分钟K线[k, 1] < 一分钟K线[k, 4]:
                        近似tick[index] = 一分钟K线[k, 1]
                        index += 1
                        近似tick[index] = 一分钟K线[k, 3]
                        index += 1
                        近似tick[index] = 一分钟K线[k, 2]
                        index += 1
                        近似tick[index] = 一分钟K线[k, 4]
                        index += 1
                    else:
                        近似tick[index] = 一分钟K线[k, 1]
                        index += 1
                        近似tick[index] = 一分钟K线[k, 2]
                        index += 1
                        近似tick[index] = 一分钟K线[k, 3]
                        index += 1
                        近似tick[index] = 一分钟K线[k, 4]
                        index += 1
        近似tick[近似tick == 0.0] = 近似tick[index - 1]
        全部近似tick[i, :] = 近似tick
    return 全部近似tick

@jit()
def _最大回撤_numba(动态权益, 最大回撤类型, 开始节点):
    长度 = 动态权益.shape[0]
    最大回撤区间 = np.zeros(长度)

    最高点 = 动态权益[0]
    最高点后最低点 = 动态权益[0]
    回撤标记1 = 0
    回撤标记2 = 0
    最高点标记 = 开始节点
    最大资金回撤 = 0
    for i in range(开始节点, 长度):
        if 动态权益[i] > 最高点:
            最高点 = 动态权益[i]
            最高点后最低点 = 最高点
            最高点标记 = i
        if 最高点后最低点 > 动态权益[i]:
            最高点后最低点 = 动态权益[i]

        if 最大回撤类型 == 0:
            if (最高点后最低点 - 最高点) / 最高点 < 最大资金回撤:
                最大资金回撤 = (最高点后最低点 - 最高点) / 最高点
                回撤标记1 = 最高点标记
                回撤标记2 = i
        elif 最大回撤类型 == 1:
            if 最高点后最低点 - 最高点 < 最大资金回撤:
                最大资金回撤 = 最高点后最低点 - 最高点
                回撤标记1 = 最高点标记
                回撤标记2 = i

    最大回撤区间[回撤标记1] = 动态权益[回撤标记1]
    最大回撤区间[回撤标记2] = 动态权益[回撤标记2]

    return 最大资金回撤, 最大回撤区间

@jit()
def _最长回撤_numba(动态权益, 开始节点):
    长度 = 动态权益.shape[0]
    最长回撤区间 = np.zeros(长度)

    最长回撤时间 = 0
    最长回撤起点 = 0
    最长回撤终点 = 0
    最高点 = 动态权益[0]
    最高点后最低点 = 动态权益[0]
    最高点标记 = 开始节点
    for i in range(开始节点, 长度):
        if 动态权益[i] >= 最高点:
            最高点 = 动态权益[i]
            最高点后最低点 = 最高点
            最高点标记 = i
        if 最高点后最低点 > 动态权益[i]:
            最高点后最低点 = 动态权益[i]

        if i - 最高点标记 > 最长回撤时间:
            最长回撤时间 = i - 最高点标记
            最长回撤起点 = 最高点标记
            最长回撤终点 = i

    最长回撤区间[最长回撤起点] = 动态权益[最长回撤起点]
    最长回撤区间[最长回撤终点] = 动态权益[最长回撤终点]

    return 最长回撤起点, 最长回撤终点, 最长回撤区间

@jit()
def _最大增长_numba(动态权益, 最大增长类型, 开始节点):
    长度 = 动态权益.shape[0]
    最大增长区间 = np.zeros(长度)

    最低点 = 动态权益[0]
    最低点后最高点 = 动态权益[0]
    增长标记1 = 0
    增长标记2 = 0
    最低点标记 = 开始节点
    最大资金增长 = 0
    for i in range(开始节点, 长度):
        if 动态权益[i] < 最低点:
            最低点 = 动态权益[i]
            最低点后最高点 = 最低点
            最低点标记 = i
        if 最低点后最高点 < 动态权益[i]:
            最低点后最高点 = 动态权益[i]

        if 最大增长类型 == 0:
            if (最低点后最高点 - 最低点) / 最低点 > 最大资金增长:
                最大资金增长 = (最低点后最高点 - 最低点) / 最低点
                增长标记1 = 最低点标记
                增长标记2 = i
        elif 最大增长类型 == 1:
            if 最低点后最高点 - 最低点 > 最大资金增长:
                最大资金增长 = 最低点后最高点 - 最低点
                增长标记1 = 最低点标记
                增长标记2 = i

    最大增长区间[增长标记1] = 动态权益[增长标记1]
    最大增长区间[增长标记2] = 动态权益[增长标记2]

    return 最大资金增长, 最大增长区间

@jit()
def _合成数据_numba(叠加数据, 交易数据):
    叠加数据位置标记 = 0
    交易数据位置标记 = 0
    列数 = 叠加数据.shape[1]
    for i in range(叠加数据.shape[0]):
        if 叠加数据[i, 0] == 交易数据[交易数据位置标记, 0]:
            if 交易数据位置标记 == 0:
                叠加数据[i, 1:列数 - 1] = 叠加数据[i, 1:列数 - 1] + 交易数据[交易数据位置标记, 1:]
                叠加数据[i, 列数 - 1] = 1
                交易数据位置标记 += 1
                叠加数据位置标记 = i
            else:
                叠加数据[i, 1:列数 - 1] = 叠加数据[i, 1:列数 - 1] + 交易数据[交易数据位置标记, 1:列数 - 1]
                叠加数据[i, 列数 - 1] = 1
                叠加数据[叠加数据位置标记 + 1:i, 1:列数 - 1] = 叠加数据[叠加数据位置标记 + 1:i, 1:列数 - 1] + 交易数据[交易数据位置标记 - 1, 1:列数 - 1]
                交易数据位置标记 += 1
                叠加数据位置标记 = i
        if 交易数据位置标记 == 交易数据.shape[0]:
            if 叠加数据位置标记 != 叠加数据.shape[0] - 1:
                叠加数据[叠加数据位置标记 + 1:, 1:列数 - 1] = 叠加数据[叠加数据位置标记 + 1:, 1:列数 - 1] + 交易数据[交易数据位置标记 - 1, 1:列数 - 1]
            break

    return 叠加数据

@jit()
def _生成增长率(动态权益, 时段, 类型):
    分几段 = math.floor(时段 / 30)
    间隔 = math.floor(动态权益.shape[0] / 分几段)
    增长率 = np.zeros(分几段)
    if 类型 == 1:
        for i in range(分几段 - 1):
            增长率[i] = math.log(动态权益[(i + 1) * 间隔 - 1] / 动态权益[i * 间隔])
            增长率[分几段 - 1] = math.log(动态权益[-1] / 动态权益[(分几段 - 1) * 间隔])
    elif 类型 == 2:
        for i in range(分几段 - 1):
            增长率[i] = 动态权益[(i + 1) * 间隔 - 1] - 动态权益[i * 间隔]
            增长率[分几段 - 1] = 动态权益[-1] - 动态权益[(分几段 - 1) * 间隔]

    return 增长率


# *-*-*-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-技术指标计算函数-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-

def 获取一分钟K线(一分钟K线数据文件, 开始日期, 结束日期, 时间格式='datetime64', 输出格式='array'):
    """
    获取一分钟K线: 读取并生成所选期货品种在开始日期与结束日期之间的一分钟K线数据
    Args:
        一分钟K线数据文件 (str): 传入要读取的数据文件的路径，读取的数据文件的格式为csv格式
        开始日期 (datetime): K线开始时间
        结束日期(datetime): K线结束时间(输出的K线中不包含结束时间)
        时间格式(str): 输出的一分钟K线数据中时间的格式，可选格式为：'datetime64':numpy.datetime64、'datetime':pandas.datetime
        输出格式 (str): 输出为什么数据类型，可选参数有'list'、'dataframe'、'array'
    Returns:
        K线：T/O/H/L/C/V/c0/c1, 小时时间[array]：用于合成K线

    """
    一分钟K线 = pd.read_csv(一分钟K线数据文件, encoding='gb2312').values
    一分钟K线[:, 0] = pd.to_datetime(一分钟K线[:, 0])
    一分钟K线 = 一分钟K线[一分钟K线[:, 0] >= 开始日期]
    一分钟K线 = 一分钟K线[一分钟K线[:, 0] < 结束日期]

    小时时间 = np.array([item.hour for item in 一分钟K线[:, 0]])

    if 输出格式 == 'array':
        if 时间格式 == 'datetime64':
            一分钟K线[:, 0] = [item.to_datetime64() for item in 一分钟K线[:, 0]]
            return 一分钟K线, 小时时间
        elif 时间格式 == 'datetime':
            return 一分钟K线, 小时时间

    elif 输出格式 == 'list':
        if 时间格式 == 'datetime64':
            一分钟K线[:, 0] = [item.to_datetime64() for item in 一分钟K线[:, 0]]
            return 一分钟K线.tolist(), 小时时间
        elif 时间格式 == 'datetime':
            return 一分钟K线.tolist(), 小时时间

    elif 输出格式 == 'dataframe':
        if 时间格式 == 'datetime64':
            一分钟K线[:, 0] = [item.to_datetime64() for item in 一分钟K线[:, 0]]
            return pd.DataFrame(一分钟K线, columns=['T', 'O', 'H', 'L', 'C', 'V', 'c0', 'c1']), 小时时间
        if 时间格式 == 'datetime':
            return pd.DataFrame(一分钟K线, columns=['T', 'O', 'H', 'L', 'C', 'V', 'c0', 'c1']), 小时时间
    else:
        return 一分钟K线, 小时时间

# 获取一分钟K线和Kline函数配合使用，主要用于循环中生成K线，在循环外使用《获取一分钟K线》，得到一分钟K线和小时时间，在循环内使用《Kline》合成K线，
# 在numba加速下可极大的提升循环内合成K线的效率, 输出的K线中的时间格式与输入的一分钟K线中的时间格式相同
def Kline(一分钟K线, 小时时间, 合成几分钟K线, 是否跨日截断=True, 输出格式='array'):
    """
    K线: 利用一分钟级别K线生成所需K线级别的K线，输出的日期格式与输入的日期格式相同
    注意：
        1. 过滤了一分钟K线中成交量为0的部分，目前合成方式为数够K线级别根K线或跨日时进行截断
    Args:
        一分钟K线 (): 需要计算均线的价格列表，可接收的类型为list,numpy.ndarray,pandas.DataFrame
        小时时间 (np.ndarray): 一分钟K线时间列对应的时钟
        合成几分钟K线 (int): K线级别
        是否跨日截断(bool): 赋值为True是进行截断
        输出格式 (str): 输出为什么数据类型，可选参数有'list'、'dataframe'、'array'
    Returns:
        list: K线：T/O/H/L/C/V/c0/c1(其中T为与一分钟K线的时间格式相同)
    """
    if not isinstance(一分钟K线, np.ndarray):
        if isinstance(一分钟K线, list):
            一分钟K线 = np.array(一分钟K线)
        elif isinstance(一分钟K线, pd.DataFrame):
            一分钟K线 = np.array(一分钟K线)

    一分钟K线数据 = np.array(一分钟K线[:, 1:], dtype=np.float64)
    K线数据, 时间标记 = _Kline_numba(一分钟K线数据, 合成几分钟K线, 小时时间, 是否跨日截断)
    K线 = 一分钟K线[时间标记 == 1.]
    K线[:, 1:] = K线数据

    if 输出格式 == 'array':
        return K线
    elif 输出格式 == 'list':
        return K线.tolist()
    elif 输出格式 == 'dataframe':
        return pd.DataFrame(K线, columns=['T', 'O', 'H', 'L', 'C', 'V', 'c0', 'c1'])
    else:
        return K线

# Kline2采用list合成K线，主要用于单次生成K线，防止因numba编译消耗额外时间
def Kline2(一分钟K线数据文件, 开始日期, 结束日期, 合成几分钟K线, 是否跨日截断=True, 时间格式='datetime64', 输出格式='list'):
    """
    获取一分钟K线: 读取并生成所选期货品种在开始日期与结束日期之间的一分钟K线数据
    注意：
        1. 过滤了一分钟K线中成交量为0的部分，目前合成方式为数够K线级别根K线或跨日时进行截断
    Args:
        一分钟K线数据文件 (str): 传入要读取的数据文件的路径，读取的数据文件的格式为csv格式
        开始日期 (datetime): K线开始时间
        结束日期(datetime): K线结束时间(输出的K线中不包含结束时间)
        合成几分钟K线(int): K线级别
        是否跨日截断(bool): 跨日时是否对未走完的K线进行截断
        时间格式(str): 输出的一分钟K线数据中时间的格式，可选格式为：'datetime64':numpy.datetime64、'datetime':pandas.datetime
        输出格式 (str): 输出为什么数据类型，可选参数有'list'、'dataframe'、'array'
    Returns:
        K线：T/O/H/L/C/V/c0/c1

    """
    一分钟K线 = pd.read_csv(一分钟K线数据文件).values
    一分钟K线[:, 0] = pd.to_datetime(一分钟K线[:, 0])
    一分钟K线 = 一分钟K线[一分钟K线[:, 0] >= 开始日期]
    一分钟K线 = 一分钟K线[一分钟K线[:, 0] < 结束日期]

    小时时间 = [item.hour for item in 一分钟K线[:, 0].tolist()]

    if 时间格式 == 'datetime':
        pass
    elif 时间格式 == 'datetime64':
        一分钟K线[:, 0] = [item.to_datetime64() for item in 一分钟K线[:, 0]]

    K线 = _Kline_list(一分钟K线.tolist(), 合成几分钟K线, 小时时间, 是否跨日截断)

    if 输出格式 == 'array':
        return np.array(K线)
    elif 输出格式 == 'list':
        return K线
    elif 输出格式 == 'dataframe':
        return pd.DataFrame(K线, columns=['T', 'O', 'H', 'L', 'C', 'V', 'c0', 'c1'])
    else:
        return K线

def 一分钟K线近似tick数据(K线, K线级别, 一分钟K线, 输出格式='array'):
    """
    一分钟K线近似tick数据: 用一分钟级别K线近似生成tick数据
        计算公式:
        如一分钟K线为阳线，则以O-L-H-C生成近似tick数据，若为阴线，则以O-H-L-C生成近似tick数据
        注意:
        1. 每根一分钟K线生成四个tick数据，认为每个收盘价与下个开盘价之下没有连续的价格
        2. 若当前K线对应的一分钟K线为n根（n小于K线级别），则该K线对应的一分钟K线近似tick数据的前4*n正常生成，之后的4*（K线级别-n）个数据用第n个一分钟K线的收盘价填充
    Args:
        K线 (): 一定级别K线的数据，可接收的类型为list,numpy.ndarray,pandas.Series
        K线级别 (int): 传入的K线对应的K线级别
        一分钟K线 (): 一分钟级别K线的数据，可接收的类型为list,numpy.ndarray,pandas.Series
        输出格式(str): 输出为什么数据类型，可选参数有'list'、'series'、'array'、'tuple'
    Returns:
        list: 近似tick数据，第一行为第一根K线对应的tick数据，第二行为第二根K线对应的tick数据，以此类推...
    """
    if not isinstance(一分钟K线, np.ndarray):
        if isinstance(一分钟K线, list):
            一分钟K线 = np.array(一分钟K线, dtype=np.float64)
        elif isinstance(一分钟K线, pd.DataFrame):
            一分钟K线 = np.array(一分钟K线, dtype=np.float64)
    elif 一分钟K线.dtype != 'float64':
        一分钟K线 = np.array(一分钟K线, dtype=np.float64)

    if not isinstance(K线, np.ndarray):
        if isinstance(K线, list):
            K线 = np.array(K线, dtype=np.float64)
        elif isinstance(K线, pd.DataFrame):
            K线 = np.array(K线, dtype=np.float64)
    elif K线.dtype != 'float64':
        K线 = np.array(K线, dtype=np.float64)

    全部近似tick = np.zeros((K线.shape[0], K线级别 * 4))
    近似tick = _tick_numba(K线, K线级别, 一分钟K线, 全部近似tick)

    if 输出格式 == 'array':
        return 近似tick
    elif 输出格式 == 'list':
        return 近似tick.tolist()
    elif 输出格式 == 'dataframe':
        return pd.DataFrame(近似tick)
    else:
        return 近似tick

def MA(价格, 均线级别, 输出格式='list'):
    """
    简单移动平均线: 求价格在均线级别周期上的简单移动平均
        计算公式:
        MA(x, 5) = (x(1) + x(2) + x(3) + x(4) + x(5)) / 5
        注意:
        1. 简单移动平均线将设定周期内的值取平均值, 其中各元素的权重都相等
        2. 均线级别为0的情况下, 或当均线级别为有效值但当前的价格列表元素个数不足均线级别个, 函数返回 np.nan 列表
        3. 返回内容中的前(均线级别-1)个元素用np.nan填充
    Args:
        价格 (): 需要计算均线的价格列表，可接收的类型为list,numpy.ndarray,pandas.Series
        均线级别 (int): 周期
        输出格式(str): 输出为什么数据类型，可选参数有'list'、'series'、'array'、'tuple'
    Returns:
        list: 简单移动平均值序列
    """
    if not isinstance(价格, pd.Series):
        价格 = pd.Series(价格)

    MA = 价格.rolling(均线级别).mean()

    if 输出格式 == 'list':
        return MA.tolist()
    elif 输出格式 == 'series':
        return MA
    elif 输出格式 == 'array':
        return MA.values
    elif 输出格式 == 'tuple':
        return tuple(MA.tolist())
    else:
        return MA

def EMA(价格, 均线级别, 输出格式='list'):
    """
    指数加权移动平均线: 求价格在均线级别周期上的指数加权移动平均
        计算公式:
        EMA(x, n) = 2 * x / (n + 1) + (n - 1) * ema(x, n).shift(1) / (n + 1)
        注意:
        1. 均线级别需大于等于1
        2. 对距离当前较近的价格赋予了较大的权重
        3. 返回内容中的前(均线级别-1)个元素用np.nan填充
    Args:
        价格 (): 需要计算均线的价格列表，可接收的类型为list,numpy.ndarray,pandas.Series
        均线级别 (int): 周期
        输出格式(str): 输出为什么数据类型，可选参数有'list'、'series'、'array'、'tuple'
    Returns:
        list: 简单移动平均值序列
    """
    if not isinstance(价格, pd.Series):
        价格 = pd.Series(价格)

    EMA = 价格.ewm(span=均线级别, adjust=False).mean()

    if 输出格式 == 'list':
        return EMA.tolist()
    elif 输出格式 == 'series':
        return EMA
    elif 输出格式 == 'array':
        return EMA.values
    elif 输出格式 == 'tuple':
        return tuple(EMA.tolist())
    else:
        return EMA

def ATR(K线, ATR参数, 输出格式='list'):
    """
    均幅指标: 计算每根K线收盘后对应的在ATR参数下的均幅指标
        计算公式:
        TR_i = max(H_i,C_i-1)-min(L_i,C_i-1) TR_i为第i根K线对应的TR指标
        ATR_i = average(TR_i + TR_i-1 +...+ TR_i-ATR参数+1) ATR_i为第i根K线对应的ATR指标，是自第i根K线起向前共ATR参数根K线的TR的均值
        注意:
        1. ATR参数需大于等于1
        2. 对距离当前较近的价格赋予了较大的权重
        3. 返回内容中的前(ATR参数-1)个元素用np.nan填充
    Args:
        K线 (): 需要计算ATR的K线列表，可接收的类型为list,numpy.ndarray,pandas.DataFrame，列表结构为：T/O/H/L/C/...
        ATR参数 (int): 周期
        输出格式(str): 输出为什么数据类型，可选参数有'list'、'series'、'array'、'tuple'
    Returns:
        list: 简单移动平均值序列
    """

    if not isinstance(K线, np.ndarray):
        if isinstance(K线, pd.DataFrame):
            K线 = np.array(K线.values[:, 1:], dtype=np.float64)
        elif isinstance(K线, list):
            K线 = [item[1:] for item in K线]
            K线 = np.array(K线, dtype=np.float64)
    elif K线.dtype != 'float64':
        K线 = np.array(list(K线[:, 1:]), dtype='float64')

    ATR = _ATR_numba(K线, ATR参数)

    if 输出格式 == 'list':
        return ATR.tolist()
    elif 输出格式 == 'series':
        return pd.Series(ATR)
    elif 输出格式 == 'array':
        return ATR
    elif 输出格式 == 'tuple':
        return tuple(ATR.tolist())
    else:
        return ATR

def KD():
    pass

def MACD():
    pass

def 唐奇安通道():
    pass


# *-*-*-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-策略评价指标计算函数-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-

def 寻找最大回撤区间并生成标记(动态权益, 最大回撤类型='比例', 开始节点=0, 输出格式='list'):
    """
    寻找最大回撤区间并生成标记: 寻找动态权益序列的最大回撤，以及最大回撤区间对应的起点和终点在动态权益序列中的相对位置
        计算公式:
        最大回撤（比例） = （当前最高点后的最低点-当前最高点）/当前最高点
        最大回撤（金额） = 当前最高点后的最低点-当前最高点
    Args:
        动态权益 (): 需要寻找最大回撤的动态权益序列，可接收的类型为list,numpy.ndarray,pandas.Series
        最大回撤类型 (str): 返回的最大回撤的类型，可选参数为：'比例'、'金额'
        开始节点 (int): 从第几根K线开始寻找最大回撤
        输出格式(str): 将最大回撤区间对应的起点和终点在动态权益序列中的相对位置输出为什么数据类型，可选参数有'list'、'series'、'array'、'tuple'
    Returns:
        Any: 最大回撤， 最大回撤区间起点终点：[0,0,..,0,price1,0,...,0,0,price2,0,...],其中price1和price2分别为起点和终点对应位置的K线的开盘价
    """
    if not isinstance(动态权益, np.ndarray):
        if isinstance(动态权益, list):
            动态权益 = np.array(动态权益, dtype=np.float64)
        elif isinstance(动态权益, pd.Series):
            动态权益 = 动态权益.values

    if 最大回撤类型 == '比例':
        回撤类型 = 0
    elif 最大回撤类型 == '金额':
        回撤类型 = 1

    最大回撤, 最大回撤区间 = _最大回撤_numba(动态权益, 回撤类型, 开始节点)

    if 输出格式 == 'list':
        return 最大回撤, 最大回撤区间.tolist()
    elif 输出格式 == 'series':
        return 最大回撤, pd.Series(最大回撤区间)
    elif 输出格式 == 'array':
        return 最大回撤, 最大回撤区间
    elif 输出格式 == 'tuple':
        return 最大回撤, 最大回撤区间.tolist()
    else:
        return 最大回撤, 最大回撤区间.tolist()

def 寻找最长回撤区间并生成标记(时间列表, 动态权益, 开始节点=0, 输出格式='list'):
    """
    寻找最大回撤区间并生成标记: 寻找动态权益序列的最大回撤，以及最大回撤区间对应的起点和终点在动态权益序列中的相对位置
        计算公式:
        最长回撤时间 = 当前最高点后的时间-当前最高点的时间
    Args:
        时间列表 (): 时间需传入pandas.datetime格式的，可接收的类型为list,numpy.ndarray,pandas.Series
        动态权益 (): 传入时间对应的动态权益序列，可接收的类型为list,numpy.ndarray,pandas.Series
        开始节点 (int): 从第几根K线开始寻找最长回撤
        输出格式(str): 将最长回撤区间对应的起点和终点在动态权益序列中的相对位置输出为什么数据类型，可选参数有'list'、'series'、'array'、'tuple'
    Returns:
        Any: 最长回撤， 最长回撤区间起点终点：[0,0,..,0,price1,0,...,0,0,price2,0,...],其中price1和price2分别为起点和终点对应位置的K线的开盘价
    """
    if not isinstance(动态权益, np.ndarray):
        if isinstance(动态权益, list):
            动态权益 = np.array(动态权益, dtype=np.float64)
        elif isinstance(动态权益, pd.Series):
            动态权益 = 动态权益.values

    最长回撤起点, 最长回撤终点, 最长回撤区间 = _最长回撤_numba(动态权益, 开始节点)
    最长回撤 = (时间列表[最长回撤终点] - 时间列表[最长回撤起点]).days

    if 输出格式 == 'list':
        return 最长回撤, 最长回撤区间.tolist()
    elif 输出格式 == 'series':
        return 最长回撤, pd.Series(最长回撤区间)
    elif 输出格式 == 'array':
        return 最长回撤, 最长回撤区间
    elif 输出格式 == 'tuple':
        return 最长回撤, 最长回撤区间.tolist()
    else:
        return 最长回撤, 最长回撤区间.tolist()

def 寻找最大资金增长并生成标记(动态权益, 最大增长类型='比例', 开始节点=0, 输出格式='list'):
    """
    寻找最大资金增长并生成标记: 寻找动态权益序列的最大增长，以及最大增长区间对应的起点和终点在动态权益序列中的相对位置
        计算公式:
        最大增长（比例） = （当前最低点后的最高点-当前最低点）/当前最低点
        最大增长（金额） = 当前最低点后的最高点-当前最低点
    Args:
        动态权益 (): 需要寻找最大增长的动态权益序列，可接收的类型为list,numpy.ndarray,pandas.Series
        最大增长类型 (str): 返回的最大增长的类型，可选参数为：'比例'、'金额'
        开始节点 (int): 从第几根K线开始寻找最大增长
        输出格式(str): 将最大增长区间对应的起点和终点在动态权益序列中的相对位置输出为什么数据类型，可选参数有'list'、'series'、'array'、'tuple'
    Returns:
        Any: 最大增长， 最大增长区间起点终点：[0,0,..,0,price1,0,...,0,0,price2,0,...],其中price1和price2分别为起点和终点对应位置的K线的开盘价
    """
    if not isinstance(动态权益, np.ndarray):
        if isinstance(动态权益, list):
            动态权益 = np.array(动态权益, dtype=np.float64)
        elif isinstance(动态权益, pd.Series):
            动态权益 = 动态权益.values

    if 最大增长类型 == '比例':
        增长类型 = 0
    elif 最大增长类型 == '金额':
        增长类型 = 1

    最大增长, 最大增长区间 = _最大增长_numba(动态权益, 增长类型, 开始节点)

    if 输出格式 == 'list':
        return 最大增长, 最大增长区间.tolist()
    elif 输出格式 == 'series':
        return 最大增长, pd.Series(最大增长区间)
    elif 输出格式 == 'array':
        return 最大增长, 最大增长区间
    elif 输出格式 == 'tuple':
        return 最大增长, 最大增长区间.tolist()
    else:
        return 最大增长, 最大增长区间.tolist()

def 统计盈亏天数(时间列表, 动态权益, 开始节点=0):
    """
    寻找最大回撤区间并生成标记: 寻找动态权益序列的最大回撤，以及最大回撤区间对应的起点和终点在动态权益序列中的相对位置
        计算公式:
        最长回撤时间 = 当前最高点后的时间-当前最高点的时间
    Args:
        时间列表 (): 时间需传入pandas.datetime格式的，可接收的类型为list,numpy.ndarray,pandas.Series
        动态权益 (): 传入时间对应的动态权益序列，可接收的类型为list,numpy.ndarray,pandas.Series
        开始节点 (int): 从第几根K线开始寻找最长回撤
    Returns:
        int: 盈利天数，亏损天数，空仓天数
    """
    if not isinstance(动态权益, np.ndarray):
        if isinstance(动态权益, list):
            动态权益 = np.array(动态权益, dtype=np.float64)
        elif isinstance(动态权益, pd.Series):
            动态权益 = 动态权益.values

    长度 = len(时间列表)

    盈利天数 = 0
    亏损天数 = 0
    空仓天数 = 0
    初始动态权益 = 动态权益[0]
    初始日 = 时间列表[开始节点].day

    for i in range(开始节点, 长度):
        if 时间列表[i].day != 初始日:
            if 动态权益[i - 1] > 初始动态权益:
                盈利天数 += 1
            elif 动态权益[i - 1] < 初始动态权益:
                亏损天数 += 1
            elif 动态权益[i - 1] == 初始动态权益:
                空仓天数 += 1
            初始日 = 时间列表[i].day
            初始动态权益 = 动态权益[i - 1]
        if i == 长度 - 1:
            if 动态权益[i] > 初始动态权益:
                盈利天数 += 1
            elif 动态权益[i] < 初始动态权益:
                亏损天数 += 1
            elif 动态权益[i] == 初始动态权益:
                空仓天数 += 1

    return 盈利天数, 亏损天数, 空仓天数

def 综合评价指标(动态权益, 交易次数, 时间列表, 开仓方式='固定比例'):
    '''
    用于生成综合评价指标，生成方式为当前最新版本，较早的版本写在注释中
    注意：
        1.年化收益,最大回撤,波动率在固定比例开仓时和固定手数开仓时有不同的计算方式
    Args:
        动态权益(Any): 动态权益序列，可接收类型包括list，numpy.ndarray，pandas.Series
        交易次数(int): 交易次数(单边)
        时间列表(Any): 动态权益对应的时间列表，时间格式为pandas.datetime
        开仓方式(str): 当前策略中使用的开仓方式，可选参数为：'固定比例'，'固定手数'

    Returns:
        指标集合(list): [最终净值,年化收益,最大回撤,年化收益/最大回撤(风险回报),风险回报乘数,交易次数,交易次数乘数,最长回撤时间(天),最长回撤时间乘数,波动率,波动率乘数,评价指标]

    '''
    if not isinstance(动态权益, np.ndarray):
        if isinstance(动态权益, list):
            动态权益 = np.array(动态权益, dtype=np.float64)
        elif isinstance(动态权益, pd.Series):
            动态权益 = 动态权益.values
    时段 = (时间列表[-1] - 时间列表[0]).days

    # 最终净值
    最终净值 = 动态权益[-1] / 动态权益[0]
    # 最长回撤时间
    最长回撤时间, _ = 寻找最长回撤区间并生成标记(时间列表, 动态权益)
    # 最长回撤时间乘数
    最长回撤时间乘数 = math.atan(math.exp((365 / 最长回撤时间) ** 2))
    # 交易次数乘数
    交易次数乘数 = math.atan(math.exp(交易次数 / 时段 * 7 + 1))

    if 开仓方式 == '固定比例':
        # 年化收益
        if min(动态权益) > 0:
            年化收益 = 最终净值 ** (365 / 时段) - 1
        else:
            年化收益 = -1
        # 最大回撤
        最大回撤, _ = 寻找最大回撤区间并生成标记(动态权益, 最大回撤类型='比例')
        # 波动率
        增长率 = _生成增长率(动态权益, 时段, 1)
        均值 = np.mean(增长率)
        标准差 = np.std(增长率)
        波动率 = 标准差 / 均值 * 100
        # 波动率乘数
        波动率乘数 = math.exp(400 / 波动率) if 波动率 > 0 else 1


    elif 开仓方式 == '固定手数':
        # 年化收益
        if min(动态权益) > 0:
            年化收益 = (动态权益[-1] - 动态权益[0]) / 时段 * 365
        else:
            年化收益 = -动态权益[0]
        # 最大回撤
        最大回撤, _ = 寻找最大回撤区间并生成标记(动态权益, 最大回撤类型='金额')
        # 波动率
        增长率 = _生成增长率(动态权益, 时段, 2)
        均值 = np.mean(增长率)
        标准差 = np.std(增长率)
        波动率 = 标准差 / 均值 * 100
        # 波动率乘数
        波动率乘数 = math.exp(400 / 波动率) if 波动率 > 0 else 1

    # 风险回报
    风险回报 = 年化收益 / abs(最大回撤)
    # 风险回报乘数
    if 风险回报 > 2:
        风险回报乘数 = math.atan(math.exp((风险回报 - 1) ** 2))
    else:
        风险回报乘数 = math.atan(math.exp(风险回报 - 1))

    # 评价指标
    评价指标 = 风险回报乘数 * 交易次数乘数 * 最长回撤时间乘数 * 波动率乘数

    指标集 = [最终净值, 年化收益, 最大回撤, 风险回报, 风险回报乘数, 交易次数, 交易次数乘数, 最长回撤时间, 最长回撤时间乘数, 波动率, 波动率乘数, 评价指标]

    return 指标集


# *-*-*-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-功能性函数-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-

def 生成随机字符串(长度=6):
    s = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'  # 共62个字符  # 62的6次方＞568亿
    x = ''
    for i in range(长度):
        x += s[random.randrange(0, len(s))]
    return x

def 引用本地JS(fname='回测结果.html', 指定存储目录='.'):
    '''
    将pyecharts生成的图片转为本地使用echarts.min.json文件打开，并将echarts.min.json与图片放在指定路径下
    :param fname(str):将图片命名为什么，格式为'xxx.html'
    :param 指定存储目录:图片和echarts.min.json的存放路径
    :return:
    '''
    # 一次读取全部内容  # 文件内容较小时采用该方式更方便
    with open(fname, 'r', encoding='UTF-8') as f:
        读取内容 = f.read()
        # print(f'数据类型：{type(读取内容)}内容：{读取内容[0:500]}')
    替换 = 'https://assets.pyecharts.org/assets/'
    替换后的内容 = 读取内容.replace(替换, '')
    # print(f'数据类型：{type(替换后的内容)}内容：{替换后的内容[0:500]}')

    s = 生成随机字符串()
    # 覆盖写入
    with open(f"{指定存储目录}\图{s}.html", 'w', encoding='UTF-8') as f:  # 使用Pyecharts-Tbale时需加入encoding参数
        f.write(替换后的内容)

    print(f"图{s}.html已生成")
    os.remove(fname)

def 生成table(内容字典, 主标题='主要指标', 子标题='', 去边框吗=False):
    '''
    生成table图表：(from pyecharts.components import Table
                  from pyecharts.options import ComponentTitleOpts)
        通过dict传入数据，可选关键字包含【时段(天) ，盈利额 ，亏损额 ，净利润 ，盈利笔数 ，亏损笔数 ，
        期初权益 ，期末权益 ，胜率 ，手续费 ，盈利天数 ，亏损天数 ，空仓天数 ，成交额(单边)/期初权益 ，盈亏比，滑点损失
        做多盈利金额 ，做多盈利笔数 ，做空盈利金额 ，做空盈利比数 ，做多亏损金额 ，做多亏损比数 ，做空亏损金额 ，做空亏损笔数，
        成交手数 ，成交笔数 ，单笔最大盈利额 ，单笔最大亏损额 ，最大资金回撤 ，最大资金增长 ，周均手数 ，周均笔数 ，区间收益率 ，年化收益率】
    :param 主标题【str】 主标题
    :param 子标题【str】 副标题
    :param 内容字典【dict】
    :param 留边框吗【True/False】 去除边框：
    :return:
        pyecharts.table
    '''

    if not isinstance(内容字典, dict):
        raise TypeError("内容字典必须是字典（dict）")
    if not isinstance(主标题, str) or not isinstance(子标题, str):
        raise TypeError("主标题/子标题必须是字符串（str）")

    head = ['', ' ', '  ', '   ', '    ']  # table不允许head中存在重复元素
    row = [['时段(天)', '-', '丨', '期初权益', '-'],
           ['盈利额', '-', '丨', '亏损额', '-'],
           ['净利润', '-', '丨', '胜率', '-'],
           ['盈利笔数', '-', '丨', '亏损笔数', '-'],
           ['手续费', '-', '丨', '期末权益', '-'],
           ['盈亏比', '-', '丨', '滑点损失', '-'],
           ['\n', '\n', '\n', '\n', '\n'],
           ['\n', '\n', '\n', '\n', '\n'],
           ['盈利天数', '-', '丨', '亏损天数', '-'],
           ['空仓天数', '-', '丨', '成交额(单边)/期初权益', '-'],
           ['做多盈利金额', '-', '丨', '做空盈利金额', '-'],
           ['做多亏损金额', '-', '丨', '做空亏损金额', '-'],
           ['做多盈利笔数', '-', '丨', '做空盈利笔数', '-'],
           ['做多亏损笔数', '-', '丨', '做空亏损笔数', '-'],
           ['成交手数', '-', '丨', '成交笔数', '-'],
           ['单笔最大盈利额', '-', '丨', '单笔最大亏损额', '-'],
           ['最大资金回撤', '-', '丨', '最大资金增长', '-'],
           ['周均手数', '-', '丨', '周均笔数', '-'],
           ['区间收益率', '-', '丨', '年化收益率', '-']]

    for key in 内容字典.keys():  # 读取字典，将值赋给row中对位置
        for i, item in enumerate(row):
            for j, word in enumerate(item):
                if key == word:
                    if isinstance(内容字典[key], float):
                        row[i][j + 1] = f'{round(内容字典[key], 2)}'
                    else:
                        row[i][j + 1] = f'{内容字典[key]}'

    if 去边框吗:
        table = Table()
        table.add(head, row, {'key': 'value'}).set_global_opts(
            title_opts=ComponentTitleOpts(title=主标题, subtitle=子标题))
        return table
    table = Table()
    table.add(head, row).set_global_opts(title_opts=ComponentTitleOpts(title=主标题, subtitle=子标题))
    return table

def 选择文件(选择文件夹=False):
    '''
    选择文件并返回文件的路径
    Returns:
        文件(str): 所选文件路径
    '''
    窗口 = Tk()
    窗口.wm_attributes('-topmost', 1)
    窗口.withdraw()  # tkinter 隐藏主窗口,只显示对话框
    if not 选择文件夹:
        print('请选择文件')
        文件 = tkinter.filedialog.askopenfilename(title='请选择文件', filetypes=[
            ('CSV', '*.csv')])  # 对话框标题，可选文件类型，如filetypes=[('EXE', '*.exe'), ('All Files', '*')]
    elif 选择文件夹:
        print('请选择文件夹')
        文件 = tkinter.filedialog.askdirectory(title='请选择文件夹')
    print(f'选择的文件夹为：{文件}')
    窗口.destroy()
    return 文件

def 寻找某类文件(文件类型=[], 搜索几级子文件夹=0, 搜索路径=''):
    '''
    在指定文件夹下寻找某一类型的文件
    Args:
        搜索几级子文件夹(int): 在当前指定文件夹下向下搜索几级子文件夹
        搜索路径(str): 需要进行搜索的文件夹的路径，若不传入或传入路径不存在，则会弹出弹框手动选择
        文件类型(list): 寻找的文件的类型，若不选择，则返回所有类型的文件，若要搜索文件夹，请传入:'文件夹'，其他类型请填入小写的文件后缀，
                       示例：['文件夹','csv','txt']

    Returns:
        文件(list): 所有当前文件加下的所选类型的文件路径
    '''
    if not os.path.exists(搜索路径):
        搜索路径 = 选择文件(选择文件夹=True)

    if not isinstance(搜索几级子文件夹, int):
        raise TypeError("搜索几级子文件夹必须是整数（int）")

    文件 = []
    文件夹 = [搜索路径]
    子文件夹 = []
    搜索到的文件 = []
    for _ in range(搜索几级子文件夹 + 1):
        for 文件夹路径 in 文件夹:
            所有文件 = os.listdir(文件夹路径)
            所有文件路径 = [os.path.join(文件夹路径, 文件名) for 文件名 in 所有文件]
            for 文件路径 in 所有文件路径:
                if '文件夹' not in 文件类型 and 文件类型 != []:
                    if os.path.isdir(文件路径):
                        子文件夹.append(文件路径)
                    else:
                        搜索到的文件.append(文件路径)
                else:
                    搜索到的文件.append(文件路径)
                    if os.path.isdir(文件路径):
                        子文件夹.append(文件路径)
        文件夹 = 子文件夹.copy()
        子文件夹 = []

    单类型文件 = []
    if 文件类型 == []:
        pass
    else:
        for 类型 in 文件类型:
            if 类型 == '文件夹':
                for item in 搜索到的文件:
                    if os.path.isdir(item):
                        单类型文件.append(item)
            else:
                for item in 搜索到的文件:
                    if item.endswith('.' + 类型):
                        单类型文件.append(item)
            文件.append(单类型文件)
            单类型文件 = []

    if 文件类型 == []:
        return [搜索到的文件]
    else:
        return 文件

def 批量删除(删除文件=[]):
    '''
    删除选中的文件
    :param 删除文件(list):所需要删除的文件的具体路径
    :return:
    '''
    for item in 删除文件:
        os.remove(item)
        print(f'{item}已删除')
    print('删除完成')

def 多品种数据叠加(账户初始资金, 数据文件路径列表, 直接相加=[], 减去初始资金相加=[], 开始时间=datetime(2016, 1, 1, 9, 0, 0),
            结束时间=datetime(2020, 10, 1, 16, 0, 0)):
    '''
    将都含有列名为'T'的数据表合并，其中每列的合并方式有直接相加的，如持仓情况等，也有减去初始资金相加的，如动态权益等
    :param 账户初始资金: 用于需要减去初始资金合并的列的合并
    :param 数据文件路径列表: 需要合并的文件的具体路径，格式为'.../xxx.csv'
    :param 直接相加: 合并方式为：Σ(列_i）
    :param 减去初始资金相加: 合并方式为：Σ(列_i-账户初始资金）+账户初始资金
    :param 开始时间: 应早于所有要合并的数据表中的最早的时间
    :param 结束时间: 应早于所有要合并的数据表中的最早的时间
    :return:
    Dataframe:叠加好的数据
    '''
    if len(数据文件路径列表) > 1:  # 两个及以上数据文件才能叠加
        列表 = 数据文件路径列表
        几分钟 = int((结束时间 - 开始时间).total_seconds() / 60)
        列数1 = len(直接相加)
        列数2 = len(减去初始资金相加)
        开始时间 = pd.to_datetime(str(datetime(开始时间.year, 开始时间.month, 开始时间.day, 开始时间.hour, 开始时间.minute, 开始时间.second)))
        # 结束时间 = pd.to_datetime(str(datetime(结束时间.year, 结束时间.month, 结束时间.day, 结束时间.hour, 结束时间.minute, 结束时间.second)))

        叠加数据 = np.zeros((几分钟, 2 + 列数1 + 列数2))
        乘数 = np.array([range(叠加数据.shape[0])])
        一分钟 = pd.to_timedelta(1, unit='m')
        时间列 = 开始时间 + 乘数 * 一分钟
        叠加数据[:, 0] = 时间列
        时间列 = 时间列.T

        # 列名df = ['T'] + 直接相加 + 减去初始资金相加
        列名df = 直接相加 + 减去初始资金相加

        for 文件 in 数据文件路径列表:
            print(f'正在操作{文件}')
            数据df = pd.read_csv(文件, encoding='gb2312', low_memory=False)
            数据时间 = pd.to_datetime(数据df['T'].values)
            交易数据 = np.zeros((数据df.shape[0], 1 + len(直接相加) + len(减去初始资金相加)))
            交易数据[:, 0] = np.array(数据时间, dtype=np.float64)
            for j, 列名 in enumerate(直接相加):
                交易数据[:, 1 + j] = 数据df[列名].values
            for j, 列名 in enumerate(减去初始资金相加):
                交易数据[:, 1 + 列数1 + j] = 数据df[列名].values - 账户初始资金
            叠加数据 = _合成数据_numba(叠加数据, 交易数据)
            print(f'{文件}操作完成')

        # 时间列 = 时间列[叠加数据[:, 1 + 列数1 + 列数2] == 1.].T
        时间列 = 时间列[叠加数据[:, 1 + 列数1 + 列数2] == 1.]
        叠加数据 = 叠加数据[叠加数据[:, 1 + 列数1 + 列数2] == 1.]
        叠加数据 = 叠加数据[:, :1 + 列数1 + 列数2]
        叠加数据[:, 1 + 列数1:1 + 列数1 + 列数2] = 叠加数据[:, 1 + 列数1:1 + 列数1 + 列数2] + 账户初始资金
        # 返回数据 = pd.DataFrame(0, index=range(叠加数据.shape[0]), columns=列名df)
        # 返回数据['T'] = 时间列[0, :]
        # 返回数据.iloc[:, 1:] = 叠加数据[:, 1:]
        返回数据 = pd.DataFrame(时间列, columns=['T']).join(pd.DataFrame(叠加数据[:, 1:], columns=列名df))

    else:
        print('只找到一个数据文件，无法叠加！')

    return 返回数据

def 合并csv(几级子文件夹=0, 合并方向=0, 保存路径='', 保存名称='合并数据表.csv'):
    '''
    将选定文件夹及其多级子文件夹下的csv表格按一定方式合并
    Args:
        几级子文件夹: 合并选定文件夹下几级子文件夹中的csv，若为0则只合并选定文件夹下的csv
        合并方向: 横向合并或纵向合并，选为0时为纵向合并，选为1时为横向合并
        保存路径: 合并好的数据表的保存路径
        保存名称: 将数据表保存为什么名称，格式为'xxx.csv'，xxx为相关命名

    Returns:

    '''
    print('请选择要遍历的文件夹')
    文件夹 = 选择文件(选择文件夹=True)
    if 保存路径 == '':
        print('请选择保存结果的文件夹')
        保存路径 = 选择文件(选择文件夹=True)
    数据表 = 寻找某类文件(['csv'], 搜索几级子文件夹=几级子文件夹, 搜索路径=文件夹)[0]

    合并表 = pd.read_csv(数据表[0], encoding='gb2312')

    for 表 in 数据表[1:]:
        读取 = pd.read_csv(表, encoding='gb2312')
        合并表 = pd.concat([合并表, 读取], axis=合并方向, join='outer')

    合并表.to_csv(os.path.join(保存路径, 保存名称), encoding='gb2312', index=False)

def 获取北京时间():
    '''
    获取当前网络时间对应的北京时间（获取失败时使用本地时间），以及当前日期的类型（工作日/双休日/法定节假日）
    :return:
    datetime:北京时间,int:日期类型（0为工作日，1为双休日，2为法定节假日，-1为获取失败）
    '''
    # try:
    #     # 设置头信息，没有访问会错误400！！！
    #     头信息 = {'User-Agent': 'Mozilla/5.0'}
    #     # 设置访问地址，我们分析到的；
    #     地址1 = r'http://time1909.beijing-time.org/time.asp'
    #     # 用requests get这个地址，带头信息的；
    #     请求1 = requests.get(url=地址1, headers=头信息)
    #     # 检查返回的通讯代码，200是正确返回；
    #     if 请求1.status_code == 200:
    #         # 定义result变量存放返回的信息源码；
    #         返回结果1 = 请求1.text
    #         # 通过;分割文本；
    #         数据1 = 返回结果1.split(";")
    #         # ======================================================
    #         # 以下是数据文本处理：切割、取长度
    #         年 = int(数据1[1][len("nyear") + 3: len(数据1[1])])
    #         月 = int(数据1[2][len("nmonth") + 3: len(数据1[2])])
    #         日 = int(数据1[3][len("nday") + 3: len(数据1[3])])
    #         # 周 = int(数据1[4][len("nwday") + 3: len(数据1[4])])
    #         时 = int(数据1[5][len("nhrs") + 3: len(数据1[5])])
    #         分 = int(数据1[6][len("nmin") + 3: len(数据1[6])])
    #         秒 = int(数据1[7][len("nsec") + 3: len(数据1[7])])
    #         # ======================================================
    #         北京时间 = datetime(年, 月, 日, 时, 分, 秒)
    #         if 月 < 10:
    #             日期 = f'{年}0{月}{日}' if 日 >= 10 else f'{年}0{月}0{日}'
    #         else:
    #             日期 = f'{年}{月}{日}' if 日 >= 10 else f'{年}{月}0{日}'
    #     else:
    #         北京时间 = datetime.now()
    #         年 = 北京时间.year
    #         月 = 北京时间.month
    #         日 = 北京时间.day
    #         if 月 < 10:
    #             日期 = f'{年}0{月}{日}' if 日 >= 10 else f'{年}0{月}0{日}'
    #         else:
    #             日期 = f'{年}{月}{日}' if 日 >= 10 else f'{年}{月}0{日}'
    #
    #     # 设置头信息，没有访问会错误400！！！
    #     头信息 = {'User-Agent': 'Mozilla/5.0'}
    #     # 设置访问地址，我们分析到的；
    #     地址2 = r"http://www.easybots.cn/api/holiday.php?d=" + 日期
    #     # 用requests get这个地址，带头信息的；
    #     请求2 = requests.get(url=地址2, headers=头信息)
    #     # 检查返回的通讯代码，200是正确返回；
    #     if 请求2.status_code == 200:
    #         # 定义result变量存放返回的信息源码；
    #         返回结果2 = 请求2.text
    #         结果字典 = ast.literal_eval(返回结果2)
    #         日期类型 = int(结果字典[日期])  # 0为工作日，1为双休日，2为法定节假日
    #     else:
    #         if 北京时间.weekday() == 5 or 北京时间.weekday() == 6:
    #             日期类型 = 1
    #         else:
    #             日期类型 = 0
    #     return 北京时间, 日期类型
    # except:
    北京时间 = datetime.now()
    if 北京时间.weekday() == 5 or 北京时间.weekday() == 6:
        日期类型 = 1
    else:
        日期类型 = 0
    return 北京时间, 日期类型


if __name__ == '__main__':
    # 文件 = 寻找某类文件(文件类型=['csv'])  # '文件夹','py','csv',
    # 批量删除(删除文件=寻找某类文件(文件类型=['txt'])[0])
    # print(文件)
    # t = datetime.now()
    # 叠加数据 = 多品种数据叠加(500000, 文件[0], 直接相加=['总持仓量', '净多底量', '净空底量'], 减去初始资金相加=['平仓余额', '动态权益'],
    #                开始时间=datetime(2016, 1, 1, 9, 0, 0),
    #                结束时间=datetime(2020, 10, 1, 16, 0, 0))
    # print('t1:', datetime.now() - t)
    # 开始日期 = datetime(2016, 1, 1, 9, 0, 0)
    # 结束日期 = datetime(2020, 9, 1, 16, 0, 0)
    # for _ in range(1):
    #     t = datetime.now()
    #     一分钟K线, 小时时间 = 获取一分钟K线('早稻指数1分钟数据.csv', 开始日期, 结束日期)
    #     print('t1:', datetime.now() - t)
    # for _ in range(1):
    #     t = datetime.now()
    #     K线 = Kline(一分钟K线, 小时时间, 15, )  # 输出格式='dataframe')
    #     # 一分钟K线 = 一分钟K线[一分钟K线[:,5]!=0.0]
    #     # 时间=np.array([[x,y] for x,y in zip(一分钟K线[:,0],小时时间)])
    #     # K线.to_csv('test.csv')
    #     print('t2:', datetime.now() - t)
    #
    # # for _ in range(3):
    # #     t = datetime.now()
    # #     K线 = Kline2('早稻指数1分钟数据.csv', 开始日期, 结束日期, 15)
    # #     print('t1:', datetime.now() - t)
    #
    # for _ in range(3):
    #     t = datetime.now()
    #     近似tick数据 = 一分钟K线近似tick数据(K线, 15, 一分钟K线, 输出格式='array')
    #     # 一分钟K线 = 一分钟K线[一分钟K线[:,5]!=0.0]
    #     # 时间=np.array([[x,y] for x,y in zip(一分钟K线[:,0],小时时间)])
    #     # K线.to_csv('test.csv')
    #     print('t2:', datetime.now() - t)
    # # 一分钟K线近似tick数据(K线, 15, 一分钟K线, 输出格式='array')
    print(获取北京时间())
