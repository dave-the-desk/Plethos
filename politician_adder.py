import sqlite3
import re
from webScraper import cursor_trades, conn_trades

# Connect to the persistent summary database
conn_summary = sqlite3.connect('summary.db')
cursor_summary = conn_summary.cursor()

# Create the main summary table
cursor_summary.execute('''
    CREATE TABLE IF NOT EXISTS summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        party TEXT,
        branch TEXT,
        state TEXT
    )
''')
conn_summary.commit()

def create_politician_tables(name):
    """Creates unique history and stocks tables for each politician."""
    sanitized_name = re.sub(r'\s+', '_', name)  # Replace spaces with underscores for table names
    
    # Create history table for the politician
    cursor_summary.execute(f'''
        CREATE TABLE IF NOT EXISTS {sanitized_name}_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_type TEXT,
            stock TEXT,
            ticker TEXT,
            size TEXT,
            date TEXT
        )
    ''')
    
    # Create stocks table for the politician
    cursor_summary.execute(f'''
        CREATE TABLE IF NOT EXISTS {sanitized_name}_stocks (
            stock TEXT PRIMARY KEY,
            ticker TEXT,
            traded_issuer TEXT,
            size TEXT
        )
    ''')
    conn_summary.commit()

def update_politician_tables(name, trade_type, stock, ticker, traded_issuer, size, date):
    """Updates the individual tables for the politician's history and stocks."""
    sanitized_name = re.sub(r'\s+', '_', name)

    # Update the politician's trade history
    cursor_summary.execute(f'''
        INSERT INTO {sanitized_name}_history (trade_type, stock, ticker, size, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (trade_type, stock, ticker, size, date))
    
    # Check if the stock is already in the politician's current stocks
    cursor_summary.execute(f'''
        SELECT size FROM {sanitized_name}_stocks WHERE stock = ?
    ''', (stock,))
    current_stock = cursor_summary.fetchone()

    if trade_type.lower() == 'buy':
        if current_stock:
            # Stock exists; update the size by adding the new size
            new_size = len(current_stock[0]) + len(size)
            cursor_summary.execute(f'''
                UPDATE {sanitized_name}_stocks
                SET size = ?, ticker = ?, traded_issuer = ?
                WHERE stock = ?
            ''', (new_size, ticker, traded_issuer, stock))
        else:
            # Stock does not exist; insert new stock with initial size
            cursor_summary.execute(f'''
                INSERT INTO {sanitized_name}_stocks (stock, ticker, traded_issuer, size)
                VALUES (?, ?, ?, ?)
            ''', (stock, ticker, traded_issuer, size))

    elif trade_type.lower() == 'sell':
        if current_stock:
            # Stock exists; subtract the size
            new_size = len(current_stock[0]) -len( size)
            if new_size > 0:
                # Update the stock with the new size if still positive
                cursor_summary.execute(f'''
                    UPDATE {sanitized_name}_stocks
                    SET size = ?
                    WHERE stock = ?
                ''', (new_size, stock))
            else:
                # Remove the stock from current stocks if size is zero or negative
                cursor_summary.execute(f'''
                    DELETE FROM {sanitized_name}_stocks
                    WHERE stock = ?
                ''', (stock,))

    conn_summary.commit()

def update_summary():
    """Main function to update the summary database with trade data from trades."""
    # Get all trades from the in-memory trades database
    cursor_trades.execute("SELECT * FROM trades ORDER BY id DESC")
    trades = cursor_trades.fetchall()
    
    # Process each trade and update both summary and individual politician tables
    for trade in trades:
        _, name, party, branch, state, traded_issuer, ticker, publish_date, trade_type, size = trade
        
        # Insert/update the individual’s info in the summary table
        cursor_summary.execute('''
            INSERT OR IGNORE INTO summary (name, party, branch, state)
            VALUES (?, ?, ?, ?)
        ''', (name, party, branch, state))
        
        # Ensure tables for this politician exist
        create_politician_tables(name)
        
        # Update the individual politician’s history and stock tables
        update_politician_tables(name, trade_type, traded_issuer, ticker, traded_issuer, size, publish_date)
    
    conn_summary.commit()

def save_last_trade():
    """Saves the last trade from the trades database into a separate table."""
    cursor_trades.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 1")
    last_trade = cursor_trades.fetchone()
    
    if last_trade:
        # Create last_trade table if it doesn’t exist
        cursor_summary.execute('''
            CREATE TABLE IF NOT EXISTS last_trade (
                id INTEGER PRIMARY KEY,
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
        
        # Clear previous last trade entry and insert the latest one
        cursor_summary.execute('DELETE FROM last_trade')
        cursor_summary.execute('''
            INSERT INTO last_trade (id, name, party, branch, state, traded_issuer, ticker, publish_date, trade_type, size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', last_trade)
        
        conn_summary.commit()

        return last_trade
