from base import *

pp = pprint.PrettyPrinter(depth = 6)

def N(x, mean=0, sd=1):
    return((1.0 + math.erf((float(x) - mean) / (float(sd) * sqrt(2.0)))) / 2)

def Np(x, mean=0, sd=1):
    var = float(sd)**2
    pi = 3.1415926
    denom = (2*pi*var)**.5
    num = math.exp(-(float(x)-float(mean))**2/(2*var))
    return num/denom

class OptionSec():

    def __init__(self, ticker, K):
        self.ticker = ticker
        self.K = K
        self.order_book = []
        self.P = 0.
        self.S = 0.
        self.t = 0.
        self.IV = 0.
        self.T = 7.5


    def update(self, bids, asks, lastPrice, underPrice, time):
        self.order_book = OrderBook(bids, asks)
        self.P = lastPrice
        self.S = underPrice
        self.t = time/60.

    def d1(self, sigma):
        top = math.log(self.S/float(self.K)) + ((float(sigma)**2)/2.)*float(self.T-self.t)
        bottom = float(sigma)* math.sqrt(self.T-self.t)
        d1 = top/float(bottom)
        return(d1)

    def d2(self, sigma):
        d2 = float(self.d1) - sigma * math.sqrt(self.T-self.t)
        return(d2)



class Call(OptionSec):
    def BS(self, sigma):
        C = N(self.d1(sigma))*self.S - N(self.d2(sigma)) * self.K
        return(C)

    def delta(self, sigma):
        return(N(self.d1(sigma)))

    def gamma(self, sigma ):
        top = Np(self.d1(sigma))
        bottom = self.S * float(sigma) * math.sqrt(self.T - self.t)
        gamma = top/bottom 
        return(gamma)

    def vega(self, sigma):
        veg = self.S * Np(self.d1(sigma)) * math.sqrt(self.T - self.t)
        return(vega)

    def theta(self, sigma):
        top = -self.S * Np(self.d1(sigma)) * sigma 
        bottom = 2*math.sqrt(self.T - self.t)
        return(top/bottom)

    def updateIV(self):
        init_sig = math.sqrt(2 * 3.14 / 7.5) * (self.P / self.S)
        self.IV = scipy.optimize.newton(self.BS, init_sig, tol = 1.0e-6,  maxiter=50, fprime = self.vega)

class Put(OptionSec):
     def BS(self, sigma):
        P = N(-1.*self.d2(sigma)) * self.K - N(-1.*self.d1(sigma)) * self.S
        return(P)

    def delta(self, sigma):
        return(N(self.d1(sigma)))

    def gamma(self, sigma ):
        top = Np(self.d1(sigma))
        bottom = self.S * float(sigma) * math.sqrt(self.T - self.t)
        gamma = top/bottom * N(self.d1(sigma))
        return(gamma)

    def vega(self, sigma):
        veg = self.S * Np(self.d1(sigma)) * math.sqrt(self.T - self.t)
        return(vega)

    def theta(self, sigma):
        top = -self.S * Np(self.d1(sigma)) * sigma 
        bottom = 2*math.sqrt(self.T - self.t)
        return(top/bottom)

class OPBot(BaseBot):

    # If you want to keep track of any information in
    # addition to that stored in BaseBot, feel free to
    # update this init function as necessary.
    def __init__(self):
        super(OPBot, self).__init__()
        self.call_ladder = {"T90C" : Call("T90C", 90),
                            "T95C" : Call("T95C", 95),
                            "T100C" : Call("T100C", 100),
                            "T110C" : Call("T100C", 100),
                            "T100C" : Call("T100C", 100),
        }
        self.put_ladder = {}
        self.tamit = OrderBook()


    def isCall(self, ticker):
        return(ticker.endswith("C"))

    def update_state(self, msg):
        super(OPBot, self).update_state(msg)


    def pcParity(self, edge):
        strikes = self.call_ladder.keys()
        strikes = [int(k) for k in strikes]
        for k in strikes: 
            #COMPARE
            todo = self.pcCheck(self.call_ladder[k], self.put_ladder[k], edge)
            print(todo)


    def pcCheck(call, put, edge ):
        #situation 1: C-P > S-K
        left1 = call.order_book.bestBid() - put.order_book.bestOffer()
        right1 = edge + self.tamit.order_book.bestOffer() - call.K 
        if left1 > right1: 
            #TO DO BUY RIGHT, SELL K 
            todo1 = {call.ticker: 'sell', put.ticker: 'buy', 'TMXFUT': 'buy'}
            return(todo1)
        #situation 2
        left2 = call.order_book.bestOffer() - put.order_book.bestBid() + edge
        right2 = self.tamit.order_book.bestBid() - call.K 
        if left2 < right2: 
            todo2 = {call.ticker: 'buy', put.ticker: 'sell', 'TMXFUT': 'sell'}
            return(todo2)


    def pd_update_state(self, msg):
        if msg.get('market_states'):
            for ticker, state in msg['market_states'].iteritems():
                if self.isCall(ticker):
                    self.call_ladder[ticker] = OrderBook(state['bids'], state['asks'])
                else:
                    self.put_ladder[ticker] = OrderBook(state['bids'], state['asks'])
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

