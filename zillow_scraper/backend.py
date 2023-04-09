# Backend functions called by main.py

import os
import time
import sys
import regex as re
import numbers
import json
import math

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
import seaborn as sb

sb.set_theme()
     
def get_url(target):
    try:
        with open('config.json', 'r') as f:
            url = json.load(f)
            sale_url = url['forSale_urls'][target]
            sold_url = url['sold_urls'][target]
            return((sale_url, sold_url))
    except KeyError:
        print('Target not found in config file')
    except FileNotFoundError:
        print('Config file not found')
    
    
def get_html(urls, target):
    # Download html, save to txt file
    req_headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.8',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
    }
    
    with requests.Session() as s:
        sale = s.get(urls[0], headers=req_headers)
        sold = s.get(urls[1], headers=req_headers)
        
    soup_sale = BeautifulSoup(sale.content, 'html.parser')
    soup_sold = BeautifulSoup(sold.content, 'html.parser')
        
    with open(f".\\{target}\\{target}.txt", "w") as target_data:
        print(soup_sale.encode('utf-8'), file=target_data)
    
    with open(f".\\{target}\\{target}_sold.txt", "w") as target_data:
        print(soup_sold.encode('utf-8'), file=target_data)
        
        
def get_lines(target_file, coarse_string, fine_string, end_string, offset):
    myfile = open(f'.\\{target_file.split("_")[0]}\\{target_file}.txt')
    contents = myfile.read()
    myfile.close()
    
    locs = []
    begInd = 0
    while contents.find(coarse_string, begInd) >= 0:
        begInd = contents.find(coarse_string, begInd) + 1
        locs.append(begInd - 1)
        
    lines = []
    for i in locs:
        lines.append(contents[i:i+100])
        
    output = []
    for i in lines:
        line_begin = i.find(fine_string) + offset
        line_end = i.find(end_string, line_begin)
        output.append(i[line_begin:line_end])
        
    return(output)
    
def get_latLong(target):
    
    lats = get_lines(target, 'latLong', 'latitude', ',', 10)
    lats = [float(i) for i in lats]
    
    longs = get_lines(target, 'latLong', 'longitude', '}', 11)
    longs = [float(i) for i in longs]
    
    return([lats,longs])
    
def get_Price(target):
    
    lines = get_lines(target, 'unformattedPrice', 'unformattedPrice', ',', 18)
    lines = [int(i) for i in lines]
    
    return(lines)
    
def get_Area(target):
    
    areas = get_lines(target, 'livingArea', 'livingArea', ',', 12)
    areas = [float(i) for i in areas]
    
    return(areas)
    
def write_data(target, df, sale=True):
    # Load from any existing data file
    filename = f'.\\{target}\\{target}_{"sale" if sale else "sold"}.csv'
    
    try:
        old_data = pd.read_csv(filename)
    except FileNotFoundError:
        old_data = pd.DataFrame()
        
    # Add new data, overwriting any matching lat/long combination
    data = pd.concat([old_data, df], ignore_index=True)
    data = data.drop_duplicates( subset = ['latitude', 'longitude'], keep = 'last').reset_index( drop = True )
    
    # Write data to file
    data.to_csv(filename, index=False, mode='w')
    
    
def build_data(target, key, sale=True):
    # Build data file to graph from
    # Raw lat/long data has to be sorted into bins, values have to be averaged or something
    # Need to create a new dataframe wth indices latitudes to 0.01, columns longitudes to 0.01
    # Sort sale_df / sold_df into latbins and longbins using https://stackoverflow.com/questions/39254704/pandas-group-bins-of-data-per-longitude-latitude
    
    df = pd.read_csv(f'.\\{target}\\{target}_{"sale" if sale else "sold"}.csv')
    
    # Find limits for lat/long
    step = 0.01
    
    max_lat = max(df['latitude'])
    max_lat = math.ceil(max_lat / 0.01) * 0.01
    
    min_lat = min(df['latitude'])
    min_lat = math.floor(min_lat / 0.01) * 0.01
    
    max_long = max(df['longitude'])
    max_long = math.ceil(max_long / 0.01) * 0.01
    
    min_long = min(df['longitude'])
    min_long = math.floor(min_long / 0.01) * 0.01
    
    min_lat = round(min_lat, 2)
    max_lat = round(max_lat, 2)
    min_long = round(min_long, 2)
    max_long = round(max_long, 2)
    
    n_lat_bins = int(abs((max_lat - min_lat)/step))
    n_long_bins = int(abs((max_long - min_long)/step))
    
    print(f'min lat: {min_lat}, max_lat: {max_lat}, lat steps: {n_lat_bins}')
    print(f'min long: {min_long}, max_long: {max_long}, long steps: {n_long_bins}')
    
    latRange = np.linspace(min_lat, max_lat, num=n_lat_bins+2)
    latRange = [round(i,2) for i in latRange]
    longRange = np.linspace(min_long, max_long, num=n_long_bins+1)
    longRange = [round(i,2) for i in longRange]
    
    init_data = np.zeros((len(latRange),len(longRange)))
    graph_data = pd.DataFrame(data=init_data, index=latRange, columns=longRange)
      
    
    # Sort data and insert into graph_data
    to_bin = lambda x: np.floor(x / step) * step
    df["latBin"] = round(to_bin(df['latitude']), 2)
    df["longBin"] = round(to_bin(df['longitude']), 2)
    groups = df.groupby(["latBin", "longBin"])
    
    for i in df.index:
        x = df.at[i, 'latBin']
        y = df.at[i, 'longBin']
        z = df.at[i, 'price']
        graph_data.at[x, y] = z
        
    print(df)
    return(graph_data)
    # Need to average values for repeat latbin/longbin
    
def graph_data(target):
    # Plot data in subplots
    # First try: plot sale price, sale price/area, sold price, sold price/area
    fig, ((ax1,ax2),(ax3,ax4)) = plt.subplots(2,2)
    
    # ax1: sale price
    ax1.set_title('For Sale Price')
    data = build_data(target, 'price')
    sb.heatmap(data, ax=ax1)
    
    # ax2: sold price
    ax2.set_title('Sold Price')
    data = build_data(target, 'price', sale=False)
    sb.heatmap(data, ax=ax2)
    
    # ax3: sale p/a
    ax3.set_title('For Sale Price/Area')
    data = build_data(target, 'p/a')
    sb.heatmap(data, ax=ax3)
    
    # ax4: sold p/a
    ax4.set_title('Sold Price/Area')
    data = build_data(target, 'p/a', sale=False)
    sb.heatmap(data, ax=ax4)
    
    plt.show()
    
# Test functions
if __name__ == '__main__':
    ''' Test integrity_check and get_url
    if integrity_check():
        url = get_url('Denver')
        print(url)
    '''
    
    # Test get_latLong
    print(get_latLong('Denver'))