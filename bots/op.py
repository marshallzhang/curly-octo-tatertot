from base import *

pp = pprint.PrettyPrinter(depth = 6)

def N(x, mean, sd):
    return((1.0 + math.erf((float(x) - mean) / (float(sd) * sqrt(2.0)))) / 2)

def Np(x, mean, sd):
    var = float(sd)**2
    pi = 3.1415926
    denom = (2*pi*var)**.5
    num = math.exp(-(float(x)-float(mean))**2/(2*var))
    return num/denom

def d1(S, K, r = 0, sigma, t):
    top = math.log(S/K) + (r+(float(sigma)**2/float(2)))(T-t)
    bottom = sigma * math.sqrt(T-t)
    d1 = top/bottom 
    return(d1)



class OptionSec():

    def __init__(self, ticker, K):
        self.ticker = ticker
        self.K = K
        self.order_book = []
        self.P = 0.
        self.S = 0.
        self.t = 0.

    def update(bids, asks, lastPrice, underPrice, time):
        self.order_book = OrderBook(bids, asks)
        self.lastPrice = lastPrice
        self.underPrice = underPrice
        self.t = time

    def d1(self, K, r = 0, sigma, t):
        top = math.log(self.S/self.K) + (r+(float(sigma)**2/float(2)))(T-t)
        bottom = sigma * math.sqrt(T-t)
        d1 = top/bottom 
        return(d1)

    def d2(d1, sigma, t):
    d2 = d1 - sigma * math.sqrt(T-t)



class Call(OptionSec):
    def BS(S, K, t, sigma):
        d1 = math.log(S / float(K))

    def delta(self):

    def gamma(self):

    def vega(self):

    def theta(self):


class Put(OptionSec):

class OPBot(BaseBot):

    # If you want to keep track of any information in
    # addition to that stored in BaseBot, feel free to
    # update this init function as necessary.
    def __init__(self):
        super(OPBot, self).__init__()
        self.market = {}

    def isCall(self, ticker):
        return(ticker[0] == "C")

    def update_state(self, msg):
        super(OPBot, self).update_state(msg)

    def pd_update_state(self, msg):
        if msg.get('market_states'):
            for ticker, state in msg['market_states'].iteritems():
                if self.isCall(ticker):
                    self.calls[ticker[1:]] = OrderBook(state['bids'], state['asks'])
                else:
                    self.puts[ticker[1:]] = OrderBook(state['bids'], state['asks'])
        if msg.get('market_state'):
            state = msg['market_stsate']
            ticker = state['ticker'][1:]
            if self.isCall(state['ticker']):
                self.calls[ticker[1:]] = OrderBook(state['bids'], state['asks'])
            else:
                self.puts[ticker[1:]] = OrderBook(state['bids'], state['asks'])

        if msg.get('news'):
            body = msg['news']['body'].split('; ')
            body = [float(x.split(" estimated to be worth ")[1]) for x in body]

    # Overrides the BaseBot process function.
    # Modify this function if you want your bot to
    # execute a strategy.
    def process(self, msg):
        super(OPBot, self).process(msg)
        if msg is not None:
            self.pd_update_state(msg)
        os.system('cls' if os.name == 'nt' else 'clear')
        print(str(self.accept) + "\n")
        n = len(self.news_releases)
        weights = np.array([r / float(n) for r in range(1,n+1)])
        weights = weights / np.sum(weights)
        for i in range(len(self.tickers)):
            lo = self.true_prices[i] - self.ses[i]
            hi = self.true_prices[i] + self.ses[i]
            estim = self.true_prices[i]
            print "        " + self.tickers[i]
            try:
                last_price = self.lastPrices[self.tickers[i]]
            except:
                continue
            # last_price = str("%.2f" % last_price)
            if last_price < lo:
                mid = bcolors.RED + str(last_price) + bcolors.ENDC
            elif last_price > hi:
                mid = bcolors.GREEN + str(last_price) + bcolors.ENDC
            else:
                if lo + ((estim - lo) / 2.) < last_price and last_price < hi - ((hi - estim) / 2.):
                    mid = str(last_price)
                elif last_price < lo + ((estim - lo) / 2.):
                    mid = bcolors.YELLOW + str(last_price) + bcolors.ENDC
                elif last_price > hi - ((hi - estim) / 2.):
                    mid = bcolors.BLUE + str(last_price) + bcolors.ENDC
            estims = np.array([float(release.body[i]) for release in self.news_releases]) 
            avg = np.sum(weights * estims)
            print (str(self.lower[i]) + 
                   " - " + 
                   ("%.2f" % lo) + 
                   " - " + 
                   mid +
                   " (" + 
                   ("%.2f" % avg) + 
                   ")" +
                   " - " + 
                   ("%.2f" % hi) + 
                   " - " +  
                   str(self.upper[i]) + "\n")
        for i in range(len(self.tickers)):
            print self.tickers[i]
            estims = np.array([float(release.body[i]) for release in self.news_releases]) 
            try:
                print str(repr(estims))
            except ZeroDivisionError:
                print ""

        return None


if __name__ == '__main__':
    bot = OPBot()
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    while not bot.done:
        sleep(0.01)

