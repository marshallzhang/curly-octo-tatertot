from base import *

pp = pprint.PrettyPrinter(depth = 6)

class OPBot(BaseBot):

    # If you want to keep track of any information in
    # addition to that stored in BaseBot, feel free to
    # update this init function as necessary.
    def __init__(self):
        super(PDBot, self).__init__()
        self.news_releases = []

        self.true_prices = [40., 60., 85., 60., 40.]
        self.init_prices = [40., 60., 85., 60., 40.]
        self.ses = [10., 20., 15., 20., 20.]

        self.corr = np.array([[1., -0.64372484, 0.09173378, -0.25319211, 0.6453473],
                              [-0.64372484, 1., -0.65889412, 0.50111104, -0.12582015],
                              [0.09173378,-0.65889412,1.,-0.19964734,-0.17288262],
                              [-0.25319211,0.50111104,-0.19964734,1.,-0.37187632],
                              [0.6453473,-0.12582015,-0.17288262,-0.37187632,1.]])

        self.lower = [30., 40., 70., 40., 20.]
        self.upper = [50., 80., 100., 80., 60.]

        self.tickers = [u"EXE", u"CPP", u"HS", u"PYPY", u"RB"]

        self.sources = []

        self.true_qs = []

        self.possible_q = [0.5, 0.7, 1.3, 3.5]

        self.tp = [42, 60, 79.9, 56, 44]

        self.accept = 0


    def likelihood(self, theta):
        posited_prices = list(theta[:5])
        posited_qs = list(theta[5:])
        len_news = len(self.news_releases)
        len_p = len(posited_prices)
        len_q = len(posited_qs)
        
        lik = np.zeros(len_news + len_p + len_q)
        for i, release in enumerate(self.news_releases):
            try:
                lik[i] = math.log(stats.multivariate_normal.pdf(release.body, 
                                                mean = posited_prices, 
                                                cov = math.pow(posited_qs[self.sources.index(release.source)], 2) * self.corr * (600 - float(release.time)) / 60))
            except:
                lik[i] = -99999.

        for i in range(len(self.upper)):
            up = self.upper[i]
            lo = self.lower[i]
            if lo < posited_prices[i] and posited_prices[i] < up:
                lik[i + len_news] = math.log(1 / float(self.upper[i] - self.lower[i]))
            else:
                lik[i + len_news] = -99999.

        for i in range(len(posited_qs)):
            try:
                lik[i + len_news + len_p] = (2/3.) * math.exp(-((2/3.) * posited_qs[i]))
            except:
                lik[i + len_news + len_p] = -99999.
        return(sum(lik))
        
    def mcmc(self, start, unique_qs, iterations, burn):
        draws = np.zeros((iterations + 1, 5 + unique_qs)) 
        draws[0, :] = start
        accept = 0
        for i in range(iterations):
            proposal = np.random.multivariate_normal(mean = draws[i, :5], cov = 0.2 * np.diag([1,1,1,1,1]))
            mv_q = np.random.multivariate_normal(mean = draws[i, 5:], cov = 0.07 * np.diag([1 for x in range(unique_qs)]))
            proposal = np.append(proposal, mv_q)

            alpha = min(0, self.likelihood(proposal) - self.likelihood(draws[i, :]))
            if math.log(np.random.random()) < alpha:
                draws[i + 1, :] = proposal
                accept += 1
            else:
                draws[i + 1, :] = draws[i, :]
        self.accept = accept / float(iterations)
        return(draws[burn::10,:])

    # Updates the bot's internal state according
    # to trader and market updates from the server.
    # Feel free to modify this method according to how
    # you want to keep track of your internal state.
    def update_state(self, msg):
        super(PDBot, self).update_state(msg)

    def pd_update_state(self, msg):
        if msg.get('news'):
            body = msg['news']['body'].split('; ')
            body = [float(x.split(" estimated to be worth ")[1]) for x in body]
            self.news_releases.extend([NewsRelease(msg['news']['source'], msg['news']['time'], body)])
            if msg['news']['source'] not in self.sources:
                self.sources.extend([msg['news']['source']])
                self.true_qs.extend([1.5])

            if msg['news']['time'] < 10:
                return
            unique_qs = len(set([releases.source for releases in self.news_releases]))
            draws = self.mcmc(self.init_prices + self.true_qs, unique_qs, 6000, 500)
            colmeans = np.mean(draws, axis = 0)
            colses = np.std(draws, axis = 0)
            self.true_prices = list(colmeans[:5])
            self.ses = list(colses[:5])
            self.true_qs = list(colmeans[5:])
            pp.pprint(self.true_prices)
            pp.pprint(self.ses)
            pp.pprint(self.true_qs)

    # Overrides the BaseBot process function.
    # Modify this function if you want your bot to
    # execute a strategy.
    def process(self, msg):
        super(PDBot, self).process(msg)
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

