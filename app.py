import numpy as np
import pandas as pd
import yfinance as yf
import datetime
import json

from pandas_datareader import data as pdr
from flask import Flask, jsonify, request
from dateutil.relativedelta import relativedelta

# Initialze flask app
app = Flask(__name__)

# Fetching small, mid or large cap assets from yahoo finance
@app.route('/stocks', methods=['POST'])
def retrieve_assets():
    # Process stock details
    stocks = request.get_json()
    
    # Create list of symbols of specified category
    symbol = [d['Symbol'] for d in stocks]
    present_date = str(datetime.date.today())

    # Fetch yahoo finance data
    curr_data = pdr.get_data_yahoo(symbol, start = present_date)['Close']

    # Refetch if finance data for current date is not updated
    if curr_data.empty:
        past_date = str(datetime.date.today() + relativedelta(days=-1))
        curr_data = pdr.get_data_yahoo(symbol, start = past_date)['Close']
    if curr_data.empty:
        past_date = str(datetime.date.today() + relativedelta(days=-2))
        curr_data = pdr.get_data_yahoo(symbol, start = past_date)['Close']

    prices = []
    for d in stocks:
        if str(curr_data.iloc[-1][d['Symbol']]) == 'nan':
            try:
                if str(curr_data.iloc[-2][d['Symbol']]) != 'nan':
                    prices.append(round(curr_data.iloc[-2][d['Symbol']], 2))
                else:
                    p = pdr.get_data_yahoo(d['Symbol'], start = str(datetime.date.today() + relativedelta(months=-1)))['Close']
                    prices.append(round(p.iloc[-1], 2))
            except:
                p = pdr.get_data_yahoo(d['Symbol'], start = str(datetime.date.today() + relativedelta(months=-1)))['Close']
                prices.append(round(p.iloc[-1], 2))
        else:
            price = round(curr_data.iloc[-1][d['Symbol']], 2)
        prices.append(price)

    return jsonify(prices)

if __name__ == "__main__":
    app.run(debug=True)