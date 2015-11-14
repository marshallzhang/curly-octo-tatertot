from Queue import Queue
from threading import Lock
from threading import Thread
from json import dumps
from json import loads
from re import match
from time import sleep
from time import time
from zlib import decompress
from zlib import MAX_WBITS
import numpy as np
import scipy.stats as stats
import math
import pprint
import os
import operator
import scipy

pp = pprint.PrettyPrinter(depth = 6)

from websocket import create_connection
from websocket import WebSocketTimeoutException
from websocket import WebSocketConnectionClosedException

DEFAULT_DELAY = 1
DEFAULT_POSITION_LIMIT = 100
DEFAULT_ORDER_QUANTITY = 50

EWMA_FACTOR = 0.2
ENTER_THRESHOLD = 0.05

class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Options():
    def __init__(self, default=None):
        self.data = default or {}
        self.mu = Lock()

    def get(self, key):
        return self.data.get(key)

    def set(self, key, val):
        if key not in self.data:
            print "Invalid option: %s" % key
        else:
            print "Set %s to %s" % (key, val)
            self.data[key] = val

class Order(): 
    def __init__(self, price, quantity):
        self.p = float(price)
        self.q = float(quantity)
    
class Bid(Order):
    def to_sign(self):
        return 1
    def to_float(self):
        return(self.to_sign * self.p * self.q)
    def __repr__(self):
        return(str(self.p) + " bid for " + str(self.q))

class Offer(Order):
    def to_sign(self):
        return -1
    def to_float(self):
        return(self.to_sign * self.p * self.q)
    def __repr__(self):
        return(str(self.q) + " offered at " + str(self.p))

class Trade():
    def __init__(self, ticker, price, quantity):
        self.ticker = ticker
        self.price = price
        self.quantity = quantity

class OrderBook():
    def __init__(self, bids, offers):
        self.bids = [Bid(p, q) for p,q in zip(map(float, bids.keys()), bids.values())]
        self.bids = sorted(self.bids, key = lambda x : x.p, reverse = True)
        self.offers = [Offer(p, q) for p,q in zip(map(float, bids.keys()), bids.values())]
        self.offers = sorted(self.offers, key = lambda x : x.p)

    def bestBid(self):
        if len(self.bids) == 0:
            return(Bid(0.,0.))
        else:
            return(self.bids[0])


    def bestOffer(self):
        if len(self.offers) == 0:
            return(Offer(10000., 0.))
        else:
            return(self.offers[0])

    def update(self, trade):
        #USEFUL CODE IN THE FUTURE
        #amt = trade.quantity
        # if trade.price == self.bestBid:
        #     amt = trade.quantity
        #     while amt >0: 
        #         for bid in self.bids: 
        #             amt = amt - bid.q
        #             if amt > 0: 
        #                 bid.q = 0 
        #             else: 
        #                 bid.q = abs(amt)
        # else: 
        #     #if trade.price == self.bestOffer:
        #     while amt >0: 
        #         for offer in self.offers: 
        #             amt = amt - offer.q
        #             if amt > 0: 
        #                 offer.q = 0 
        #             else: 
        #                 offer.q = abs(amt)

        # if trade.price == self.bestBid().p:
        #     print('hello')
        #     self.bestBid().q = self.bestBid().q - trade.quantity
        #     new_orderBids = [bid for bid in self.bids if not bid.q == 0]            
        # else:
        #     self.bestOffer().q = self.bestOffer().q - trade.quantity
        #     new_orderOffers = [offer for offer in self.offers if not offer.q == 0]
        # self.bids = new_orderBids
        # self.offers = new_orderOffers

        #delete all the order book lines with 0 

        return 1

    def __repr__(self):
        return(repr((self.bids, self.offers)))

class BaseBot(object):
    # XXX change me for actual running

    trader_id = 'mxzhang@college.harvard.edu'
    password = 'around-afferent-programs'

    # Sets up the connection to the server.
    # Please do not change anything here unless
    # you know what's going on
    def __init__(self):
        self.options = Options({
            'delay': DEFAULT_DELAY,
            'position_limit': DEFAULT_POSITION_LIMIT,
            'order_quantity': DEFAULT_ORDER_QUANTITY,
            'ewma_factor': EWMA_FACTOR,
            'enter_threshold': ENTER_THRESHOLD,
        })

        self.ws = create_connection(
            'ws://d.angocore.com/%s/%s' % (self.trader_id, self.password),
            timeout=0.5,
        )
        self.outbox = Queue()

        self.started = False
        self.done = False
        self.lastActionTime = time()

        # Market information.

        self.lastPrices = {}
        self.positions = {}
        self.order_books = {}

        register_msg = dumps({
            'message_type': 'REGISTER',
        })
        self.outbox.put(register_msg)


    # You should not have to modify the following three
    # methods.
    
    # Starts and returns the two processes of the bot.
    def makeThreads(self):
        reader_t = Thread(target=self.ws_reader, args=())
        writer_t = Thread(target=self.ws_writer, args=())

        return reader_t, writer_t

    # Reads input from from the server and processes
    # them accordingly
    def ws_reader(self):
        while True:
            try:
                msg = self.ws.recv()
                msg = decompress(msg, 16+MAX_WBITS)
                msg = loads(msg)
            except WebSocketTimeoutException:
                msg = None
            except WebSocketConnectionClosedException:
                self.outbox.put(None)
                return

            output = self.process(msg)
            if output is not None:
                self.outbox.put(output)

    # Sends messages in our outbox to the server
    def ws_writer(self):
        while True:
            msg = self.outbox.get()
            if msg is None:
                break
            else:
                self.ws.send(msg)
        self.ws.close()


    # Updates the bot's internal state according
    # to trader and market updates from the server.
    # Feel free to modify this method according to how
    # you want to keep track of your internal state.
    def update_state(self, msg):
        try:
            # Update internal positions
            if msg.get('trader_state'):
                self.positions = msg['trader_state']['positions']

            # Update internal books for each ticker
            if msg.get('market_states'):
                for ticker, state in msg['market_states'].iteritems():
                    self.lastPrices[ticker] = state['last_price']

            if msg.get('market_state'):
                state = msg['market_state']
                ticker = state['ticker']
                self.lastPrices[ticker] = state['last_price']

            # Update internal books for each ticker
            # if msg.get('market_states'):
            #     for ticker, state in msg['market_states'].iteritems():
            #         if not self.order_books:
            #             self.order_books[ticker] = OrderBook(state['bids'], state['asks'])
            #         else:
            #             print self.order_books[ticker] == OrderBook(state['bids'], state['asks'])
            #             self.order_books[ticker] = OrderBook(state['bids'], state['asks'])

            # Update internal book for a single ticker
            # if msg.get('market_state'):
            #     state = msg['market_state']
            #     ticker = state['ticker']
            #     if not self.order_books:
            #         self.order_books[ticker] = OrderBook(state['bids'], state['asks'])
            #     else:
            #         print self.order_books[ticker] == OrderBook(state['bids'], state['asks'])
            #         self.order_books[ticker] = OrderBook(state['bids'], state['asks'])

            # if msg.get('trades'):
            #     trades = msg['trades']
            #     for trade in trades:
            #         t = Trade(trade['ticker'], trade['price'], trade['quantity'])
            #         print "OLD"
            #         print trade['ticker']
            #         print self.order_books[trade['ticker']]
            #         print(trade)
            #         self.order_books[trade['ticker']].update(t)
            #         print "NEW"
            #         print self.order_books[trade['ticker']]

            if msg.get('message_type') == 'START':
                self.started = True
            elif msg.get('end_time'):
                if not msg.get('end_time').startswith('0001'):
                    self.started = True

        except:
            x=0
    # Processes the messages received from the server.
    # This BaseBot process only updates the bot's state
    # with server updates. To execute your own strategies,
    # modify this method (in either a child class or this one).
    def process(self, msg):
        if msg is not None:
            self.update_state(msg)
        #os.system('cls' if os.name == 'nt' else 'clear')
        return None


if __name__ == '__main__':
    bot = BaseBot()
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    while not bot.done:
        sleep(0.01)

