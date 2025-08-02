from fredapi import Fred

fred = Fred(api_key='5c1fc41bfb9c4550f4d3eae5c5eddd10 ')
sofr = fred.get_series('SOFR')  # Daily SOFR time series
latest_sofr = sofr.iloc[-1]