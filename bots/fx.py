from base import *


class FXBot(BaseBot):

    # If you want to keep track of any information in
    # addition to that stored in BaseBot, feel free to
    # update this init function as necessary.
    def __init__(self):
        super(FXBot, self).__init__()
        self.order_books = {}

    # An example market making strategy.
    # Returns the orders the bots should execute.
    def penny(self):
        tickers = self.order_books.keys()
        orders = []
        for ticker in tickers: 
            orderbook = self.order_books[ticker]
            
            if len(orderbook.bids) == 0 or len(orderbook.offers) == 0:
                print "LENGTH 0 ORDERBOOKS"
                return []
            else:
                offer = orderbook.bestBid()
                bid = orderbook.bestOffer()
                print (offer.p, bid.p)
                if (offer.p  - bid.p) > 0: #(order-1)-(bid+1)
                    #pennyable 
                    print "IM IN!"
                    orderbuy = {'ticker' : ticker, 'buy': True, 'quantity': 100, 'price': bid.p+0.01}
                    ordersell = {'ticker' : ticker, 'buy': False, 'quantity': 100, 'price': offer.p-0.01}
                    orders.append(orderbuy)
                    orders.append(ordersell)
                    print "IN THE PENNY FUNCTION"
                    print orders
        return orders


        # ORDERS IS A LIST, CONTAINING DICTIONARIES OF THE FORM BELOW
        return 0

    def scale(self):
        return 0

    def take(self):
        return 0
        
    # def marketMake(self):
    #     orders = []

    #     for ticker, position in self.positions.iteritems():
    #         lastPrice = self.lastPrices[ticker]

    #         if abs(position) > self.options.get('position_limit'):
    #             orders.append({
    #                 'ticker': ticker,
    #                 'buy': position < 0,
    #                 'quantity': abs(position),
    #                 'price': lastPrice * (1.5 if position < 0 else 0.5),
    #             })
    #         else:
    #             if ticker in self.topBid:
    #                 orders.append({
    #                     'ticker': ticker,
    #                     'buy': True,
    #                     'quantity': self.options.get('order_quantity'),
    #                     'price': self.topBid[ticker] + 0.01,
    #                 })
    #             if ticker in self.topAsk:
    #                 orders.append({
    #                     'ticker': ticker,
    #                     'buy': False,
    #                     'quantity': self.options.get('order_quantity'),
    #                     'price': self.topAsk[ticker] - 0.01,
    #                 })
    #     return orders


    # # An example momentum strategy.
    # # Returns the orders the bot should execute.
    # def momentum(self):
    #     orders = []

    #     enter_threshold = self.options.get('enter_threshold')
    #     for ticker, change in self.priceChange.iteritems():
    #         lastPrice = self.lastPrices[ticker]
    #         if change > enter_threshold:
    #             orders.append({
    #                 'ticker': ticker,
    #                 'buy': True,
    #                 'quantity': 100,
    #                 'price': lastPrice * 1.5,
    #             })
    #         elif change < -enter_threshold:
    #             orders.append({
    #                 'ticker': ticker,
    #                 'buy': False,
    #                 'quantity': 100,
    #                 'price': lastPrice * .5,
    #             })

    #     return orders

    # Updates the bot's internal state according
    # to trader and market updates from the server.
    # Feel free to modify this method according to how
    # you want to keep track of your internal state.
    def update_state(self, msg):
        super(FXBot, self).update_state(msg)

    def fx_update_state(self, msg):
           # Update internal books for each ticker
        if msg.get('market_states'):
            for ticker, state in msg['market_states'].iteritems():
                self.order_books[ticker] = OrderBook(state['bids'], state['asks'])

        # Update internal book for a single ticker
        if msg.get('market_state'):
            state = msg['market_state']
            ticker = state['ticker']
            self.order_books[ticker] = OrderBook(state['bids'], state['asks'])    
    # Overrides the BaseBot process function.
    # Modify this function if you want your bot to
    # execute a strategy.
    def process(self, msg):
        super(FXBot, self).process(msg)
        if msg is not None:
            self.fx_update_state(msg)
        orders = []
        if (self.started and time() - self.lastActionTime >
                self.options.get('delay')):
            self.lastActionTime = time()

            # XXX: Your strategies go here
            # examples:
            orders.extend(self.penny())
            print "OUTSIDE"
            print self.penny()
            print orders
            # orders.extend(self.marketMake())
            # orders.extend(self.momentum())


        if len(orders) > 0:
            action = {
                'message_type': 'MODIFY ORDERS',
                'orders': orders,
            }
            return dumps(action)
        return None


if __name__ == '__main__':
    bot = FXBot()
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    while not bot.done:
        sleep(0.01)

