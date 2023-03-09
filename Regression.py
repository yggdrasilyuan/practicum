#!/usr/bin/env python
#  -*- coding: utf-8 -*-

"""
This file is used to select, process, save, and read raw data.
"""

__author__ = 'jl208@illinois.edu'

import json
import os
import math
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
import statsmodels.formula.api as smf
import DataCleaning as DC

# #  "SECTOR"  "REGION"  "COUNTRY"  "SIMPLEINDUSTRYDESCRIPTION"  "TRADINGITEMSTATUSNAME"  None
classification_tag = "SECTOR"

# #  'avg_sent'  'sum_sent'  'hit_count'  'positive_hits'  'negative_hits'
#                 'section_count'  'word_count'
factor_name = 'avg_sent'

# #  Get path
# path = os.getcwd()
path = os.path.abspath('.')

print(path)

data, tag_dict, tag_dict_note = DC.read_classified_data(path, classification_tag)

tag_dict = {key: tag_dict[key] for key in tag_dict if
            key not in tag_dict_note[classification_tag + "_with_few_samples"]}
tag_name = [key for key in tag_dict if key not in tag_dict_note[classification_tag + "_with_few_samples"]]

model_value_x = []
model_value_y = []
name = [factor_name, "time"]
intercept_name = []
coefficient_name = []
variable_name_note_x = {tag_name[0]: "All dummy variables equal to 0"}
for i, key in enumerate(tag_name):

    tag_value = tag_dict[key]
    tag_value_avg = DC.average(tag_value, factor=factor_name, period=1, unit="month", if_civil=False)
    time_length = len(tag_value_avg)
    tag_number = len(tag_name)
    if i > 0:
        intercept_name.append("intercept_d{}".format(i))
        coefficient_name.append("coef_d{}".format(i))
        variable_name_note_x["intercept_d{}".format(i)] = "intercept of " + key + "'s dummy variable"
        variable_name_note_x["coef_d{}".format(i)] = "coefficient of " + key + "'s dummy variable"

    for j in range(time_length):
        time = [j]
        intercept_dummy = [0] * (tag_number - 1)
        coefficient_dummy = [0] * (tag_number - 1)
        if i > 0:
            intercept_dummy[i - 1] = 1
            coefficient_dummy[i - 1] = j
        model_value_x.append(time + intercept_dummy + coefficient_dummy)

    model_value_y += tag_value_avg[factor_name].values.tolist()
name += intercept_name + coefficient_name

model_value_x = np.array(model_value_x)
model_value_y = np.array(model_value_y)
model_value = np.column_stack((model_value_y, model_value_x))
model_value = pd.DataFrame(model_value, columns=name)

formula = name[0] + '~' + name[1]
for i in range(2, len(name)):
    formula += '+' + name[i]
res = smf.ols(formula=formula, data=model_value)
mod = res.fit()
print(mod.summary())
for key in variable_name_note_x:
    print(key,' : ', variable_name_note_x[key])
