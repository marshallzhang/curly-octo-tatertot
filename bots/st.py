from base import *

pp = pprint.PrettyPrinter(depth = 6)

class TenderOffer():
    def __init__(self, ticker, price, quantity, we_buy):
        self.ticker = ticker
        self.price = price
        self.we_buy = we_buy

    def __repr__(self):
        return(repr((self.ticker, self.price, self.we_buy)))

class STBot(BaseBot):

    # If you want to keep track of any information in
    # addition to that stored in BaseBot, feel free to
    # update this init function as necessary.
    def __init__(self):
        super(STBot, self).__init__()
        self.order_books = {}

    def accept_tender(self, tender_offer, edge):
        return None
        # TODO
        # this should take in a tender offer and return TRUE/FALSE if we should take it
        # so you take the cost of the tender offer, and look through the order book
        # and see how much we would make if we executed the offer right now and liquidated it
        # edge is how much money per share we want to make (e.g. only take the tender share
        # if we liquidiate it right now, we make 0.10c per share on the average price to liquidate)

    def how_to_hedge(self):
        return None
        # TODO
        # this should tell us how many TAMIT index futures we need to buy to hedge out
        # our general market exposure, using the betas from the packet, self.positions,
        # and the order book.

    # Updates the bot's internal state according
    # to trader and market updates from the server.
    # Feel free to modify this method according to how
    # you want to keep track of your internal state.
    def update_state(self, msg):
        super(STBot, self).update_state(msg)

    def st_update_state(self, msg):
        if msg.get('tender_offer'):
            offer = TenderOffer(msg['tender_offer']['ticker'], 
                                msg['tender_offer']['price'], 
                                msg['tender_offer']['quantity'], 
                                msg['tender_offer']['buy'])

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
        super(STBot, self).process(msg)
        if msg is not None:
            self.st_update_state(msg)
        os.system('cls' if os.name == 'nt' else 'clear')
        pp.pprint(self.order_books)

        return None


if __name__ == '__main__':
    bot = STBot()
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    while not bot.done:
        sleep(0.01)

