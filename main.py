import pandas as pd
import yfinance as yf
import requests
from datetime import datetime
import pytz

REPORT_FILE = "report.txt"
report_lines = []

def log(line=""):
    report_lines.append(line)

def plus(val):
    return '+' if val > 0 else ''

def market_open():
    india = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india)

    return (
        now.weekday() < 5 and
        (now.hour > 9 or (now.hour == 9 and now.minute >= 15)) and
        (now.hour < 15 or (now.hour == 15 and now.minute <= 30))
    )

print("Generating report...")

if market_open():
    log("⚡ Using LIVE intraday prices")
else:
    log("✅ Using official closing prices")

PORTFOLIO_FILE = "portfolio.csv"

# ==============================
# INDEX TICKERS
# ==============================

NIFTY_TICKER = "^NSEI"
SENSEX_TICKER = "^BSESN"
MIDCAP_TICKER = "NIFTY_MIDCAP_100.NS"
SMALLCAP_TICKER = "NIFTYSMLCAP250.NS"

# ==============================
# SECTOR TICKERS
# ==============================

NIFTY_IT_TICKER = "^CNXIT"
NIFTY_BANK_TICKER = "^NSEBANK"
NIFTY_AUTO_TICKER = "^CNXAUTO"
NIFTY_METAL_TICKER = "^CNXMETAL"
NIFTY_PSU_BANK_TICKER = "^CNXPSUBANK"
NIFTY_FMCG_TICKER = "^CNXFMCG"

# ---------------------------
# LOAD PORTFOLIO
# ---------------------------
portfolio = pd.read_csv(PORTFOLIO_FILE)
portfolio["YF_Ticker"] = portfolio["TICKER"] + ".NS"

tickers = list(portfolio["YF_Ticker"]) + [NIFTY_TICKER, SENSEX_TICKER, 
                                          MIDCAP_TICKER, SMALLCAP_TICKER,
                                            NIFTY_IT_TICKER, NIFTY_BANK_TICKER, 
                                            NIFTY_AUTO_TICKER, NIFTY_METAL_TICKER, 
                                            NIFTY_PSU_BANK_TICKER, NIFTY_FMCG_TICKER]

# ---------------------------
# DOWNLOAD DATA
# ---------------------------
data = yf.download(
    tickers,
    period="2d",
    interval="1d",
    group_by="ticker",
    progress=False
)

total_value_today = 0
total_value_yesterday = 0
total_cost = 0
results = []

for i, row in portfolio.iterrows():

    ticker = row["YF_Ticker"]
    qty = row["QUANTITY"]
    avg_price = row["AVG_PRICE"]

    try:
        close_today = data[ticker]["Close"].iloc[-1]
        close_yesterday = data[ticker]["Close"].iloc[-2]

        value_today = close_today * qty
        value_yesterday = close_yesterday * qty
        invested = avg_price * qty

        daily_pnl = value_today - value_yesterday
        total_pnl = value_today - invested
        daily_perc = (100 * (close_today - close_yesterday)) / close_yesterday
        total_perc = (100 * total_pnl) / invested

        total_value_today += value_today
        total_value_yesterday += value_yesterday
        total_cost += invested

        results.append({
            "ticker": row["TICKER"],
            "invested": invested,
            "value_today": value_today,
            "daily_pnl": daily_pnl,
            "daily_perc": daily_perc,
            "total_perc": total_perc
        })

    except Exception:
        log(f"Failed {row['TICKER']}")

# ---------------------------
# SORT BY DAILY %
# ---------------------------
results.sort(key=lambda x: x["daily_perc"], reverse=True)

# ---------------------------
# PRINT SORTED OUTPUT
# ---------------------------
log("\n📈 STOCK PERFORMANCE (Sorted by Day %)")
log("--------------------------------------")

for r in results:
    log(
        f"{r['ticker']:12} "
        f"Invested: ₹{r['invested']:,.0f} | "
        f"Today: ₹{r['value_today']:,.0f} | "
        f"Total %: {plus(r['total_perc'])}{r['total_perc']:,.2f}% | "
        f"Day P&L: ₹{r['daily_pnl']:,.2f} | "
        f"Day %: {plus(r['daily_perc'])}{r['daily_perc']:,.2f}%"
    )

# ---------------------------
# PORTFOLIO RETURNS
# ---------------------------
portfolio_return = (
    (total_value_today - total_value_yesterday)
    / total_value_yesterday
) * 100

total_profit = total_value_today - total_cost

# ---------------------------
# NIFTY RETURN
# ---------------------------
nifty_today = data[NIFTY_TICKER]["Close"].iloc[-1]
nifty_yesterday = data[NIFTY_TICKER]["Close"].iloc[-2]

nifty_return = (
    (nifty_today - nifty_yesterday) / nifty_yesterday
) * 100

alpha = portfolio_return - nifty_return

# ---------------------------
# MARKET STATUS
# ---------------------------
def get_market_status():
    url = "https://www.nseindia.com/api/marketStatus"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"
    }

    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)
    r = session.get(url, headers=headers)

    if r.status_code == 200:
        return r.json()["marketState"][0]["marketStatus"]

    return "Unavailable"

market_status = get_market_status()

# ---------------------------
# FINAL REPORT
# ---------------------------
log("\n===========================")
log("📊 DAILY PORTFOLIO REPORT")
log("===========================")
log(f"Date: {datetime.now().strftime('%Y-%m-%d')}")

log(f"\nPortfolio Cost: ₹{total_cost:,.0f}")
log(f"\nPortfolio Value: ₹{total_value_today:,.0f}")
log(f"Total Profit/Loss: {plus(total_profit)}₹{total_profit:,.0f}")

log(f"\n1D Nifty Return: {plus(nifty_return)}{nifty_return:.2f}%")
log(f"1D Portfolio Return: {plus(portfolio_return)}{portfolio_return:.2f}%")
log(f"Alpha vs Nifty: {plus(alpha)}{alpha:.2f}%")

log(f"\nMarket Status: {market_status}")

log("\n🧠 INTERPRETATION")

if alpha > 0:
    log("✅ Portfolio showing RELATIVE STRENGTH")
else:
    log("⚠️ Portfolio underperforming index")

if nifty_return < 0 and portfolio_return > 0:
    log("🔥 Excellent signal: Green portfolio on red market")

elif nifty_return > 0 and portfolio_return < 0:
    log("🚨 WARNING: Market up but portfolio lagging")

else:
    log("ℹ️ Neutral behaviour")


def index_change(symbol):
    global data

    close_today = data[symbol]["Close"].iloc[-1]
    close_yesterday = data[symbol]["Close"].iloc[-2]

    return 100 * (close_today - close_yesterday) / close_yesterday

log("\n===========================")
log("📊 INDEX CHECK")
log("===========================\n")

indices = {
    "Nifty 50": NIFTY_TICKER,
    "Sensex": SENSEX_TICKER,
    "Midcap Index": MIDCAP_TICKER,
    "Smallcap Index": SMALLCAP_TICKER,
}

results_index = {}

for name, symbol in indices.items():
    try:
        change = index_change(symbol)
        results_index[name] = change
        log(f"{name:15} → {plus(change)}{change:.2f}%")
    except:
        log(f"{name:15} → Failed")

# Interpretation
lc = results_index["Nifty 50"]
mc = results_index["Midcap Index"]
sc = results_index["Smallcap Index"]

if lc < 0 and (mc > 0 or sc > 0):
    log("\n🟢 Risk-On Market (money moving to mid/small caps)")
elif mc < 0 and sc < 0:
    log("\n🔴 Smart money cautious")

log("\n===========================")
log("📈 MARKET BREADTH")
log("===========================\n")

NSE_HOME = "https://www.nseindia.com"
ADV_DEC_API = "https://www.nseindia.com/api/live-analysis-advance"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json",
}

session = requests.Session()
session.get(NSE_HOME, headers=headers)
response = session.get(ADV_DEC_API, headers=headers)

advance_data = response.json()

advances = advance_data["advance"]["count"]["Advances"]
declines = advance_data["advance"]["count"]["Declines"]
unchanged = advance_data["advance"]["count"]["Unchange"]
total = advance_data["advance"]["count"]["Total"]

log(f"Advances  : {advances}")
log(f"Declines  : {declines}")
log(f"Unchanged : {unchanged}")
log(f"Total     : {total}\n")

# Interpretation
if advances > declines:
    log("✅ Risk ON — money entering market")
else:
    log("⚠️ Risk OFF — distribution phase")

log("\n===========================")
log("🏭 SECTOR STRENGTH")
log("===========================\n")

SECTOR_TICKERS = {
    "IT": NIFTY_IT_TICKER,
    "Banking": NIFTY_BANK_TICKER,
    "Auto": NIFTY_AUTO_TICKER,
    "Metal": NIFTY_METAL_TICKER,
    "PSU Bank": NIFTY_PSU_BANK_TICKER,
    "FMCG": NIFTY_FMCG_TICKER,
}

sector_perf = []

for name, symbol in SECTOR_TICKERS.items():
    try:
        change = index_change(symbol)
        sector_perf.append((name, change))
    except:
        pass

sector_perf.sort(key=lambda x: x[1], reverse=True)

log("Top 3 sectors today:")
top3 = sector_perf[:3]

for s in top3:
    log(f"{s[0]} → {s[1]:.2f}%")   
     
log("\n===========================")

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    for line in report_lines:
        f.write(line + "\n")

print("✅ Report written to report.txt")