from selenium import webdriver
from bs4 import BeautifulSoup
from data import Web_Data
import sqlite3
import re
from datetime import datetime
import time

# Set up the in-memory database for temporary trade data storage
conn_trades = sqlite3.connect(':memory:')
cursor_trades = conn_trades.cursor()

# Create the trades table
cursor_trades.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        party TEXT,
        branch TEXT,
        state TEXT,
        traded_issuer TEXT,
        ticker TEXT,
        publish_date TEXT,
        trade_type TEXT,
        size TEXT
    )
''')
conn_trades.commit()


def Connect_To_Website_Page(i):
    print("Connecting to Capital Trades...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.get(WebPage_Updater(i))
    print("____Connection Successful____")
    return driver


def WebPage_Updater(index):
    return f'https://www.capitoltrades.com/trades?page={index}'

def format_trade_data(data):
    # Extract and format trade data, returning an instance of Web_Data
    name_party_branch_state = re.match(r'([A-Za-z ]+)(Democrat|Republican)(House|Senate)([A-Z]{2})', data[0])
    if name_party_branch_state:
        name = name_party_branch_state.group(1).strip()
        party = name_party_branch_state.group(2)
        branch = name_party_branch_state.group(3)
        state = name_party_branch_state.group(4)
    else:
        raise ValueError(f"Could not parse name, party, branch, and state from '{data[0]}'")
    
    # Extract remaining fields
    issuer_ticker_match = re.match(r'(.+?)([A-Z]+\/?[A-Z]+):US', data[1])
    traded_issuer = issuer_ticker_match.group(1).strip() if issuer_ticker_match else data[1].strip()
    ticker = issuer_ticker_match.group(2) if issuer_ticker_match else 'N/A'
    if traded_issuer.endswith("N/A"):
        traded_issuer = traded_issuer[:-3].strip()
    
    date_match = re.match(r'(\d{1,2})\s([A-Za-z]+)(\d{4})', data[3].strip())
    if date_match:
        day, month, year = date_match.groups()
        publish_date = datetime.strptime(f"{day} {month[:3]} {year}", "%d %b %Y").strftime("%B %d, %Y")
    else:
        raise ValueError(f"Date format is incorrect: '{data[3]}'")

    trade_type = data[6].capitalize()
    bounds = re.findall(r'\d+', data[7])
    
    if len(bounds) == 2:
        lower_bound = int(bounds[0]) * 1000  # Convert to integer and scale if needed
        upper_bound = int(bounds[1]) * 1000
        average = (lower_bound + upper_bound) / 2  # Calculate the average
    else:
        average = None  # Handle the case where bounds are not as expected

    # Check if data[8] is "N/A"
    if len(data) <= 8 or data[8] == 'N/A':
        return None  # Skip this entry by returning None

    # Extract and clean up the monetary value in data[8]
    monetary_value_str = data[8].replace('$', '').replace(',', '').strip()
    try:
        monetary_value = float(monetary_value_str)
    except ValueError:
        raise ValueError(f"Monetary value format is incorrect: '{data[8]}'")

    # Divide average by monetary_value if both are available and monetary_value is not zero
    if average is not None and monetary_value != 0:
        adjusted_size = average / monetary_value
    else:
        adjusted_size = None  # Handle division by zero or missing size

    size = round(adjusted_size)

    # Return the Web_Data instance
    return Web_Data(name, party, branch, state, traded_issuer, ticker, publish_date, trade_type, size)


def insert_trade_data(trade):
    # Convert TradeData object to dictionary, if using to_dict() method
    trade_data = trade.to_dict()
    
    # Insert data into the trades table
    cursor_trades.execute('''
        INSERT INTO trades (name, party, branch, state, traded_issuer, ticker, publish_date, trade_type, size)
        VALUES (:name, :party, :branch, :state, :traded_issuer, :ticker, :publish_date, :trade_type, :size)
    ''', trade_data)
    conn_trades.commit()
