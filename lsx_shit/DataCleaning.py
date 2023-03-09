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


def classify(data, classification_tag, path, if_save=True):
    """
    Use a specific tag to split data and save the results
    :param data: pd.DataFrame: raw data
    :param classification_tag: str: "SECTOR"  "REGION"  "COUNTRY"
    :param path: str: the absolute path to save results
    :param if_save: Bool: weather save the result or not
    :return: data_with_tag: pd.DataFrame, tag_dict: dict, tag_dict_note: dict
    """

    if classification_tag == None:
        return 0

    #  split by tag
    note = ""
    tag_name = data[classification_tag].values
    tag_select = [True if isinstance(sn, str) else False for sn in tag_name]
    data_with_tag = data.iloc[tag_select, :]
    tag_name = np.unique(tag_name[tag_select])
    tag_dict = {key: data.loc[data[classification_tag].values == key].values.tolist() for key in tag_name}
    tag_with_few_samples_index = [True if len(tag_dict[key]) < 500 else False for key in tag_name]
    tag_with_few_samples = tag_name[tag_with_few_samples_index].tolist()
    note += "There are " + str(
        len(data) - len(data_with_tag)) + " reports without tagging of " + classification_tag + ".\n"
    note += "There are " + str(len(data_with_tag)) + " reports with tagging of " + classification_tag + ".\n"
    tag_dict_note = {"columns_name": data.columns.values.tolist(),
                        classification_tag + "_name": tag_name.tolist(),
                        "Number_of_" + classification_tag: len(tag_name),
                        classification_tag + "_with_few_samples": tag_with_few_samples,
                        "Number_of_" + classification_tag + "_with_few_samples": len(tag_with_few_samples),
                        "note": note}

    #  save file
    if if_save:
        folder_name = classification_tag + "_Classification"
        folder_list = [x for x in os.listdir(path) if os.path.isdir(x)]
        if folder_name not in folder_list:
            os.mkdir(os.path.join(path, folder_name))
        sub_path = os.path.join(path, classification_tag + "_Classification")

        json_str = json.dumps(tag_dict)
        with open(os.path.join(sub_path, classification_tag + '_Classification.json'), 'w',
                  encoding='utf-8') as json_file:
            json_file.write(json_str)
            json_file.close()
        json_str = json.dumps(tag_dict_note)
        with open(os.path.join(sub_path, classification_tag + '_Classification_Note.json'), 'w',
                  encoding='utf-8') as json_file:
            json_file.write(json_str)
            json_file.close()

        data_with_tag.to_csv(os.path.join(sub_path, "Data_with_" + classification_tag + "_Tag.csv"),
                                    encoding="utf-8", index=False)

    return data_with_tag, tag_dict, tag_dict_note


def read_classified_data(path, principle):
    """
    Read data classified by a certain principle, like region, country, or sector
    :param path: str: the path of a specific folder that contains the folder
    which include data_with_tag, tag_dict, and tag_dict_note
    :param principle: str: the way to split data, usually are "SECTOR"  "REGION"  "COUNTRY"
    :return: data: pd.DataFrame, tag_dict: dict, tag_dict_note: dict
    """
    if principle == None:
        data = pd.read_csv(os.path.join(path, "Factors.csv"))
        data["FILING_DATE"] = pd.to_datetime(data["FILING_DATE"])
        tag_dict = {}
        tag_dict_note = {}
    else:
        folder_name = principle + "_Classification"
        sub_path = os.path.join(path, folder_name)

        data = pd.read_csv(os.path.join(sub_path, "Data_with_" + principle + "_Tag.csv"))
        data["FILING_DATE"] = pd.to_datetime(data["FILING_DATE"])
        tag_dict = json.load(open(os.path.join(sub_path, principle + '_Classification.json'), 'r', encoding='utf8'))
        tag_dict_note = json.load(
            open(os.path.join(sub_path, principle + '_Classification_Note.json'), 'r', encoding='utf8'))

        for key in tag_dict:
            tag_dict[key] = pd.DataFrame(tag_dict[key], columns=data.columns)
            tag_dict[key]["FILING_DATE"] = pd.to_datetime(tag_dict[key]["FILING_DATE"])
        for key in tag_dict_note:
            print(key, " : ", tag_dict_note[key])

    return data, tag_dict, tag_dict_note


def _break_point(end_point, data, n, index):
    for i in range(n):
        if i < n - 1:
            if data[i, 0] != data[i + 1, 0]:
                end_point.append(i)
                index += 1
        else:
            end_point.append(i)

    return end_point


def split(path):
    """
    Split the whole price file into files of individual stock's price
    :param path: str: the path used to save results
    :return: None
    """
    data = pd.read_csv("Monthly_Price.csv")
    col = data.columns
    data = data.values
    n = len(data)
    index = 0
    end_point = []
    end_point = _break_point(end_point, data, n, index)

    folder_name = "Individual_Stock_Price"
    sub_folder_name = "Stock_Price"
    folder_list = [x for x in os.listdir('.') if os.path.isdir(x)]
    sub_path = os.path.join(path, folder_name)
    sub_sub_path = os.path.join(sub_path, sub_folder_name)
    if folder_name not in folder_list:
        os.makedirs(sub_sub_path)

    start = 0
    id_list = []
    for end in end_point:
        id = str(data[end, 0])
        id_list.append(data[end, 0])
        # pd.DataFrame(data[start:end + 1, :], columns=col).to_csv(os.path.join(sub_sub_path, id + '.csv'),
        #                                                          encoding="utf-8")
        start = end + 1

    id_dict = {"stock_id": id_list}

    json_str = json.dumps(id_dict)
    with open(os.path.join(sub_path, "stock_id.json"), 'w', encoding='utf-8') as json_file:
        json_file.write(json_str)
        json_file.close()


def read_stock_id(path):
    """
    Get stock id
    :param path:
    :return: stock_id: list
    """
    sub_path = os.path.join(path, "Individual_Stock_Price")
    stock_id_dict = json.load(open(os.path.join(sub_path, "stock_id.json"), 'r', encoding='utf8'))
    return stock_id_dict["stock_id"]


def get_valid_id(stock_id, trading_item_id):
    """
    To get the stock id which appears in both factor file and stock price file
    :param stock_id: list: stock id from stock price file
    :param trading_item_id: list: stock id from factor file
    :return: valid_id: list: id of which we have both factor values and stock price data
    """
    trading_item_id = np.unique(trading_item_id)
    valid_id_index = [True if id in trading_item_id else False for id in stock_id]
    valid_id = np.array(stock_id)[valid_id_index].tolist()
    print("There are ", len(valid_id), " valid stock id and ", len(stock_id) - len(valid_id),
          "invalid stock id in stock price file.")
    print(len(trading_item_id) - len(valid_id), " stocks in factor file don't have their price data.")

    return valid_id


def average(data, factor, period=1, unit="month", if_civil=False):
    """
    Used to calculate average of factor value on a specific time length, and the missing value will be estimated
    by several values around its position
    :param data: pd.DataFrame: the dataframe that contains datetime and factor value
    :param factor: str: the factor of which we will calculate the average value of "avg_sent",
                        "sum_sent", "hit_count". "positive_hits", ""negative_hits",
                        "section_count", "word_count"
    :param period: int: how many periods of unit we want to calculate the average on
    :param unit: str: time unit, "month","year"
    :param if_civil: whether to use civil calendar time. if not, 1 month = 30 days and 1 year = 365 days
    :return: avg_value: pd.Series: the average value of the factor with index set as timestamp of end date of each period
    """

    # calculate average value on time
    if if_civil:
        pass
    else:
        if unit == "month":
            time_unit = relativedelta(days=30)
        elif unit == "year":
            time_unit = relativedelta(days=365)

        time_length = period * time_unit
        data.sort_values('FILING_DATE', ascending=True, ignore_index=True, inplace=True)
        start_date = data["FILING_DATE"][0]
        end_date = data["FILING_DATE"][len(data) - 1]
        if unit == "month":
            periods_number = math.ceil((end_date - start_date).days / 30 / period)
        elif unit == "year":
            periods_number = math.ceil((end_date - start_date).days / 365 / period)

        end_time = [start_date + time_length * i for i in range(1, periods_number - 1)]

        index = 0
        avg_value = []
        for time in end_time:
            sum_of_avg = 0
            count = 0
            while data["FILING_DATE"][index] < time:
                sum_of_avg += data[factor][index]
                count += 1
                index += 1
                if index == len(data["FILING_DATE"]):
                    break
            avg_value.append(sum_of_avg / count if count > 0 else 0)
        avg_value = np.array(avg_value)

    #  estimate missing values
    while np.sum([avg_value == 0]) > 0:
        for i in range(len(avg_value)):
            if i == 0:
                if avg_value[i] == 0:
                    avg_value[i] = avg_value[i + 1]
            elif i == len(avg_value) - 1:
                if avg_value[i] == 0:
                    avg_value[i] = avg_value[i - 1]
            else:
                if avg_value[i] == 0:
                    avg_value[i] = (avg_value[i - 1] + avg_value[i + 1]) / 2

    # average_value = pd.DataFrame(np.array([end_time, avg_value]).T, columns=["end_time", "avg_value"])
    average_value = pd.DataFrame(np.array([end_time, avg_value]).T, columns=["end_time", factor])

    return average_value


def moving_average(value, period=10, type="SMA"):
    '''
    Used to calculate moving average
    :param value: np.array: the data of that calculate moving average
    :param period: int: calculate moving average on witch time periods
    :param type: str: method to calculate MA, "SMA", "EMA", "WMA", "CMA"
    :return: MA: np.array: MA
    '''
    MA = []
    if type == "SMA":
        for i in range(len(value)):
            if i < period - 1:
                MA.append(np.mean(value[:i + 1]))
            else:
                MA.append(np.mean(value[i - 9:i + 1]))

    elif type == "EMA":
        pass

    elif type == "WMA":
        pass

    elif type == "CMA":
        pass

    return MA


if __name__ == "__main__":
    col_name = ['FILINGID', 'TRADINGITEMID', 'TICKERSYMBOL', 'TRADINGITEMSTATUSNAME',
                'COMPANYNAME', 'EXCHANGENAME', 'EXCHANGEIMPORTANCE', 'SECTOR',
                'SIMPLEINDUSTRYDESCRIPTION', 'REGION', 'COUNTRY', 'DOCUMENT_ID',
                'DOCUMENT_TYPE', 'FILING_DATE', 'DETAIL_JSONcompany_name', 'avg_sent',
                'sum_sent', 'hit_count', 'positive_hits', 'negative_hits',
                'section_count', 'word_count']

    # #  "SECTOR"  "REGION"  "COUNTRY"  "SIMPLEINDUSTRYDESCRIPTION"  "TRADINGITEMSTATUSNAME"  None
    classification_tag = "SECTOR"

    # #  Get path
    # path = os.getcwd()
    path = os.path.abspath('.')

    # #  Classify
    data = pd.read_csv("Factors.csv")
    classify(data, classification_tag,path)

    # #  Read files
    data, tag_dict, tag_dict_note = read_classified_data(path, classification_tag)

    # #  Split stock price file
    split(path)

    # #  Get valid stock id
    stock_id = read_stock_id(path)
    valid_id = get_valid_id(stock_id, data["TRADINGITEMID"].values)

    # #  Average Value
    avg = average(data, factor="avg_sent", period=3, unit="month", if_civil=False)

    # #  Moving Average
    avg["moving_average"] = moving_average(avg["avg_value"].values, period=10, type="SMA")

    input("\nPress enter to exit")
