from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List,Dict
import string

class Trader:
    def __init__(self):
        self.resin_strategy = FixedProductStrategy("RAINFOREST_RESIN",50,10_000)
        self.ink_kelp_strategy = MeanReversionStrategy("SQUID_INK",50,"KELP") 
        self.kelp_strategy = Strategy("KELP",50)

    def run(self, state: TradingState) -> Dict[str, list[Order]]:
        """
        Takes all buy and sell orders for all symbols as input,
        and outputs a list of orders to be sent.
        """
        result = {}

        for product in state.order_depths.keys():
            order_depth: OrderDepth = state.order_depths[product]
            self.orders: list[Order] = []
            
            if product == "RAINFOREST_RESIN":
                self.orders = self.resin_strategy.trade(state)

            elif product == "SQUID_INK":
                self.ink_kelp_strategy.trade(state)

            elif product == "KELP":
                #self.kelp_strategy.trade(state)
                continue
            
            result[product] = self.orders

        traderData = "SAMPLE"
        conversions = 1
        return result, conversions, traderData


class Strategy:
    def __init__(self, product: str, limit: int) -> None:
        self.product = product
        self.limit = limit
        self.orders = []

    def buy(self, price: int, quantity: int) -> None:
        self.orders.append(Order(self.product, price, quantity))

    def sell(self, price: int, quantity: int) -> None:
        self.orders.append(Order(self.product, price, -quantity))

class MeanReversionStrategy(Strategy): 
    def __init__(self, product: str, limit: int, mr_product: str) -> None:
        super().__init__(product, limit)

class FixedProductStrategy(Strategy):
    def __init__(self, product: str, limit: int, stable_price: float) -> None:
        super().__init__(product, limit)
        self.stable_price = stable_price

    def trade(self, state: TradingState) -> list[Order]:

        order_depth = state.order_depths[self.product]
        position = state.position.get(self.product, 0)

        print('position:',position)
        sorted_buys = sorted(order_depth.buy_orders.items(), key=lambda x: x[0], reverse=True)
        sorted_sells = sorted(order_depth.sell_orders.items(), key=lambda x: x[0])
        buy_list = [[p, v] for p, v in sorted_buys]
        sell_list = [[p, v] for p, v in sorted_sells]

        print(buy_list,sell_list)
        i, j = 0, 0
        while i < len(buy_list) and j < len(sell_list):
            buy_price, buy_vol = buy_list[i]
            sell_price, sell_vol = sell_list[j]

            print('buy_price',buy_price)
            print('sell_price',sell_price)

            if buy_price <= self.stable_price: 
                i+=1 
                continue
            if sell_price >= self.stable_price: 
                j+=1 
                continue
          

            if buy_price >= sell_price:
                print('found pair: ',buy_price,sell_price)
                matched_vol = min(buy_vol, abs(sell_vol))

                self.sell(buy_price,matched_vol)
                self.buy(sell_price,matched_vol)
              
                buy_list[i][1] -= matched_vol
                sell_list[j][1] += matched_vol

                if buy_list[i][1] <= 0:
                    i += 1
                if sell_list[j][1] >= 0:
                    j += 1
            else:
                continue

        for price, vol in buy_list:
            # SELL outstanding positions

            print('sell',position,price)
            allowable_sell = position + self.limit

            if allowable_sell <= 0 or price <= self.stable_price:
                break

            fill_vol = min(abs(vol), allowable_sell)
          
            position -= fill_vol
            self.sell(price,fill_vol)

        for price, vol in sell_list:
            # BUY outstanding positions

            print('buy',position,price)
            allowable_buy = self.limit - position

            if allowable_buy <= 0 or price >= self.stable_price:
                break

            fill_vol = min(abs(vol), allowable_buy)

            position += fill_vol
            self.buy(price,fill_vol)
    
        return self.orders

                
                

            


