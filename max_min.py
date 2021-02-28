#!/usr/bin/env python
# coding: utf-8

# # Margins Min-Max (Cervix cancer data) 
#  
# Python code to extract the maximum and minimum values from motion data of MR-Linac patients.  
# Margins are drawn around key structures, including CTV, GTV, and organs at risk.  
# This is for pelvic MR-Linac only - but can be adapted towards other margins projects.  
# 
# ## File structure:
# patient MRI data is stored in csv, by week and imaging type.  
# prior Python script has already done a comparison between margins of various weeks
# 
# ## Comparisons: 
# Intrafraction = within same week, comparing motion of scans over time in same day  
# Interfraction = same patient but across different weeks 
# 
# ## Sections
# Part 1 - importing libraries, declaring all functions to read files for each patient  
# Part 2 - defining target folders, parameters and regions of interest  
# Part 3 - running the script  
# 
# # Part 1:

# In[1]:


import pandas as pd
import os
import csv
import re


def splitter_base_comparison(comparison_scan, original_df, roi):
    """Splits the original csv into two dataframes - base scan and comparison scan for ROI.
    
    Arguments:
    comparison_scan = comparison week scan in pandas dataFrame
    original_df = full original csv in pandas dataFrame
    roi = string of region of interest, ie. "Bladder"
    
    """
    # get indices for region of interest
    df_idx = comparison_scan.index[comparison_scan['roi'] == roi].tolist()
    
    # get base week df
    df_base = original_df[original_df['roi'].str.match(roi)]
    df_base = df_base[df_base['R.x'].eq(0)] # get base week data
    
    return df_base, comparison_scan.loc[df_idx]


def getLRAPS(df, roi):
    """Returns minimum and maximum values for motions in 3 axes"""
 
    # removes all useless rows that are zero values
    # in dataset, zero values are the base week
    # comparison week has values 
    comparison_scan = df[(df != 0).all(1)]  
    df_base, dataFrame = splitter_base_comparison(comparison_scan, df, roi)

    # refZ = dataFrame.iloc[0]['RefZ'] // not used at the moment
    
    # zcompareMax - zbaseMAx
    supz = float(dataFrame['z-RefZ'].max()) - df_base['z-RefZ'].max()
                                        
    # zcompareMin - zbasemin
    infz =  float(dataFrame['z-RefZ'].min()) - df_base['z-RefZ'].min()
    

    # get min and max for each paramater
    rx_max = dataFrame['R.x'].max()
    rx_min = dataFrame['R.x'].min()
    lx_max = dataFrame['L.x'].max()
    lx_min = dataFrame['L.x'].min()

    py_max = dataFrame['P.y'].max()
    py_min = dataFrame['P.y'].min()
    ay_max = dataFrame['A.y'].max()
    ay_min = dataFrame['A.y'].min()
    
    return supz, infz, rx_max, rx_min, lx_max, lx_min, py_max, py_min, ay_max, ay_min


# In[2]:


def getStudyMetadata(filename):
    """extract patient metadata out of namefile"""
    
    patientNum = filename[0:7]
    baseWeek = filename[13:16]
    
    baseModality = ""
    temp_baseModality = re.search(r"\=....(.*)...\_", filename)
    if temp_baseModality:
        baseModality = (temp_baseModality.group(1))
    
    comparisonWeek = ""
    temp_comparisonWeek = re.search(r"\_vs_(Wk\d)", filename)
    if temp_comparisonWeek:
        comparisonWeek = (temp_comparisonWeek.group(1))
    
    comparisonModality = filename[29:-4]
    
        
    comparisonModality = ""
    temp_comparisonModality = re.search(r"\_vs_... (.*)\.", filename)
    if temp_comparisonModality:
        comparisonModality = (temp_comparisonModality.group(1))
    
    fraction = ''    
    if baseWeek == comparisonWeek:
        fraction = 'intrafraction'
    else:
        fraction = 'interfraction'    
    
    return patientNum, baseWeek, baseModality, comparisonWeek, comparisonModality, fraction


# In[3]:


# main function
def calculate_points(dir_list, roi):
    output_file_paths = [] # init output_paths
    
    for folder in dir_list:
        for filename in os.listdir(folder) :
            if filename.endswith('.csv') and filename.startswith('Z') and ("SUPINF" not in filename):
                df = pd.read_csv(os.path.join(folder, filename))

                roi = roi
                output = [] 
                # populates output with patient metadata for naming files later
                output.extend(list(getStudyMetadata(filename)))

                for n in roi:
                    output.extend(list(getLRAPS(df, n)))

                # separate csv for inter and intrafraction
                # open and output to new CSV file
                
                os.makedirs(os.path.join(folder, 'output'), exist_ok=True)
                with open(os.path.join(folder, 'output/{}{}.csv'.format(output[5],folder[-3:])), 'a') as file_:
                    output_file_paths.append(os.path.realpath(file_.name))
                    wr = csv.writer(file_, delimiter=',')
                    wr.writerow(output)

                print('Done extract for ', filename, output[5])
    
    return list(set(output_file_paths))


# In[4]:


# write full headers recursively
def write_headers(roi, headers, output_file_paths):
    for n in roi:
        for l in param:
            headers.append(n + ' ' + l)

    # get output file paths and to add headers to output files
    for file_path in output_file_paths:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        add_header = pd.read_csv(file_path, names=headers, index_col=None)
        add_header.to_csv(file_path)
        print('Done header:' + file_path)


# # Part 2: Specifying folders and variables

# In[5]:


# use os.join and os.getcdw to pull all filenames
# init variables folder_names, 

folder_name = [
    'Dec20_data/Interfraction/Interfraction 3D 0.8', 
    'Dec20_data/Interfraction/Interfraction DIXON 2.0', 
    'Dec20_data/Intrafraction 3D vs DIXON HR IP 2.0'
    ]

dir_list = []
for i in range(len(folder_name)):
    dir_list.append(
        os.path.join(os.getcwd(), folder_name[i])
    )

roi = ['GTV_T', 'CTV_Clin', 'CTV_SmallVol', 'Bladder', 'Rectum']

headers = ['patientNum', 'baseWeek', 'baseModality', 'comparisonWeek', 'comparisonModaility', 'fraction']
param = ['supz', 'infz', 'rx_max', 'rx_min', 'lx_max', 'lx_min', 'py_max', 'py_min', 'ay_max', 'ay_min']


# # Part 3: Running script

# In[6]:


# execute all functions
# 1. do all calculations 
output_file_paths = calculate_points(dir_list, roi)

# 2. write all headers'
write_headers(roi, headers, output_file_paths)

