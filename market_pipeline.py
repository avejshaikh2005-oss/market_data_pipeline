import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime 

class Marketdatapipeline:
    """
    Automated python and SQL Data pipeline.
    Fatches real-time market data, cleans it, stores it in SQL, and generates a utomated analytics reports.
    """
    def __init__(self, ticker="GC=F", db_name="market_data.db"):
        self.ticker = ticker
        self.db_name = db_name

    def extract_data(self, period="3mo", interval="1d"):
        """step 1: data ingestion (python API extraction)"""
        print(f"\n[INFO] {datetime.now().strftime('%Y-%m-%d %H:%M:%S') } - fetching data for {self.ticker}...")
        try:
            stock = yf.Ticker(self.ticker)
            df = stock.history(period=period, interval=interval)
            df.reset_index(inplace=True)
            df.columns = [col.lower().replace(" ","_") for col in df.columns]
            print(f"[success] extracted {len(df)} records successfully.")
            return df
        except Exception as e:
            print(f"[ERROR] extraction failed: {e}")
            return None

    def load_to_database(self, df):
        """step 2: SQL storage (relational database load )"""
        if df is None or df.empty:
            print("[WARNING] no data to store in database .")
            return

        print(f"[INFO] saving records into SQLite database ({self.db_name})...")
        conn = sqlite3.connect(self.db_name)
        df.to_sql('market_prices', conn, if_exists='replace', index=False)
        conn.close()
        print("[SUCCESS] data stored into SQL table 'market_prices'.")

    def analyze_data(self):
        """step 3: data analysis & feature engineering (pandas + SQL)"""
        print(f"[INFO] quering SQL database for analysis...")
        conn = sqlite3.connect(self.db_name)
        query="select date, open, high, low, close, volume from market_prices"
        df =  pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            print("[ERROR] no data found in database.")
            return

        #feature engineering (pandas calculations)
        df['date'] = pd.to_datetime(df['date'])
        df['daily_return_pct'] = df['close'].pct_change() * 100
        df['moving_avg_7'] = df['close'].rolling(window=7).mean()
        df['volatility_7d'] = df['daily_return_pct'].rolling(window=7).std()

        # summary metrics
        latest_close = df['close'].iloc[-1]
        highest_price = df['high'].max()
        avg_volume = df['volume'].mean()
        recent_volatility = df['volatility_7d'].iloc[-1]

        # summary report
        print("\n" + "="*50)
        print("   AUTOMATED MARKET ANALYSIS REPORT   ")
        print("="*50)
        print(f"asset tracked : {self.ticker}")
        print(f"latest closing price : ${latest_close:.2f}")
        print(f"period high price : ${highest_price:.2f}")
        print(f"average daily vilume : {avg_volume:,.0f}")
        print(f"7-day volatility (risk) : {recent_volatility:.2f}%")
        print("="*50)
        print("\n[PREVIEW] recent 3 days processed data:")
        print(df[['date', 'close', 'daily_return_pct', 'moving_avg_7']].tail(3).to_string(index=False))
        print("="*50)


if __name__ == "__main__":
    # initialize and execute pipeline
    pipeline = Marketdatapipeline(ticker="GC=F")
    raw_data = pipeline.extract_data(period="3mo")
    pipeline.load_to_database(raw_data)
    pipeline.analyze_data()

