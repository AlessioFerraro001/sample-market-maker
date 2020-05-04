import requests
from bs4 import BeautifulSoup

class CoinMarketCap:
    def __init__(self):
        self.uml = 'https://coinmarketcap.com/all/views/all/'

    def getPrice(self, config):
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
        print(coins)