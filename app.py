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

    if len(investments) > 0:
        # Fetching records of last 5 years
        start = str(datetime.date.today() + relativedelta(years=-5))

        # Add all user investments
        for inv in investments:
            if inv['Quantity'] > 0:
                inv_details['symbol'].append(inv['Symbol'])
                inv_details['types'].append(inv['Type'])
        
        # Add two global assets
        inv_details['symbol'].append('^NSEI')
        inv_details['symbol'].append('^BSESN')

        curr_data = pdr.get_data_yahoo(inv_details['symbol'], start = start)['Close']
        for inv in investments:
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
            inv_details['beta'].append(beta)
            inv_details['price'].append(price)

        # Add details into return variable
        for i in range(len(investments)):
            if investments[i]['Quantity'] > 0:
                p = inv_details['price'][i]
                inv_details['percent_change'].append(round((1 - investments[i]['buyPrice']/p)*100, 2))
                inv_details['net_pl'] += p * investments[i]['Quantity']
                da = investments[i]['Date'][:10].split("-")     # Date format = 2021-01-24 
                date = f"{da[2]}-{da[1]}-{da[0]}"
                inv_details['date'].append(date)
                inv_details['total'] += investments[i]['buyPrice'] * investments[i]['Quantity']
        inv_details['total_inv'] = inv_details['total']
        returns = user_data['Returns']
        if len(returns) > 0:
            for r in returns:
                inv_details['total_inv'] += r['buyPrice'] * r['Quantity']
        inv_details['roi'] = round(((inv_details['net_pl']-inv_details['total'])/inv_details['total'])*100, 2)
        inv_details['cagr'] = round(((inv_details['net_pl']/inv_details['total'])**(1/5)-1)*100, 2)

        # Setting completion as true
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

            # Add net pl
            ret_details['net_pl'] += r['Quantity'] * (r['sellPrice'] - r['buyPrice'])
        ret_details['success'] = True
        return ret_details
    else:
        return ret_details

# @app.route("/portfolio", methods = ['POST'])
# def portfolio():
#     invs = db.execute("SELECT * FROM investment WHERE username = :username", {"username": username}).fetchall()
#     if len(invs) > 0:
#         category = []
#         assets = []
#         symbols = []
#         for i in invs:
#             a = db.execute("SELECT * FROM assets WHERE name = :name", {"name": i.asset}).fetchall()[0]
#             category.append(a.type)
#             if i.asset not in assets:
#                 assets.append(i.asset)
#                 symbols.append(a.symbol)
#         fig = plt.figure(figsize = (12, 6))
#         d = dict(Counter(category))
#         plt.pie(d.values(), labels = d.keys(), autopct = '%1.1f%%')
#         img = BytesIO()
#         fig.savefig(img, format = 'png', bbox_inches = 'tight')
#         img.seek(0)
#         encoded_pc = b64encode(img.getvalue())
#         plt.close(fig)

#         curr_data = pdr.get_data_yahoo(symbols, start = "2020-01-01")['Adj Close']
#         # if there's only one symbol then curr_data is a series not dataframe, & series does not have columns attribute
#         if len(symbols) == 1:
#             curr_data = pd.DataFrame(curr_data)
#         stock_graphs = []
#         count = 0
#         for c in curr_data.columns:
#             fig1 = plt.figure(figsize = (12, 6))
#             plt.plot(curr_data[c], c = np.random.rand(3,))
#             plt.xlabel('DATE')
#             plt.ylabel('PRICE')
#             plt.title(assets[count].upper())
#             #plt.fill_between(curr_data.index, curr_data[c])
#             plt.grid()
#             img1 = BytesIO()
#             fig1.savefig(img1, format = 'png', bbox_inches = 'tight')
#             img1.seek(0)
#             encoded_graph = b64encode(img1.getvalue())
#             stock_graphs.append(encoded_graph.decode('utf-8'))
#             count += 1
#             plt.close(fig1)
#         db.close()
#         return render_template("portfolio.html", curruser = username, investments = 'True', pie_chart = encoded_pc.decode('utf-8'), stock_graphs = stock_graphs)
#     else:
#         db.close()
#         return render_template("portfolio.html", curruser = username, investments = 'False')

if __name__ == "__main__":
    app.run(debug=True)