
import pandas as pd
import numpy as np
import ndjson
import os
import fnmatch


# folder with the Reference, Data, Word Count, and Sentiment zipped files
os.chdir('D:\\CA\\en-US')
flag=0

#### Filing Reference Package ####
# create an empty list, combined_ref, and loop through each file and combine to combined_ref
# combined ref will be a list of dictionaries
combined_ref = []
for file in os.listdir():
    if(fnmatch.fnmatch(file, 'SP_FILING_REFERENCE*')):
        with open(file,'r',encoding='utf_8') as ref:
            ref = ndjson.load(ref)
        combined_ref.extend(ref)    
 
# normalize the reference package from its NDJSON form into a Data Frame - uses from pandas.io.json import json_normalize
ref_normalize = pd.json_normalize(combined_ref)

# change order of columns to reflect User Guide documentation
ref_normalize = ref_normalize[['ID', 'DOCUMENT_ID','DOCUMENT_TYPE','FILING_DATE','MODIFIED_AT','DETAIL_JSON.company_name', 'DETAIL_JSON.parsing_status']]

# convert the ID and document ID field to a string
ref_normalize['ID'] = ref_normalize['ID'].apply(str)
ref_normalize['DOCUMENT_ID'] = ref_normalize['DOCUMENT_ID'].apply(str)
# ref_normalize['DETAIL_JSON.ISIN_active'] = ref_normalize['DETAIL_JSON.ISIN_active'].apply(str)
# ref_normalize['DETAIL_JSON.SP_DocumentId'] = ref_normalize['DETAIL_JSON.SP_DocumentId'].apply(str)

#### Sentiment Score Package ####
# create an empty list, combined_sc, and loop through each file and combine to combined_sc
# combined_sc will be a list of dictionaries
combined_sc = []
for file in os.listdir():
    if(fnmatch.fnmatch(file, 'SP_FILING_SENTIMENT*')):
        try:
            with open(file,'r',encoding='utf_8') as sc:# gzip 用来打开压缩文件中的数据
                sc = ndjson.load(sc)
            combined_sc.extend(sc)  # 加入最后
        except Exception as e:
            pass
            flag+=1
        continue


## Filing Level Function
# Function for calculating the sentiment figures at the main filing level - i.e., the aggregated sentiment figures for the actual
# filing (EXCLUDING exhibits)
#Parameter: filing_type - the filing type of the data in combined_sc (examples: '10-k', '10-q')
def filing_level_func(filing_type):
# column names of sentiment scores package based on User Guide documentation
    column_names = ['ID','avg_sent','sum_sent','hit_count','positive_hits','negative_hits','section_count','word_count']
# create empty list called filin g_level_list
    filing_level_list = [[]]
# loop through each element in combined_sc, check if the filing_type key exists in the 'SENTIMENT' key
# if it does append doc_level_list with ID and the sentiment scores
# if it does not, append doc_level_level with ID and NAs
    for element in range(len(combined_sc)):
        if combined_sc[element].get('SENTIMENT',{}).get(filing_type):
            filing_level_list.append([str(combined_sc[element]['ID']), 
                          combined_sc[element]['SENTIMENT'][filing_type]['avg_sent'],
                          combined_sc[element]['SENTIMENT'][filing_type]['sum_sent'],
                          combined_sc[element]['SENTIMENT'][filing_type]['hit_count'], 
                          combined_sc[element]['SENTIMENT'][filing_type]['positive_hits'],
                          combined_sc[element]['SENTIMENT'][filing_type]['negative_hits'],
                          combined_sc[element]['SENTIMENT'][filing_type]['section_count'],
                          combined_sc[element]['SENTIMENT'][filing_type]['word_count']])
        else:
            filing_level_list.append([str(combined_sc[element]['ID']), np.nan, np.nan, np.nan, np.nan, np.nan, np.nan,np.nan])

    # take contents of filing_level_list and put into a data frame called filing_level_df
    filing_level_df = pd.DataFrame(filing_level_list[1:len(filing_level_list)], columns = column_names)    
     
    # convert the ID field to a string
    filing_level_df['ID'] = filing_level_df['ID'].apply(str)
    
    # return the data frame
    return filing_level_df


## Section Level Function
# Function for calculating the sentiment figures at the section level
#Parameter: 
# filing_type - the filing type of the data in combined_sc (examples: 'AR', 'QR', 'SR')
# section - the section of the filing_type of the data in combined_sc (examples: 'data', 'letter to shareholders', 'ceo report',etc)    
def section_level_func(filing_type, section):
# column names of sentiment scores package based on User Guide documentation
    column_names = ['ID','avg_sent','sum_sent','hit_count','positive_hits','negative_hits','section_count','word_count']   
# create empty list called section_level_list
    section_level_list = [[]] 
# loop through each element in combined_sc, check if the section key exists in the 'SENTIMENT' key -> filing_type key
# if it does append section_level_list with ID and the sentiment scores
# if it does not, append section_level_level with ID and NAs
    for element in range(len(combined_sc)):
        if combined_sc[element].get('SENTIMENT',{}).get(filing_type,{}).get(section):
            section_level_list.append([str(combined_sc[element]['ID']), 
                          combined_sc[element]['SENTIMENT'][filing_type][section]['avg_sent'],
                          combined_sc[element]['SENTIMENT'][filing_type][section]['sum_sent'],
                          combined_sc[element]['SENTIMENT'][filing_type][section]['hit_count'], 
                          combined_sc[element]['SENTIMENT'][filing_type][section]['positive_hits'],
                          combined_sc[element]['SENTIMENT'][filing_type][section]['negative_hits'],
                          combined_sc[element]['SENTIMENT'][filing_type][section]['section_count'],
                          combined_sc[element]['SENTIMENT'][filing_type][section]['word_count']])
        else:
            section_level_list.append([str(combined_sc[element]['ID']), np.nan, np.nan, np.nan, np.nan, np.nan, np.nan,np.nan])

    # take contents of section_level_list and put into a data frame called section_level_df
    section_level_df = pd.DataFrame(section_level_list[1:len(section_level_list)], columns = column_names)    
    
    # convert the ID field to a string
    section_level_df['ID'] = section_level_df['ID'].apply(str)
    
    # return the data frame
    return section_level_df


## Sub-section Level Function  
#Parameter: 
# filing_type - the filing type of the data in combined_sc (examples: '10-k', '10-q')
# section - the section of the filing_type of the data in combined_sc (examples: 'data', 'letter to shareholders', 'ceo report',etc)    
# sub-section - the sub-section of the section of the filing_type in combined_sc (examples: 'data','esg','risk', etc.)  
def sub_level_func(filing_type, section, sub):
# column names of sentiment scores package based on User Guide documentation
    column_names = ['ID','avg_sent','sum_sent','hit_count','positive_hits','negative_hits','section_count','word_count']
# create empty list called sub_level_list
    sub_level_list = [[]] 
# loop through each element in combined_sc, check if the seub-section key exists in the 'SENTIMENT' key -> filing_type key -> section key
# if it does append sub_level_list with ID and the sentiment scores
# if it does not, append sub_level_list with ID and NAs
    for element in range(len(combined_sc)):
        if combined_sc[element].get('SENTIMENT',{}).get(filing_type,{}).get(section,{}).get(sub):
            sub_level_list.append([str(combined_sc[element]['ID']), 
                          combined_sc[element]['SENTIMENT'][filing_type][section][sub]['avg_sent'], 
                          combined_sc[element]['SENTIMENT'][filing_type][section][sub]['sum_sent'],
                          combined_sc[element]['SENTIMENT'][filing_type][section][sub]['hit_count'], 
                          combined_sc[element]['SENTIMENT'][filing_type][section][sub]['positive_hits'],
                          combined_sc[element]['SENTIMENT'][filing_type][section][sub]['negative_hits'], 
                          combined_sc[element]['SENTIMENT'][filing_type][section][sub]['section_count'],
                          combined_sc[element]['SENTIMENT'][filing_type][section][sub]['word_count']])
      
        else: sub_level_list.append([str(combined_sc[element]['ID']), np.nan, np.nan, np.nan, np.nan, np.nan, np.nan,np.nan])
        
    # take contents of sub_level_list and put into a data frame called sub_level_df
    sub_level_df = pd.DataFrame(sub_level_list[1:len(sub_level_list)], columns = column_names)    
    
    # convert the ID field to a string
    sub_level_df['ID'] = sub_level_df['ID'].apply(str)  
    
    # return the data frame
    return sub_level_df

## Examples of calling functions
# get the AR sentiment data at the filing level
ars = filing_level_func('ar')

# Join reference information with sentiment metrics
combined = pd.merge(left = ref_normalize, right = ars, on = 'ID')

# Examine how many data that the exception drops
print(flag)

# drop the duplicate 
len_init=len(combined)
print(len_init)
combined.duplicated(['ID'])
combined=combined.drop_duplicates(['ID'])
len_out=len(combined)
drop_len=len_init-len_out
print(drop_len)

combined.to_csv("D:\\code\\practicum\\outcome\\combined_CA.csv",sep=",",header=True)

# combined.groupy({})
# type(combined)
