import numpy as np
import pandas as pd
import os
import sys
import math
import datetime as dt
from dateutil.relativedelta import relativedelta
import seaborn as sns

import matplotlib.pyplot as plt

#  AR: Africa, Asian_Pacific, Asian, Euro, North_America
#  FR: North_America, Euro
Africa = pd.read_csv("Africa.csv")
Asian_Pacific = pd.read_csv("Asian Pacific.csv")
Asian = pd.read_csv("Asian.csv")
Euro = pd.read_csv("EURO.csv")
North_America = pd.read_csv("North America.csv")
Gb = pd.read_csv("Global.csv")

Africa["FILING_DATE"] = pd.to_datetime(Africa["FILING_DATE"])
Asian_Pacific["FILING_DATE"] = pd.to_datetime(Asian_Pacific["FILING_DATE"])
Asian["FILING_DATE"] = pd.to_datetime(Asian["FILING_DATE"])
Euro["FILING_DATE"] = pd.to_datetime(Euro["FILING_DATE"])
North_America["FILING_DATE"] = pd.to_datetime(North_America["FILING_DATE"])
Gb["FILING_DATE"] = pd.to_datetime(Gb["FILING_DATE"])

Africa.sort_values('FILING_DATE', ascending=True, ignore_index=True, inplace=True)
Asian_Pacific.sort_values('FILING_DATE', ascending=True, ignore_index=True, inplace=True)
Asian.sort_values('FILING_DATE', ascending=True, ignore_index=True, inplace=True)
Euro.sort_values('FILING_DATE', ascending=True, ignore_index=True, inplace=True)
North_America.sort_values('FILING_DATE', ascending=True, ignore_index=True, inplace=True)
Gb.sort_values('FILING_DATE', ascending=True, ignore_index=True, inplace=True)

t = [Gb["FILING_DATE"][0].date() + (i + 1) * relativedelta(months=3) for i in range(69)]


# print(Gb.columns)


def func(time, region, factor):
    index = 0
    avg = []
    for i in range(len(time)):
        sum_of_avg = 0
        count = 0
        while region["FILING_DATE"][index] < time[i]:
            sum_of_avg += region[factor][index]
            count += 1
            index += 1
            if index == len(region["FILING_DATE"]):
                break
        d = sum_of_avg / count if count > 0 else 0
        avg.append(d)

    # avg = np.array([sum(avg[i - 4:i + 1]) / 5 if i > 3 else sum(avg[0:i + 1]) / (i + 1) for i in range(len(time))])

    return avg


#  'avg_sent_x'  'sum_sent_x'  'hit_count_x'  'positive_hits_x'  'negative_hits_x'
#  'section_count_x'  'word_count_x'  'avg_sent_y' 'sum_sent_y'  'hit_count_y'
#  'positive_hits_y'  'negative_hits_y'  'section_count_y'  'word_count_y'
factor = 'avg_sent_x'

# print(Gb[factor].values)
factor_matrix = pd.DataFrame()
factor_matrix["Global"] = func(t, Gb, factor)
factor_matrix["Africa"] = func(t, Africa, factor)
factor_matrix["Asian_Pacific"] = func(t, Asian_Pacific, factor)
factor_matrix["Asian"] = func(t, Asian, factor)
factor_matrix["Euro"] = func(t, Euro, factor)
factor_matrix["North_America"] = func(t, North_America, factor)

# print(factor_matrix)


names = ['Global', 'Africa', 'Asian_Pacific', 'Asian', 'Euro', 'North_America']
correlations = factor_matrix.corr()
# correlations = abs(correlations)

fig = plt.figure()
ax = fig.add_subplot(figsize=(20, 20))  # 图片大小为20*20
ax = sns.heatmap(correlations, cmap=plt.cm.Greys, linewidths=0.05, vmax=1, vmin=0, annot=True,
                 annot_kws={'size': 6, 'weight': 'bold'})
# 热力图参数设置（相关系数矩阵，颜色，每个值间隔等）
ticks = np.arange(0, 6, 1)  # 生成0-16，步长为1
plt.xticks(np.arange(6), names)  # 横坐标标注点
plt.yticks(np.arange(6), names)  # 纵坐标标注点
ax.set_xticks(ticks + 0.5)  # 生成刻度
ax.set_yticks(ticks + 0.5)
ax.set_xticklabels(names)  # 生成x轴标签
ax.set_yticklabels(names)
ax.set_title('Characteristic correlation')  # 标题设置

plt.savefig(factor + '_MA5.png', dpi=600)
plt.show()
