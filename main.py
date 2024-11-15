import webScraper as ws
import politician_adder as pa
from bs4 import BeautifulSoup
import time

def main():
    x = 1
    while True:
        # Connect to the page and scrape data
        driver = ws.Connect_To_Website_Page(x)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()  # Close the driver after fetching the page
        

        # Find and process table rows from the page
        coulmn_data = soup.find_all('tr')
        for row in coulmn_data[1:]:  # Skip the header row
            row_data = row.find_all('td')
            individual_row_data = [data.text.strip() for data in row_data]
            traded = ws.format_trade_data(individual_row_data)
            if traded is None:
                print("Skipping entry with N/A monetary value.")
            else:
                ws.insert_trade_data(traded)


        # Update summary database with the trades from the current page
        pa.update_summary()

        # Save the last trade from the current page's trades
        pa.save_last_trade()


        # Clear the trades database before moving to the next page
        ws.cursor_trades.execute("DELETE FROM trades")
        ws.conn_trades.commit()

        # Move to the next page
        x += 1
        time.sleep(5)  # Delay for courtesy to avoid overloading the server

if __name__ == "__main__":
    main()
