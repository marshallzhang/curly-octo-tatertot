from base import *

pp = pprint.PrettyPrinter(depth = 6)

class TenderOffer():
    def __init__(self, ticker, price, quantity, we_buy):
        self.ticker = ticker
        self.price = price
        self.quantity = quantity
        self.we_buy = we_buy #T/F

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
        #return(tender_offer.price)
        # TODO
        # this should take in a tender offer and return TRUE/FALSE if we should take it
        # so you take the cost of the tender offer, and look through the order book
        # and see how much we would make if we executed the offer right now and liquidated it
        # edge is how much money per share we want to make (e.g. only take the tender share
        # if we liquidiate it right now, we make 0.10c per share on the average price to liquidate)

        #print(tender_offer)
        #print(tender_offer.price)
        #print(tender_offer.ticker)
        #print(tender_offer.quantity)
        #print(tender_offer.we_buy)
        print('ANOTHER TENDER OFFER ARRIVES')

        if tender_offer.we_buy == False: 
            #look at the offers
            offers = self.order_books[tender_offer.ticker].offers
            s = 0
            for offer in offers:
                if (s+offer.q) <= tender_offer.quantity: 
                    s= s + offer.q
                else: 
                    cutoff = offer 
                    position = offers.index(cutoff)
                    #print([sum, offers, cutoff, position])
                    print(offers)
                    break
            #now calculate quantity * price for offers < position
            hypPrice = 0
            for i in range(position): 
                hypPrice = hypPrice + offers[i].p * offers[i].q
            if (tender_offer.quantity - s) > 0: #need to check for half quantities
                hypPrice = hypPrice + (tender_offer.quantity - s) * offers[position].p 
            print(hypPrice)

            #find diff and decide to accept/not 
            return(tender_offer.price > (hypPrice/tender_offer.quantity)) #is it less than?! price that we buy at is less than what it would be

            #print(bids[1].p)
            
        else: #we sell
            #look at the bids
            bids = self.order_books[tender_offer.ticker].bids 
            s = 0
            for bid in bids:
                if (s + bid.q) < tender_offer.quantity: 
                    s = s + bid.q
                else: 
                    cutoff = bid
                    position = bids.index(cutoff)
                    #print([sum, offers, cutoff, position])
                    print(bids)
                    break
            #now calculate quantity * price for offers < position
            hypPrice = 0
            for i in range(position): 
                hypPrice = hypPrice + bids[i].p * bids[i].q
            if (tender_offer.quantity - s) > 0: #need to check for half quantities
                hypPrice = hypPrice + (tender_offer.quantity - s) * bids[position].p 
            print(hypPrice)

            #find diff and decide to accept/not 
            return(tender_offer.price < (hypPrice/tender_offer.quantity)) #is it more than?! price that we buy at is less than what it would be
                
    def how_to_hedge(self):
        return None
        
        # IN THEORY INPUT POSITIONS AND OUTPUT SHARES TO BUY/SELL OF TAMIT
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
            #DO SHIT HERE 
            print(self.accept_tender(offer, 0.50))
            # this should return T//F self.accept_tender(offer, 5.00)


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
        #os.system('cls' if os.name == 'nt' else 'clear')
        #pp.pprint(self.order_books)

        return None


if __name__ == '__main__':
    bot = STBot()
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    while not bot.done:
        sleep(0.01)

