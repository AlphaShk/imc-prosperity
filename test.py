from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List,Dict
import string

class Trader:
    def __init__(self):
        # Initialize trade tracking variables
        self.entered_trade = False
        self.current_position = 0  # Track our current position
        self.price_history_squid_ink = []  # To store historical prices for SQUID_INK
        self.price_history_kelp = []  # To store historical prices for KELP
        
        # Track previous MA values for crossover detection for both products
        self.prev_fast_ma_squid_ink = None
        self.prev_slow_ma_squid_ink = None
        self.prev_fast_ma_kelp = None
        self.prev_slow_ma_kelp = None

        self.orders: list[Order] = []


    # def trade_stable(self, product: str,order_depth: OrderDepth): 
    #     # Simple price check logic remains the same
    #     best_bid = max(order_depth.buy_orders.keys(), default=0)
    #     best_ask = min(order_depth.sell_orders.keys(), default=0)
        
    #     if len(order_depth.buy_orders) != 0:
    #         best_bid = max(order_depth.buy_orders.keys())
    #         best_bid_volume = order_depth.buy_orders[best_bid] * 2
    #         if best_bid > 10000:
    #             print("SELL", str(best_bid_volume) + "x", best_bid)
    #             self.orders.append(Order(product, best_bid, -best_bid_volume))

    #     if len(order_depth.sell_orders) != 0:
    #         best_ask = min(order_depth.sell_orders.keys())
    #         best_ask_volume = order_depth.sell_orders[best_ask] * 2
    #         if best_ask < 10000:
    #             print("BUY", str(-best_ask_volume) + "x", best_ask)
    #             self.orders.append(Order(product, best_ask, -best_ask_volume))
        
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
              # self.trade_stable(product,order_depth)
              strat = FixedProductStrategy(product,50,10_000)
              self.orders = strat.trade(state)
              print(self.orders)

            elif product == "SQUID_INK":
              continue

            elif product == "KELP":
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

                
                

            


