import json, time, pandas
from decimal import Decimal

class Data:
    def __init__(self):
        # The json that holds all the user configured values
        self.config = {}
        # The amount of standard currency we have to buy with
        self.standardAmount = 0
        # The amount of cryptocurrency we have to sell
        self.cryptoAmount = 0
        # The number of buy orders we have completed by now
        self.numBuy = 0
        # The number of sell orders we have completed so far
        self.numSell = 0
        # The direction of the rate of change of the market's prices
        self.marketTrend = "Side"
        # The profit made from market trades
        self.marketProfitTotal = 0
        self.marketProfitsLastHour = 0
        # The profit made from BitMEX's fees for placing orders
        self.feeProfit = Decimal(str(0))

    def updateConfigs(self, webconfig):
        # Download JSON from website
        self.config = webconfig
        self.config['walletAmountCrypto'] = float(self.config['walletAmountCrypto'])
        self.config['minSpread'] = float(self.config['minSpread'])
        self.config['marketLowThreshold'] = float(self.config['marketLowThreshold'])
        self.config['marketHighThreshold'] = float(self.config['marketHighThreshold'])
        self.config['relistThreshold'] = float(self.config['relistThreshold'])
        self.config['aggressiveness'] = float(self.config['aggressiveness'])
        self.config['terminateTime'] = int(self.config['terminateTime'])
        self.config['lossyShutdown'] = (self.config['lossyShutdown'] == "True")
        print(webconfig)
        self.cryptoAmount = self.config["walletAmountCrypto"]
        #self.config["terminateTime"] = self.config["terminateTime"] + time.time()

    # TODO: calculate total profit for last hour every 15 mins
    def updateProfit(self, start, current):
        self.marketProfitTotal = current - start
        self.marketProfitsLastHour = current - self.marketProfitsLastHour

    def rateOfChange(self, asks):
        rates = pandas.Series(asks).pct_change()
        if not rates.empty:
            avgRate = rates.sum() / rates.size
            if avgRate > 0.02: #TEMP VALUE
                self.marketTrend = "High"
            if avgRate < -0.02: #TEMP VALUE
                self.marketTrend = "Low"
            else:
                self.marketTrend = "Side"