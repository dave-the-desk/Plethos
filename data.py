class Web_Data:
    def __init__(self, name, party, branch, state, traded_issuer, ticker, publish_date, trade_type, size):
        self.name = name                   # Name of the person/entity trading
        self.party = party                 # Political party
        self.branch = branch               # Branch of government or organization
        self.state = state                 # State the person/entity is from
        self.traded_issuer = traded_issuer # Issuer of the traded stock
        self.ticker = ticker               # Ticker symbol of the stock
        self.publish_date = publish_date   # Date the trade was published
        self.trade_type = trade_type       # Type of trade (e.g., buy, sell)
        self.size = size                   # Size of the trade
    
    def __str__(self):
        return (f"StockTrade(name={self.name}, party={self.party}, branch={self.branch}, "
                f"state={self.state}, traded_issuer={self.traded_issuer}, ticker={self.ticker}, "
                f"publish_date={self.publish_date}, trade_type={self.trade_type}, size={self.size}")
    
    def to_dict(self):
        return {
            'name': self.name,
            'party': self.party,
            'branch': self.branch,
            'state': self.state,
            'traded_issuer': self.traded_issuer,
            'ticker': self.ticker,
            'publish_date': self.publish_date,
            'trade_type': self.trade_type,
            'size': self.size,
        }
