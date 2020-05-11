import requests
from bs4 import BeautifulSoup
from decimal import Decimal

class CoinMarketCap:
    def __init__(self):
        self.uml = 'https://coinmarketcap.com/all/views/all/'

    def getPrice(self, coinName):
        page = requests.get(self.uml)
        soup = BeautifulSoup(page.content, 'lxml')
        coins = []
        table = soup.find('tbody')

        for tr in table.find_all('tr'):
            coin = {}
            name_tag = tr.find('a')
            coin['name'] = name_tag.next_element
            price_tag = name_tag.find_next('a')
            coin['price'] = price_tag.next_element
            coins.append(coin)
        for coin in coins:
            if coin["name"] == coinName:
                cleanedCoin = self.cleanCoin(coin["price"])
                print(cleanedCoin)
                return float(cleanedCoin)
        return None

    def cleanCoin(self, dirtyCoin):
        temp = dirtyCoin[1:].split(",")
        clean = ""
        for piece in temp:
            clean += piece
        return clean

    def getCoin(self, symbol):
        if symbol == "XBTUSD" or "XBTJPY":
            return "Bitcoin"
        elif symbol == "ADAM20":
            return "Cardano"
        elif symbol == "BCHM20":
            return "Bitcoin Cash"
        elif symbol == "EOSM20":
            return "EOS"
        elif symbol == "ETHXBT":
            return "Ethereum"
        elif symbol == "LTCM20":
            return "Litecoin"
        elif symbol == "TRXM20":
            return "Tron"
        elif symbol == "XRPUSD":
            return "XRP"
        else:
            return None