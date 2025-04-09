from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List,Dict
import string
from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import numpy as np

class Trader:
    def __init__(self):
        self.resin_strategy = FixedProductStrategy("RAINFOREST_RESIN", 50, 10_000)
        self.ink_strategy = SimpleSpreadStrategy("SQUID_INK", 50, spread=1)
        self.kelp_strategy = SimpleSpreadStrategy("KELP", 50, spread=1)

    def run(self, state: TradingState) -> Dict[str, list[Order]]:
        result = {}

        # Fixed strategy for RAINFOREST_RESIN
        if "RAINFOREST_RESIN" in state.order_depths:
            result["RAINFOREST_RESIN"] = self.resin_strategy.trade(state)

        # Simple spread strategy for SQUID_INK
        if "SQUID_INK" in state.order_depths:
            result["SQUID_INK"] = self.ink_strategy.trade(state)

        # Simple spread strategy for KELP
        if "KELP" in state.order_depths:
            result["KELP"] = self.kelp_strategy.trade(state)

        traderData = "SAMPLE"
        conversions = 1
        return result, conversions, traderData

class Strategy:
    def __init__(self, product: str, limit: int) -> None:
        self.product = product
        self.limit = limit
        self.orders: List[Order] = []

    def buy(self, price: int, quantity: int) -> None:
        self.orders.append(Order(self.product, price, quantity))

    def sell(self, price: int, quantity: int) -> None:
        self.orders.append(Order(self.product, price, -quantity))

class FixedProductStrategy(Strategy):
    def __init__(self, product: str, limit: int, stable_price: float) -> None:
        super().__init__(product, limit)
        self.stable_price = stable_price

    def trade(self, state: TradingState) -> list[Order]:
        self.orders = []
        order_depth = state.order_depths[self.product]
        position = state.position.get(self.product, 0)

        sorted_buys = sorted(order_depth.buy_orders.items(), key=lambda x: x[0], reverse=True)
        sorted_sells = sorted(order_depth.sell_orders.items(), key=lambda x: x[0])
        buy_list = [[p, v] for p, v in sorted_buys]
        sell_list = [[p, v] for p, v in sorted_sells]

        i, j = 0, 0
        while i < len(buy_list) and j < len(sell_list):
            buy_price, buy_vol = buy_list[i]
            sell_price, sell_vol = sell_list[j]

            if buy_price <= self.stable_price:
                i += 1
                continue
            if sell_price >= self.stable_price:
                j += 1
                continue

            if buy_price >= sell_price:
                matched_vol = min(buy_vol, abs(sell_vol))
                self.sell(buy_price, matched_vol)
                self.buy(sell_price, matched_vol)
                buy_list[i][1] -= matched_vol
                sell_list[j][1] += matched_vol

                if buy_list[i][1] <= 0:
                    i += 1
                if sell_list[j][1] >= 0:
                    j += 1
            else:
                break

        for price, vol in buy_list:
            allowable_sell = position + self.limit
            if allowable_sell <= 0 or price <= self.stable_price:
                break
            fill_vol = min(abs(vol), allowable_sell)
            position -= fill_vol
            self.sell(price, fill_vol)

        for price, vol in sell_list:
            allowable_buy = self.limit - position
            if allowable_buy <= 0 or price >= self.stable_price:
                break
            fill_vol = min(abs(vol), allowable_buy)
            position += fill_vol
            self.buy(price, fill_vol)

        return self.orders

class SimpleSpreadStrategy(Strategy):
    def __init__(self, product: str, limit: int, spread: int = 1) -> None:
        super().__init__(product, limit)
        self.spread = spread

    def trade(self, state: TradingState) -> list[Order]:
        self.orders = []
        order_depth = state.order_depths[self.product]

        if order_depth.buy_orders and order_depth.sell_orders:
            best_bid = max(order_depth.buy_orders.keys(), default=0)
            best_ask = min(order_depth.sell_orders.keys(), default=0)

            best_bid_volume = order_depth.buy_orders[best_bid]
            best_ask_volume = order_depth.sell_orders[best_ask]

            mid_price = (best_bid + best_ask) / 2

            buy_price = int(mid_price - self.spread)
            sell_price = int(mid_price + self.spread)

            self.buy(buy_price, best_ask_volume)
            self.sell(sell_price, best_bid_volume)

        return self.orders

# class Trader:
#     def __init__(self):
#         self.resin_strategy = FixedProductStrategy("RAINFOREST_RESIN", 50, 10_000)
#         self.ink_kelp_strategy = PairTradingStrategy("SQUID_INK", 50, "KELP", lag=680, coef=-1.0)
#         self.kelp_strategy = Strategy("KELP", 50)

#     def run(self, state: TradingState) -> Dict[str, list[Order]]:
#         result = {}

#         # Fixed Product Strategy
#         if "RAINFOREST_RESIN" in state.order_depths.keys():
#             resin_orders = self.resin_strategy.trade(state)
#             result["RAINFOREST_RESIN"] = resin_orders

#         # Pair Strategy: KELP (based on SQUID_INK)
#         if "SQUID_INK" in state.order_depths.keys() and "KELP" in state.order_depths.keys():
#             pair_orders = self.ink_kelp_strategy.trade(state)

#             # Add orders for product2 (KELP) into result
#             if pair_orders:
#                 result["KELP"] = pair_orders

#         traderData = "SAMPLE"
#         conversions = 1
#         return result, conversions, traderData

# class Strategy:
#     def __init__(self, product: str, limit: int) -> None:
#         self.product = product
#         self.limit = limit
#         self.orders = []

#     def buy(self, price: int, quantity: int) -> None:
#         self.orders.append(Order(self.product, price, quantity))

#     def sell(self, price: int, quantity: int) -> None:
#         self.orders.append(Order(self.product, price, -quantity))

# class PairTradingStrategy(Strategy): 
#     def __init__(self, product1: str, limit: int, product2: str, lag: int, coef: float) -> None:
#         super().__init__(product2, limit)  # base class uses product2, the one we trade
#         self.signal_product = product1
#         self.lag = lag 
#         self.coef = coef 
#         self.history1 = []
#         self.history2 = []

#     def trade(self, state: TradingState) -> list[Order]:
#         self.orders = []

#         def midprice(order_depth: OrderDepth):
#             if order_depth.buy_orders and order_depth.sell_orders:
#                 return (max(order_depth.buy_orders) + min(order_depth.sell_orders)) / 2
#             return None

#         # Get order depths
#         od1 = state.order_depths[self.signal_product]
#         od2 = state.order_depths[self.product]

#         mid1 = midprice(od1)
#         mid2 = midprice(od2)

#         if mid1 is None or mid2 is None:
#             return []

#         self.history1.append(mid1)
#         self.history2.append(mid2)

#         if len(self.history1) <= self.lag or len(self.history2) <= 1:
#             return []

#         # Returns
#         ret1_lagged = (self.history1[-self.lag] - self.history1[-self.lag - 1]) / self.history1[-self.lag - 1]
#         ret2 = (self.history2[-1] - self.history2[-2]) / self.history2[-2]

#         spread = self.coef * ret1_lagged + ret2
#         position = state.position.get(self.product, 0)
#         threshold = 0.001  # to avoid noise-triggered trades

#         if spread > threshold:
#             # Expect spread to fall -> short product2 (kelp)
#             best_bid = max(od2.buy_orders.keys(), default=None)
#             if best_bid:
#                 vol = min(self.limit + position, od2.buy_orders[best_bid])
#                 if vol > 0:
#                     self.sell(best_bid, vol)

#         elif spread < -threshold:
#             # Expect spread to rise -> long product2 (kelp)
#             best_ask = min(od2.sell_orders.keys(), default=None)
#             if best_ask:
#                 vol = min(self.limit - position, -od2.sell_orders[best_ask])
#                 if vol > 0:
#                     self.buy(best_ask, vol)

#         return self.orders


# class FixedProductStrategy(Strategy):
#     def __init__(self, product: str, limit: int, stable_price: float) -> None:
#         super().__init__(product, limit)
#         self.stable_price = stable_price

#     def trade(self, state: TradingState) -> list[Order]:

#         order_depth = state.order_depths[self.product]
#         position = state.position.get(self.product, 0)

#         print('position:',position)
#         sorted_buys = sorted(order_depth.buy_orders.items(), key=lambda x: x[0], reverse=True)
#         sorted_sells = sorted(order_depth.sell_orders.items(), key=lambda x: x[0])
#         buy_list = [[p, v] for p, v in sorted_buys]
#         sell_list = [[p, v] for p, v in sorted_sells]

#         print(buy_list,sell_list)
#         i, j = 0, 0
#         while i < len(buy_list) and j < len(sell_list):
#             buy_price, buy_vol = buy_list[i]
#             sell_price, sell_vol = sell_list[j]

#             print('buy_price',buy_price)
#             print('sell_price',sell_price)

#             if buy_price <= self.stable_price: 
#                 i+=1 
#                 continue
#             if sell_price >= self.stable_price: 
#                 j+=1 
#                 continue
          

#             if buy_price >= sell_price:
#                 print('found pair: ',buy_price,sell_price)
#                 matched_vol = min(buy_vol, abs(sell_vol))

#                 self.sell(buy_price,matched_vol)
#                 self.buy(sell_price,matched_vol)
              
#                 buy_list[i][1] -= matched_vol
#                 sell_list[j][1] += matched_vol

#                 if buy_list[i][1] <= 0:
#                     i += 1
#                 if sell_list[j][1] >= 0:
#                     j += 1
#             else:
#                 continue

#         for price, vol in buy_list:
#             # SELL outstanding positions

#             print('sell',position,price)
#             allowable_sell = position + self.limit

#             if allowable_sell <= 0 or price <= self.stable_price:
#                 break

#             fill_vol = min(abs(vol), allowable_sell)
          
#             position -= fill_vol
#             self.sell(price,fill_vol)

#         for price, vol in sell_list:
#             # BUY outstanding positions

#             print('buy',position,price)
#             allowable_buy = self.limit - position

#             if allowable_buy <= 0 or price >= self.stable_price:
#                 break

#             fill_vol = min(abs(vol), allowable_buy)

#             position += fill_vol
#             self.buy(price,fill_vol)
    
#         return self.orders

                
                

            


