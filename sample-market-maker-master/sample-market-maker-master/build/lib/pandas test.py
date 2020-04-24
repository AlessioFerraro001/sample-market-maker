import pandas as pd
prices = [30.4, 32.5, 31.7, 31.2, 32.7, 34.1, 35.8, 37.8, 36.3, 36.3, 35.6]

price_series = pd.Series(prices)
rates = price_series.pct_change()
print(rates.sum() / rates.size)
print(rates)