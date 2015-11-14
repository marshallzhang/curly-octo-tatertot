from base import *
import time

pp = pprint.PrettyPrinter(depth = 6)

def N(x, mean=0, sd=1):
    return((1.0 + math.erf((float(x) - mean) / (float(sd) * math.sqrt(2.0)))) / 2)

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
        d2 = float(self.d1(sigma)) - sigma * math.sqrt(self.T-self.t)
        return(d2)



class Call(OptionSec):
    def BS(self, sigma):
        C = N(self.d1(sigma))*self.S - N(self.d2(sigma)) * self.K
        return(C)

    def optBS(self, sigma):
        return(abs(self.BS(sigma) - self.P)**2)

    def delta(self, sigma):
        return(N(self.d1(sigma)))

    def gamma(self, sigma):
        top = Np(self.d1(sigma))
        bottom = self.S * float(sigma) * math.sqrt(self.T - self.t)
        gamma = top/bottom 
        return(gamma)

    def vega(self, sigma):
        vega = self.S * Np(self.d1(sigma)) * math.sqrt(self.T - self.t)
        return(vega)

    def theta(self, sigma):
        top = -self.S * Np(self.d1(sigma)) * sigma 
        bottom = 2*math.sqrt(self.T - self.t)
        return(top/bottom)

    def updateIV(self):
        init_sig = math.sqrt(2 * 3.14 / 7.5) * (self.P / self.S)
        if self.t > 7.5 or self.t < 0.1:
            self.IV = 2.
        else:
            for i in range(50):
                init_sig = init_sig - ((self.BS(init_sig) - self.P) / self.vega(init_sig))
                print init_sig
            self.IV = init_sig

class Put(OptionSec):

    def BS(self, sigma):
        P = N(-1.*self.d2(sigma)) * self.K - N(-1.*self.d1(sigma)) * self.S
        return(P)

    def optBS(self, sigma):
        return(abs(self.BS(sigma) - self.P)**2)

    def delta(self, sigma):
        return(N(self.d1(sigma)))

    def gamma(self, sigma):
        top = Np(self.d1(sigma))
        bottom = self.S * float(sigma) * math.sqrt(self.T - self.t)
        gamma = (top/bottom) * N(self.d1(sigma))
        return(gamma)

    def vega(self, sigma):
        vega = self.S * Np(self.d1(sigma)) * math.sqrt(self.T - self.t)
        return(vega)

    def theta(self, sigma):
        top = -self.S * Np(self.d1(sigma)) * sigma 
        bottom = 2*math.sqrt(self.T - self.t)
        return(top/bottom)

    def updateIV(self):
        init_sig = math.sqrt(2 * 3.14 / 7.5) * (self.P / self.S)
        try:
            self.IV = scipy.optimize.minimize(self.optBS, init_sig).x
        except:
            self.IV = 0.

class OPBot(BaseBot):

    # If you want to keep track of any information in
    # addition to that stored in BaseBot, feel free to
    # update this init function as necessary.
    def __init__(self):
        super(OPBot, self).__init__()
        self.call_ladder = {90 : Call("T90C", 90.),
                            95 : Call("T95C", 95.),
                            100 : Call("T100C", 100.),
                            105 : Call("T105C", 105.),
                            110 : Call("T110C", 110.)
        }

        self.put_ladder = {90 : Put("T90P", 90.),
                            95 : Put("T95P", 95.),
                            100 : Put("T100P", 100.),
                            105 : Put("T105P", 105.),
                            110 : Put("T110P", 110.)
        }

        self.tamit = []
        self.start = 0.


    def isCall(self, ticker):
        return(ticker.endswith("C"))
    
    def getK(self, ticker):
        return(int(ticker[1:-1]))

    def update_state(self, msg):
        super(OPBot, self).update_state(msg)

    def pcParity(self):
        if self.tamit == []:
            return {}
        strikes = self.call_ladder.keys()
        strikes = [int(k) for k in strikes]
        arbs = {}
        for k in strikes: 
            #COMPARE
            arbs[k] = self.pcCheck(self.call_ladder[k], self.put_ladder[k])
        return(arbs)

    def pcCheck(self, call, put):
        #situation 1: C-P > S-K
        left1 = call.order_book.bestBid().p - put.order_book.bestOffer().p
        right1 = self.tamit.bestOffer().p - call.K 
        if left1 > right1: 
            #TO DO BUY RIGHT, SELL K 
            todo1 = {call.ticker: 'sell', put.ticker: 'buy', 'TMXFUT': 'buy',"edge": left1 - right1}
            return(todo1)
        left2 = call.order_book.bestOffer().p - put.order_book.bestBid().p
        right2 = self.tamit.bestBid().p - call.K 
        if left2 < right2: 
            todo2 = {call.ticker: 'buy', put.ticker: 'sell', 'TMXFUT': 'sell', "edge": left2 - right2}
            return(todo2)
        return None

    def getCall(self, ticker):
        return(self.call_ladder[self.getK(ticker)])
    
    def getPut(self, ticker):
        return(self.put_ladder[self.getK(ticker)])

    def portGreeks(self):
        delta = 0.
        vega = 0.
        print self.positions.items()
        for ticker, quantity in self.positions.items():
            if ticker == "TMXFUT":
                delta += quantity
            else:
                try:
                    if self.isCall(ticker):
                        call = self.getCall(ticker)
                        delta += call.delta(call.IV) * quantity
                        vega += call.vega(call.IV) * quantity
                    else:
                        put = self.getPut(ticker)
                        delta += put.delta(put.IV) * quantity
                        vega += put.vega(put.IV) * quantity
                except:
                    delta = delta
                    vega = vega
        return {"delta" : delta, "vega" : vega}

    def pd_update_state(self, msg):
        if msg.get('market_states'):
            for ticker, state in msg['market_states'].iteritems():
                if ticker == "TMXFUT":
                    self.tamit = OrderBook(state['bids'], state['asks'])
                elif "INDEX" in ticker:
                    continue
                else:
                    if self.isCall(ticker):
                        call = self.call_ladder[self.getK(ticker)]
                        call.update(state['bids'], 
                                    state['asks'], 
                                    self.lastPrices[ticker], 
                                    self.lastPrices["TAMITINDEX"], 
                                    time.time() - self.start)
                        call.updateIV()
                    else:
                        put = self.put_ladder[self.getK(ticker)]
                        put.update(state['bids'], 
                                    state['asks'], 
                                    self.lastPrices[ticker], 
                                    self.lastPrices["TAMITINDEX"], 
                                    time.time() - self.start)
                        put.updateIV()
        if msg.get('market_state'):
            if self.start == 0.:
                self.start = time.time()
            state = msg['market_state']
            ticker = state['ticker']
            if ticker == "TMXFUT":
                self.tamit = OrderBook(state['bids'], state['asks'])
            elif "INDEX" in ticker:
                return None
            else:
                if self.isCall(ticker):
                    call = self.call_ladder[self.getK(ticker)]
                    call.update(state['bids'], 
                                state['asks'], 
                                self.lastPrices[ticker], 
                                self.lastPrices["TAMITINDEX"], 
                                time.time() - self.start)
                    call.updateIV()
                else:
                    put = self.put_ladder[self.getK(ticker)]
                    put.update(state['bids'], 
                                state['asks'], 
                                self.lastPrices[ticker], 
                               self.lastPrices["TAMITINDEX"], 
                                time.time() - self.start)
                    put.updateIV()

    # Overrides the BaseBot process function.
    # Modify this function if you want your bot to
    # execute a strategy.
    def process(self, msg):
        super(OPBot, self).process(msg)
        if msg is not None:
            self.pd_update_state(msg)
            arbs = self.pcParity()
            greeks = self.portGreeks()


            # PRINT DASHBOARD
            os.system('cls' if os.name == 'nt' else 'clear')
            try:
                print((" " * 32 + "TAMIT: ")  + ("%.0f" % (self.lastPrices["TAMITINDEX"])))
                c = self.call_ladder[90]
                print(c.S, c.K, c.t, c.P)
            except:
                x = 0
            topcalls = '{0: >30}'.format("CALLS")
            print topcalls + " " * 14 + "PUTS"
            for call, put in zip(sorted(self.call_ladder.values(), key = lambda x : x.K), sorted(self.put_ladder.values(), key = lambda x : x.K)):
                calls = '{0: >30}'.format("(%.2f, %.2f)" % (call.P, call.IV * 100))
                puts = '{0: <17}'.format("(%.2f, %.2f)" % (put.IV * 100, put.P))
                print calls +  "  | " + '{0: <7}'.format(str(call.K)) + "|  " + puts
            print((" " * 17 + "PUT CALL PARITY "))
            for arb in arbs.values():
                print arb

            print(" " * 17 + "PORTFOLIO GREEKS")
            for k,v in greeks.items():
                print(k,v)
        return None


if __name__ == '__main__':
    bot = OPBot()
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    while not bot.done:
        sleep(0.01)

