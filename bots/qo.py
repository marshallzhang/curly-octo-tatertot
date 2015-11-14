from base import *

pp = pprint.PrettyPrinter(depth = 6)
coeffs = {'Inter': 1011, 'GDP': 0.03122, 'CPI': 0.5188, 'PPI': -1.098, 'ECI': 4.500, 'CCI': 0.0007618, 'U': -2.428}
#PPI(-) > U(-) > ECI (+)

class NewsRelease():
    def __init__(self, source, time, body):
        self.source = source
        self.time = time
        self.body = body

    def __repr__(self):
        return(repr((self.source, self.body)))

class PDBot(BaseBot):

    # If you want to keep track of any information in
    # addition to that stored in BaseBot, feel free to
    # update this init function as necessary.
    def __init__(self):
        super(PDBot, self).__init__()
        self.current_news = ""
        self.current_prediction = 0.

    # Updates the bot's internal state according
    # to trader and market updates from the server.
    # Feel free to modify this method according to how
    # you want to keep track of your internal state.
    def update_state(self, msg):
        super(PDBot, self).update_state(msg)

    def pd_update_state(self, msg):
        if msg.get('news'):
            body = msg['news']['headline'].split('; ')
            body = {x.split(" estimated to be ")[0] : (float(x.split(" estimated to be ")[1])) for x in body}
            self.current_news = body
            #regression output
            coeff_prod = {k: v* body[k] for k, v in coeffs.items() if k in body}
            new_pred = coeffs['Inter']+ sum(coeff_prod.values())
            self.current_prediction = new_pred 

    # Overrides the BaseBot process function.
    # Modify this function if you want your bot to
    # execute a strategy.
    def process(self, msg):
        super(PDBot, self).process(msg)
        if msg is not None:
            self.pd_update_state(msg)
        os.system('cls' if os.name == 'nt' else 'clear')
        pp.pprint(self.current_news)
        pp.pprint("PREDICTION: " + str(self.current_prediction))

if __name__ == '__main__':
    bot = PDBot()
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    while not bot.done:
        sleep(0.01)

