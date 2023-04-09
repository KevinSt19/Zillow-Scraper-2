'''
This program downloads html source from a Zillow search page, parses the html to extract data, and displays the data in a variety of figures.  It is intended to provide insight into the local real estate market, with configurable parameters such as location.
'''

import os
import time
import sys
import regex as re
import numbers
import json
import math
from datetime import datetime as dt

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import numpy as np
import pandas as pd
import requests
import lxml
from lxml.html.soupparser import fromstring
import prettify
import htmltext
import matplotlib.pyplot as plt

import backend as be


# GLOBAL VARIABLES
root_dir = os.getcwd()
target = 'Denver'
target_sold = f'{target}_sold'
sale_df = pd.DataFrame()
sold_df = pd.DataFrame()

def integrity_check():
    # Overall result, will be returned as an indicator or good integrity
    good = True
    print('Beginning integrity check')
    
    # Check for config file
    if os.path.isfile('config.json'):
        print('Config file good')
    else:
        print("Config file was not found\nCreating empty config file")
        config_default = json.dumps({"urls": {"target": ""}}, indent=4, sort_keys=False)
        
        with open('config.json', 'w') as f:
            result = f.write(config_default)
            result = bool(result)
                        
            if result:
                print('New config file created\nWarning: no data in config file')
                good = good and result
        
    # Check for folder for current target
    data_folder = f'.\\{target}'
    if os.path.isdir(data_folder):
        print('Target folder present')
    else:
        print('Target folder not found\nCreating new folder')
        result = os.makedirs(data_folder)
        good = good and bool(result)
        
    print('Checking data files')
    needed_files = 0
    os.chdir(data_folder)
    for filename in [f'{target}.txt', f'{target_sold}.txt', f'{target}_sale.csv', f'{target}_sold.csv']:
        if not os.path.isfile(f'.\\{filename}'):
            needed_files += 1
            print(f'Creating {filename}')
            with open(filename, 'w') as file:
                result = file.write('')
                good = good and bool(result)
                
    if needed_files == 0:
        print('Target folder setup complete, all files present')
    else:
        print(f'Target folder setup complete, {needed_files} files added')
        
    # End integrity check
    os.chdir(root_dir)
    if good:
        print("Integrity check complete, all files present")
    return(good)

def build_sequence(target, target_df):
    # Call a sequence of functions to extract wanted data from html
    
    # Get coordinates and add to df
    lats, longs = be.get_latLong(target)
    target_df['latitude'] = lats
    target_df['longitude'] = longs
    
    # Get prices
    prices = be.get_Price(target)
    target_df['price'] = prices
    
    # Get areas
    areas = be.get_Area(target)
    target_df['area'] = areas   
    
    # Add price/area column
    target_df['p/a'] = target_df['price']/target_df['area']

def main():
    # Main function
    # Calls backend functions
    
    # Add time column to database, so we can track when entries were added
    sale_df['time_run'] = dt.now()
    sold_df['time_run'] = dt.now()
    
    # Select url from config.json
    urls = be.get_url(target)
    
    # Download html and save as txt file
    be.get_html(urls, target)
    
    # Run build_sequence() to create data file
    build_sequence(target, sale_df)
    build_sequence(target_sold, sold_df)
    
    # Read any existing data file and add new data
    be.write_data(target, sale_df, sale=True)
    be.write_data(target, sold_df, sale=False)
    
    # Graph data
    be.graph_data(target)
        
if __name__ == '__main__':
    if integrity_check():
        main()
