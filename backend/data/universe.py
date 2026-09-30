"""Initial manageable universe of liquid Indian large-caps. Expandable later.

Mock fundamentals are illustrative and clearly flagged as mock data in the UI; real
fundamentals will come from a FundamentalDataProvider in the next milestone.
"""

UNIVERSE = {
    "RELIANCE": {"name": "Reliance Industries", "sector": "Energy", "base_price": 2900, "drift": 0.0009,
                 "fundamentals": {"revenue_growth": 11.2, "profit_growth": 9.5, "eps_growth": 8.1, "roe": 8.9,
                                  "roce": 10.2, "debt_equity": 0.42, "pe": 24.5, "pb": 2.1, "ocf": 1.0, "margin_trend": "up"}},
    "TCS": {"name": "Tata Consultancy Services", "sector": "IT", "base_price": 3850, "drift": 0.0008,
            "fundamentals": {"revenue_growth": 7.0, "profit_growth": 8.8, "eps_growth": 9.0, "roe": 46.0,
                             "roce": 55.0, "debt_equity": 0.08, "pe": 29.0, "pb": 12.5, "ocf": 1.0, "margin_trend": "flat"}},
    "HDFCBANK": {"name": "HDFC Bank", "sector": "Financials", "base_price": 1650, "drift": 0.0006,
                 "fundamentals": {"revenue_growth": 15.5, "profit_growth": 12.0, "eps_growth": 11.0, "roe": 17.0,
                                  "roce": None, "debt_equity": None, "pe": 19.0, "pb": 2.8, "ocf": 1.0, "margin_trend": "up"}},
    "INFY": {"name": "Infosys", "sector": "IT", "base_price": 1580, "drift": 0.0007,
             "fundamentals": {"revenue_growth": 6.1, "profit_growth": 7.5, "eps_growth": 7.8, "roe": 31.0,
                              "roce": 38.0, "debt_equity": 0.1, "pe": 26.0, "pb": 8.0, "ocf": 1.0, "margin_trend": "flat"}},
    "ICICIBANK": {"name": "ICICI Bank", "sector": "Financials", "base_price": 1180, "drift": 0.001,
                  "fundamentals": {"revenue_growth": 18.0, "profit_growth": 20.0, "eps_growth": 19.0, "roe": 18.5,
                                   "roce": None, "debt_equity": None, "pe": 18.5, "pb": 3.1, "ocf": 1.0, "margin_trend": "up"}},
    "SBIN": {"name": "State Bank of India", "sector": "Financials", "base_price": 820, "drift": 0.0008,
             "fundamentals": {"revenue_growth": 13.0, "profit_growth": 16.0, "eps_growth": 15.0, "roe": 16.0,
                              "roce": None, "debt_equity": None, "pe": 11.0, "pb": 1.7, "ocf": 1.0, "margin_trend": "up"}},
    "BHARTIARTL": {"name": "Bharti Airtel", "sector": "Telecom", "base_price": 1520, "drift": 0.0011,
                   "fundamentals": {"revenue_growth": 14.0, "profit_growth": 22.0, "eps_growth": 20.0, "roe": 15.0,
                                    "roce": 13.0, "debt_equity": 1.4, "pe": 55.0, "pb": 7.0, "ocf": 1.0, "margin_trend": "up"}},
    "ITC": {"name": "ITC Ltd", "sector": "FMCG", "base_price": 460, "drift": 0.0004,
            "fundamentals": {"revenue_growth": 4.5, "profit_growth": 5.0, "eps_growth": 5.2, "roe": 28.0,
                             "roce": 35.0, "debt_equity": 0.0, "pe": 27.0, "pb": 7.5, "ocf": 1.0, "margin_trend": "flat"}},
    "LT": {"name": "Larsen & Toubro", "sector": "Industrials", "base_price": 3600, "drift": 0.0009,
           "fundamentals": {"revenue_growth": 17.0, "profit_growth": 14.0, "eps_growth": 13.5, "roe": 15.5,
                            "roce": 16.0, "debt_equity": 0.9, "pe": 33.0, "pb": 5.0, "ocf": 1.0, "margin_trend": "up"}},
    "HINDUNILVR": {"name": "Hindustan Unilever", "sector": "FMCG", "base_price": 2450, "drift": 0.0003,
                   "fundamentals": {"revenue_growth": 3.0, "profit_growth": 2.5, "eps_growth": 2.8, "roe": 20.0,
                                    "roce": 25.0, "debt_equity": 0.02, "pe": 52.0, "pb": 10.0, "ocf": 1.0, "margin_trend": "down"}},
    "TATAMOTORS": {"name": "Tata Motors", "sector": "Automobile", "base_price": 980, "drift": 0.0012,
                   "fundamentals": {"revenue_growth": 12.0, "profit_growth": 30.0, "eps_growth": 28.0, "roe": 22.0,
                                    "roce": 18.0, "debt_equity": 1.1, "pe": 15.0, "pb": 3.5, "ocf": 1.0, "margin_trend": "up"}},
    "AXISBANK": {"name": "Axis Bank", "sector": "Financials", "base_price": 1150, "drift": 0.0007,
                 "fundamentals": {"revenue_growth": 14.0, "profit_growth": 11.0, "eps_growth": 10.5, "roe": 15.0,
                                  "roce": None, "debt_equity": None, "pe": 13.5, "pb": 2.2, "ocf": 1.0, "margin_trend": "up"}},
}

SECTORS = sorted({v["sector"] for v in UNIVERSE.values()})

NEWS_TEMPLATES = [
    {"headline": "{company} reports strong quarterly profit growth, beats estimates", "source": "Economic Times"},
    {"headline": "{company} announces expansion, brokerages upgrade target", "source": "Moneycontrol"},
    {"headline": "{company} shares rally on robust volume", "source": "Business Standard"},
    {"headline": "Analysts remain cautious on {company} amid margin pressure", "source": "Livemint"},
    {"headline": "{company} faces regulatory probe, stock under pressure", "source": "Reuters"},
    {"headline": "{company} board approves dividend, investors cheer", "source": "CNBC-TV18"},
    {"headline": "{company} guidance in-line, stock trades flat", "source": "Bloomberg Quint"},
    {"headline": "{company} wins large order, order book at record high", "source": "Financial Express"},
]
