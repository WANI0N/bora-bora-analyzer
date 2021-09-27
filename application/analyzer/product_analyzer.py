# return {'var_stdDev': 0.2748939189335891, 'var_perc': 44.337728860256306, 'min': False, 'max': 0.99, 'availability_perc': 100.0}
import math
from datetime import datetime, date, timedelta


class ProductAnalyzer:
    def __init__(self,data,dbUpdateDate = None):
        
        self.prices = list()
        self.dates = list()
        self.data = data
        
        self.activeCount = 0
        for o in data:
            self.dates.append(o['date'])
            self.prices.append(o['price'])
            if o['active']:
                self.activeCount += 1
            
        # current_date and dbUpdateDate might be the same
        now = datetime.now()
        self.current_date = now.strftime("%Y-%m-%d")
        self.dbUpdateDate = dbUpdateDate if dbUpdateDate else self.current_date
        d0 = date(int(self.dbUpdateDate[0:4]),int(self.dbUpdateDate[5:7]),int(self.dbUpdateDate[8:10]))
        d1 = date(int(self.dates[len(self.dates)-1][0:4]),int(self.dates[len(self.dates)-1][5:7]),int(self.dates[len(self.dates)-1][8:10]))
        # self.baseDate = d1
        delta = d0 - d1
        self.dayRange = (delta.days)+1
        
        self.getProductVariation()
        self.getProductAllTimePrice()
        self.getProductAvailability()
        self.getProductUniquePriceCount()
        
    def getResultsAsDict(self):
        return dict({
            "var_stdDev":self.var_stdDev,
            "var_perc":self.var_perc,
            "min":self.min,
            "max":self.max,
            "availability_perc":self.availability_perc,
            "unique_price_count":self.uniquePriceCount
        })

    def getDifferenceToMeanList(self):
        # self.getProductMean()
        returnArr = []
        # for o in self.pricesPadded:
        #     diff = o['price']-self.mean
        #     perc_diff = diff/self.mean*100
        #     returnArr.append({
        #         "perc_diff":perc_diff,
        #         "date":o['date']
        #     })
        # return returnArr
        for o in self.data:
            diff = o['price']-self.mean
            perc_diff = diff/self.mean*100
            returnArr.append({
                "perc_diff":perc_diff,
                "date":o['date']
            })
        return returnArr

    def getProductUniquePriceCount(self):
        self.uniquePriceCount = len( list(dict.fromkeys(self.prices)) )

    def getProductVariation(self):
        
        self.mean = round(sum(self.prices)/len(self.prices),2)
        deviation_sqr = [ (price - self.mean) ** 2 for price in self.prices ]
        variance = sum(deviation_sqr)/len(self.prices)
        stdDev = math.sqrt(variance)
        diff = abs(self.mean-stdDev)
        perc = diff/self.mean*100
        perc_diff = 100-perc
        self.var_stdDev = stdDev
        self.var_perc = perc_diff
        
    def getProductAllTimePrice(self):
        if (self.dates[0] != self.current_date) or (round(sum(self.prices),2) == round(self.prices[0]*len(self.prices),2)):
            self.min = False
            self.max = False
            return
        
        _min = min(self.prices)
        _max = max(self.prices)
        self.min = self.prices[0] if (self.prices[0] == _min) else False 
        self.max = self.prices[0] if (self.prices[0] == _max) else False
        
    def getProductAvailability(self):
        # d0 = date(int(self.dates[0][0:4]),int(self.dates[0][5:7]),int(self.dates[0][8:10]))
        # d0 = date(int(self.dbUpdateDate[0:4]),int(self.dbUpdateDate[5:7]),int(self.dbUpdateDate[8:10]))
        # d1 = date(int(self.dates[len(self.dates)-1][0:4]),int(self.dates[len(self.dates)-1][5:7]),int(self.dates[len(self.dates)-1][8:10]))
        # delta = d0 - d1
        self.availability_perc = self.activeCount/((self.dayRange)/100)
        # self.availability_perc = self.activeCount/(len(self.prices)/100)

if __name__ == "__main__":
    data = [
        {
            "price": 0.99,
            "comparative_unit_price": 0.99,
            "date": "2021-09-15",
            "active": True
        },
        {
            "price": 0.99,
            "comparative_unit_price": 0.49,
            "date": "2021-09-13",
            "active": True
        },
        {
            "price": 0.99,
            "comparative_unit_price": 0.49,
            "date": "2021-09-02",
            "active": True
        },
        {
            "price": 0.39,
            "comparative_unit_price": 0.49,
            "date": "2021-09-01",
            "active": True
        },
        {
            "price": 0.19,
            "comparative_unit_price": 0.49,
            "date": "2021-08-31",
            "active": True
        },
        {
            "price": 0.99,
            "comparative_unit_price": 0.49,
            "date": "2021-08-30",
            "active": True
        },
        {
            "price": 0.99,
            "comparative_unit_price": 0.49,
            "date": "2021-08-29",
            "active": True
        },
        {
            "price": 0.99,
            "comparative_unit_price": 0.49,
            "date": "2021-08-28",
            "active": True
        },
        {
            "price": 0.99,
            "comparative_unit_price": 0.49,
            "date": "2021-08-27",
            "active": True
        },
        {
            "price": 0.99,
            "comparative_unit_price": 0.99,
            "date": "2021-08-26",
            "active": True
        },
        {
            "price": 0.99,
            "comparative_unit_price": 0.99,
            "date": "2021-08-25",
            "active": True
        },
        {
            "price": 0.99,
            "comparative_unit_price": 0.49,
            "date": "2021-08-24",
            "active": True
        },
        {
            "price": 0.29,
            "comparative_unit_price": 0.19,
            "date": "2021-08-23",
            "active": True
        }
    ]
    
    item = ProductAnalyzer(data,"2021-09-15")
    results = item.getResultsAsDict()
    print(results)
    print( item.uniquePriceCount )
    # results = ProductAnalyzer(data,"2021-09-15").getProductMean()

    
    