import numpy as np
import pandas as pd
import yfinance as yf
import datetime
import json
import math

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
    
    try:
        # Fetch yahoo finance data
        curr_data = pdr.get_data_yahoo(symbol, start = present_date)['Close']
    except:
        # Refetch if finance data for current date is not updated
        past_date = str(datetime.date.today() + relativedelta(days=-1))
        curr_data = pdr.get_data_yahoo(symbol, start = past_date)['Close']

        if curr_data.empty:
            past_date = str(datetime.date.today() + relativedelta(days=-2))
            curr_data = pdr.get_data_yahoo(symbol, start = past_date)['Close']

    prices = []
    for d in stocks:
        # handle nan values
        # push the prices of stocks
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

#####                                                                                                 #####
    ###################################################################################################
    #                                                                                                 #
    #             (https://github.com/astonizer/investment-planner) specific routes below             # 
    #                                                                                                 #
    ###################################################################################################
#####                                                                                                 #####

# Analysing investments by user
@app.route("/investment", methods = ['POST'])
def investments():
    # Process user investments
    user_data = request.get_json()    # stock symbols
    investments = user_data['Investments']

    # Ininitialize return object
    inv_details = {
        'date': [],
        'price': [],
        'types': [],
        'percent_change': [],
        'net_pl': 0,
        'total': 0,
        'total_inv': 0,
        'symbol': [],
        'beta': [],
        'cagr': [],
        'roi': [],
        'success': False
    }

    # store symbol for ones with zero quantity for better error handling
    nonZeroQuantityIndexes=[]
    id=0

    if len(investments) > 0:
        # Fetching records of last 5 years
        start = str(datetime.date.today() + relativedelta(years=-5))

        # Add all user investments
        for inv in investments:
            inv_details['symbol'].append(inv['Symbol'])
            inv_details['types'].append(inv['Type'])
            
            # add the indexes for assets having non-zero quantity
            if inv['Quantity'] > 0:
                nonZeroQuantityIndexes.append(id)
            id+=1
        
        # Add two global assets
        inv_details['symbol'].append('^NSEI')
        inv_details['symbol'].append('^BSESN')

        curr_data = pdr.get_data_yahoo(inv_details['symbol'], start = start)['Close']
        for inv in investments:
            # handle nan values
            inv_symbol = inv['Symbol']
            if str(curr_data.iloc[-1][inv_symbol]) == 'nan':
                price = round(curr_data.iloc[-2][inv_symbol], 2)
            else:
                price = round(curr_data.iloc[-1][inv_symbol], 2)
            
            if inv_symbol[-2:] == 'BO':
                index = '^BSESN'
            else:
                index = '^NSEI'
                
            # Compute covariance, beta and percent change
            data = curr_data[[inv_symbol, index]]
            returns = data.pct_change()
            cov = returns.cov()
            covar = cov[inv_symbol].iloc[1]
            var = cov[index].iloc[1]
            beta = round(covar/var, 2)

            # push the results in return object
            inv_details['beta'].append(beta)
            inv_details['price'].append(price)

        # Add important details into return variable
        for i in range(len(investments)):
            p = inv_details['price'][i]
            inv_details['percent_change'].append(round((1 - investments[i]['buyPrice']/p)*100, 2))
            if(i in nonZeroQuantityIndexes):
                inv_details['net_pl'] += p * investments[i]['Quantity']
                inv_details['total'] += investments[i]['buyPrice'] * investments[i]['Quantity']
            
            # date format be YYYY/MM/DD
            da = investments[i]['Date'][:10].split("-")
            date = f"{da[2]}-{da[1]}-{da[0]}"
            inv_details['date'].append(date)

        inv_details['total_inv'] = inv_details['total']
        returns = user_data['Returns']
        if len(returns) > 0:
            for r in returns:
                inv_details['total_inv'] += r['buyPrice'] * r['Quantity']
        inv_details['roi'] = round(((inv_details['net_pl']-inv_details['total'])/inv_details['total'])*100, 2)
        inv_details['cagr'] = round(((inv_details['net_pl']/inv_details['total'])**(1/5)-1)*100, 2)
        inv_details['net_pl'] = round(inv_details['net_pl'], 2)
        inv_details['total'] = round(inv_details['total'], 2)
        inv_details['total_inv'] = round(inv_details['total_inv'], 2)

        # check for possible infinity values
        if(math.isnan(inv_details['roi'])):
            inv_details['roi'] = 0.00
        if(math.isnan(inv_details['cagr'])):
            inv_details['cagr'] = 0.00

        # mark the completion
        inv_details['success'] = True
        return jsonify(inv_details)
    else:
        return jsonify(inv_details)
        
# Analysing returns of user
@app.route("/return", methods = ['POST'])
def returns():
    # Process invoming json data
    returnsData = request.get_json()
    returns = returnsData['Returns']

    # Initialize return variable
    ret_details = {
        'percent_change': [],
        'net_pl': 0,
        'success': False
    }

    if(len(returns)):
        for r in returns:
            # Calculate percent change
            ret_details['percent_change'].append(round((1 - r['buyPrice']/r['sellPrice'])*100, 2))

            # Adding net pl
            ret_details['net_pl'] += r['Quantity'] * (r['sellPrice'] - r['buyPrice'])

        # mark the completion
        ret_details['success'] = True
        return ret_details
    else:
        return ret_details

if __name__ == "__main__":
    app.run(debug=True)