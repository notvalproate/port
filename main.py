import os
import locale
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime
import pytz

now = datetime.now(pytz.timezone("Asia/Kolkata"))

REPORT_DIR = "reports"
TXT_REPORT_DIR = "reports/txt"
DAILY_REPORT_FILE = f"{now.strftime('%Y_%m_%d')}.txt"
DAILY_HTML_FILE = f"{now.strftime('%Y_%m_%d')}.html"
REPORT_FILE = "latest.txt"
HTML_REPORT_FILE = "latest.html"
report_lines = []

def log(line=""):
    report_lines.append(line)

def plus(val):
    return '+' if val > 0 else ''

def minus(val):
    return '+' if val > 0 else '-'

def market_open():
    global now
    return (
        now.weekday() < 5 and
        (now.hour > 9 or (now.hour == 9 and now.minute >= 15)) and
        (now.hour < 15 or (now.hour == 15 and now.minute <= 30))
    )

print("Generating report...")

is_live = market_open()
if is_live:
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
SMALLCAP_TICKER = "NIFTYSMLCAP50.NS"

# ==============================
# SECTOR TICKERS
# ==============================
NIFTY_AUTO_TICKER = "^CNXAUTO"
NIFTY_FIN_TICKER = "NIFTY_FIN_SERVICE.NS"
NIFTY_IT_TICKER = "^CNXIT"
NIFTY_MEDIA_TICKER = "^CNXMEDIA"
NIFTY_METAL_TICKER = "^CNXMETAL"
NIFTY_PHARMA_TICKER = "^CNXPHARMA"
NIFTY_BANK_TICKER = "^NSEBANK"
NIFTY_PSU_BANK_TICKER = "^CNXPSUBANK"
NIFTY_REALTY_TICKER = "^CNXREALTY"
NIFTY_FMCG_TICKER = "^CNXFMCG"

SECTOR_TICKER_LIST = [
    NIFTY_AUTO_TICKER, NIFTY_FIN_TICKER, NIFTY_IT_TICKER, NIFTY_MEDIA_TICKER,
    NIFTY_METAL_TICKER, NIFTY_PHARMA_TICKER, NIFTY_BANK_TICKER,
    NIFTY_PSU_BANK_TICKER, NIFTY_REALTY_TICKER, NIFTY_FMCG_TICKER,
]

# ---------------------------
# LOAD PORTFOLIO
# ---------------------------
portfolio = pd.read_csv(PORTFOLIO_FILE)
portfolio["YF_Ticker"] = portfolio["TICKER"] + ".NS"

tickers = list(portfolio["YF_Ticker"]) + [NIFTY_TICKER, SENSEX_TICKER,
                                          MIDCAP_TICKER, SMALLCAP_TICKER] + SECTOR_TICKER_LIST

# ---------------------------
# DOWNLOAD DATA
# ---------------------------
DATA_PERIOD_IN_DAYS = 6

data = yf.download(
    tickers,
    period=f"{DATA_PERIOD_IN_DAYS}d",
    interval="1d",
    group_by="ticker",
    progress=False
)

total_value_today = 0
total_value_yesterday = 0
total_value_3d = 0
total_value_5d = 0
total_cost = 0
results = []

for i, row in portfolio.iterrows():
    ticker = row["YF_Ticker"]
    qty = row["QUANTITY"]
    avg_price = row["AVG_PRICE"]

    try:
        close_today = data[ticker]["Close"].iloc[-1]
        close_yesterday = data[ticker]["Close"].iloc[-2]
        close_3d = data[ticker]["Close"].iloc[-4]
        close_5d = data[ticker]["Close"].iloc[-6]

        value_today = close_today * qty
        value_yesterday = close_yesterday * qty
        value_3d = close_3d * qty
        value_5d = close_5d * qty
        invested = avg_price * qty

        daily_pnl = value_today - value_yesterday
        total_pnl = value_today - invested
        daily_perc = (100 * (close_today - close_yesterday)) / close_yesterday
        total_perc = (100 * total_pnl) / invested

        total_value_today += value_today
        total_value_yesterday += value_yesterday
        total_value_3d += value_3d
        total_value_5d += value_5d
        total_cost += invested

        results.append({
            "ticker": row["TICKER"],
            "invested": invested,
            "value_today": value_today,
            "daily_pnl": daily_pnl,
            "total_pnl": total_pnl,
            "daily_perc": daily_perc,
            "total_perc": total_perc,
            "share": 100 * (invested / total_cost) if total_cost > 0 else 0
        })

    except Exception:
        log(f"Failed {row['TICKER']}")

# Recalculate share percentages after total_cost is known
for r in results:
    r["share"] = 100 * (r["invested"] / total_cost) if total_cost > 0 else 0

# ---------------------------
# SORT BY DAILY %
# ---------------------------
results.sort(key=lambda x: x["daily_perc"], reverse=True)

# ---------------------------
# PRINT SORTED OUTPUT (TXT)
# ---------------------------
log(f"\n📈 STOCK PERFORMANCE | {now.strftime('%d/%m/%Y')} | (Sorted by Day %)\n")
log("---------------------------------------------------------------------------------------------")
log(f"TICKER     ||  SHARE || Invested ||    Today ||        Day | Total P&L  ||    Day% | Total%")
log("---------------------------------------------------------------------------------------------")

loser_line = False
for r in results:
    if r['daily_perc'] < 0 and not loser_line:
        loser_line = True
        log("----------------------------------------TODAY'S LOSERS---------------------------------------")

    daily_perc_text = f"{plus(r['daily_perc'])}{r['daily_perc']:,.2f}%"
    total_perc_text = f"{plus(r['total_perc'])}{r['total_perc']:,.2f}%"

    log(
        f"{r['ticker']:10} || "
        f"{r['share']:>5,.2f}% || "
        f"{f'₹{r["invested"]:,.0f}':>8} || "
        f"{f'₹{r["value_today"]:,.0f}':>8} || "
        f"{f'₹{r["daily_pnl"]:,.2f}':>10} | {f'₹{r["total_pnl"]:,.2f}':<10} || "
        f"{daily_perc_text:>7} | {total_perc_text:>7}"
    )

log("---------------------------------------------------------------------------------------------")

# ---------------------------
# PORTFOLIO RETURNS
# ---------------------------
portfolio_return_amt = total_value_today - total_value_yesterday
portfolio_return = (portfolio_return_amt / total_value_yesterday) * 100

portfolio_return_amt_3d = total_value_today - total_value_3d
portfolio_return_3d = (portfolio_return_amt_3d / total_value_3d) * 100

portfolio_return_amt_5d = total_value_today - total_value_5d
portfolio_return_5d = (portfolio_return_amt_5d / total_value_5d) * 100

total_profit = total_value_today - total_cost
total_profit_perc = (total_profit * 100) / total_cost

# ---------------------------
# NIFTY RETURN
# ---------------------------
nifty_today = data[NIFTY_TICKER]["Close"].iloc[-1]
nifty_yesterday = data[NIFTY_TICKER]["Close"].iloc[-2]
nifty_3d = data[NIFTY_TICKER]["Close"].iloc[-4]
nifty_5d = data[NIFTY_TICKER]["Close"].iloc[-6]

nifty_return = ((nifty_today - nifty_yesterday) / nifty_yesterday) * 100
nifty_return_3d = ((nifty_today - nifty_3d) / nifty_3d) * 100
nifty_return_5d = ((nifty_today - nifty_5d) / nifty_5d) * 100

alpha = portfolio_return - nifty_return
alpha_3d = portfolio_return_3d - nifty_return_3d
alpha_5d = portfolio_return_5d - nifty_return_5d

participation = (portfolio_return / nifty_return) * 100 if nifty_return != 0 else 0
participation_3d = (portfolio_return_3d / nifty_return_3d) * 100 if nifty_return_3d != 0 else 0
participation_5d = (portfolio_return_5d / nifty_return_5d) * 100 if nifty_return_5d != 0 else 0

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
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers)
        r = session.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()["marketState"][0]["marketStatus"]
    except:
        pass
    return "Unavailable"

def get_higher_lower(nifty_return_rate):
    return "(Higher is Better)" if nifty_return_rate >= 0 else "(Lower is Better)"

market_status = get_market_status()

# ---------------------------
# FINAL REPORT (TXT)
# ---------------------------
locale.setlocale(locale.LC_ALL, "en_IN.UTF-8")

log("\n===========================")
log("📊 DAILY PORTFOLIO REPORT")
log("===========================")
log(f"Date: {now.strftime('%Y-%m-%d')}")

log(f"\nPortfolio Cost: ₹{locale.format_string('%d', total_cost, grouping=True)}")
log(f"Portfolio Value: ₹{locale.format_string('%d', total_value_today, grouping=True)}")

log(f"\n1D Profit/Loss: {plus(portfolio_return_amt)}₹{locale.format_string('%d', portfolio_return_amt, grouping=True)}")
log(f"Total Profit/Loss: {plus(total_profit)}₹{locale.format_string('%d', total_profit, grouping=True)}")
log(f"Total P/L %: {plus(total_profit_perc)}{total_profit_perc:.2f}%")

log(f"\n1D Nifty Return: {plus(nifty_return)}{nifty_return:.2f}%")
log(f"1D Portfolio Return: {plus(portfolio_return)}{portfolio_return:.2f}%")
log(f"Alpha vs Nifty: {plus(alpha)}{alpha:.2f}%")
log(f"Participation: {plus(participation)}{participation:.2f}% {get_higher_lower(nifty_return)}")

log(f"\n3D Nifty Return: {plus(nifty_return_3d)}{nifty_return_3d:.2f}%")
log(f"3D Portfolio Return: {plus(portfolio_return_3d)}{portfolio_return_3d:.2f}%")
log(f"3D Alpha vs Nifty: {plus(alpha_3d)}{alpha_3d:.2f}%")
log(f"3D Participation: {plus(participation_3d)}{participation_3d:.2f}% {get_higher_lower(nifty_return_3d)}")

log(f"\n5D Nifty Return: {plus(nifty_return_5d)}{nifty_return_5d:.2f}%")
log(f"5D Portfolio Return: {plus(portfolio_return_5d)}{portfolio_return_5d:.2f}%")
log(f"5D Alpha vs Nifty: {plus(alpha_5d)}{alpha_5d:.2f}%")
log(f"5D Participation: {plus(participation_5d)}{participation_5d:.2f}% {get_higher_lower(nifty_return_5d)}")

log(f"\nMarket Status: {market_status}")

log("\n🧠 INTERPRETATION")

interpretation_txt = []
if alpha > 0:
    interpretation_txt.append("✅ Portfolio showing RELATIVE STRENGTH")
else:
    interpretation_txt.append("⚠️ Portfolio underperforming index")

if nifty_return < 0 and portfolio_return > 0:
    interpretation_txt.append("🔥 Excellent signal: Green portfolio on red market")
elif nifty_return > 0 and portfolio_return < 0:
    interpretation_txt.append("🚨 WARNING: Market up but portfolio lagging")
else:
    interpretation_txt.append("ℹ️ Neutral behaviour")

for line in interpretation_txt:
    log(line)

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

# Index Interpretation
lc = results_index.get("Nifty 50", 0)
mc = results_index.get("Midcap Index", 0)
sc = results_index.get("Smallcap Index", 0)

index_interpretation = ""
if lc < 0 and (mc > 0 or sc > 0):
    index_interpretation = "🟢 Risk-On Market (money moving to mid/small caps)"
    log(f"\n{index_interpretation}")
elif mc < 0 and sc < 0:
    index_interpretation = "🔴 Smart money cautious"
    log(f"\n{index_interpretation}")

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
breadth_interpretation = "⚠️ Risk OFF — distribution phase"

if advances > declines:
    breadth_interpretation = "✅ Risk ON — money entering market"

log(breadth_interpretation)

log("\n===========================")
log("🏭 SECTOR STRENGTH")
log("===========================\n")

SECTOR_TICKERS = {
    "Auto": NIFTY_AUTO_TICKER,
    "Finance": NIFTY_FIN_TICKER,
    "IT": NIFTY_IT_TICKER,
    "Media": NIFTY_MEDIA_TICKER,
    "Metal": NIFTY_METAL_TICKER,
    "Pharma": NIFTY_PHARMA_TICKER,
    "Banking": NIFTY_BANK_TICKER,
    "PSU Banking": NIFTY_PSU_BANK_TICKER,
    "Realty": NIFTY_REALTY_TICKER,
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

log("Sector-wise performance today:")
for s in sector_perf:
    log(f"{s[0]:12} → {s[1]:.2f}%")

log("\n===========================")

# ---------------------------
# WRITE TXT REPORTS
# ---------------------------
os.makedirs(TXT_REPORT_DIR, exist_ok=True)
report_path = os.path.join(TXT_REPORT_DIR, REPORT_FILE)
daily_report_path = os.path.join(TXT_REPORT_DIR, DAILY_REPORT_FILE)

with open(report_path, "w", encoding="utf-8") as f:
    for line in report_lines:
        f.write(line + "\n")

with open(daily_report_path, "w", encoding="utf-8") as f:
    for line in report_lines:
        f.write(line + "\n")

print("✅ TXT Report written")

# ==============================================================================
# HTML REPORT GENERATION
# ==============================================================================

def color_class(val):
    """Return CSS class based on positive/negative value."""
    if val > 0:
        return "positive"
    elif val < 0:
        return "negative"
    return "neutral"

def format_currency(val):
    """Format number as Indian currency."""
    return f"₹{locale.format_string('%d', val, grouping=True)}"

def format_percent(val):
    """Format percentage with sign."""
    sign = '+' if val > 0 else ''
    return f"{sign}{val:.2f}%"

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Report - {now.strftime('%d %b %Y')}</title>
    <style>
        :root {{
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --bg-tertiary-hover: #363e49;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --border-color: #30363d;
            --positive: #3fb950;
            --negative: #f85149;
            --neutral: #8b949e;
            --accent: #58a6ff;
            --accent-hover: #80bbff;
            --warning: #d29922;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 30px;
        }}
        
        header h1 {{
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        header .date {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}
        
        header .status {{
            display: inline-block;
            margin-top: 15px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        header .status.live {{
            background: rgba(63, 185, 80, 0.15);
            color: var(--positive);
            border: 1px solid var(--positive);
        }}
        
        header .status.closed {{
            background: rgba(139, 148, 158, 0.15);
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
        }}
        
        .card h2 {{
            font-size: 1rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .card h2 .icon {{
            font-size: 1.2rem;
        }}
        
        .stat {{
            margin-bottom: 16px;
        }}
        
        .stat:last-child {{
            margin-bottom: 0;
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-bottom: 4px;
        }}
        
        .stat-value {{
            font-size: 1.5rem;
            font-weight: 600;
        }}
        
        .stat-value.large {{
            font-size: 2rem;
        }}
        
        .positive {{
            color: var(--positive);
        }}
        
        .negative {{
            color: var(--negative);
        }}
        
        .neutral {{
            color: var(--neutral);
        }}
        
        .comparison {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }}
        
        .comparison-item {{
            text-align: center;
            padding: 16px;
            background: var(--bg-tertiary);
            border-radius: 8px;
        }}
        
        .comparison-item .period {{
            color: var(--text-secondary);
            font-size: 0.8rem;
            margin-bottom: 8px;
        }}
        
        .comparison-item .value {{
            font-size: 1.1rem;
            font-weight: 600;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        
        th {{
            text-align: left;
            padding: 12px 16px;
            background: var(--bg-tertiary);
            color: var(--text-secondary);
            font-weight: 500;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        th:first-child {{
            border-radius: 8px 0 0 0;
        }}
        
        th:last-child {{
            border-radius: 0 8px 0 0;
        }}
        
        td {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        tr:hover td {{
            background: var(--bg-tertiary);
        }}
        
        .ticker {{
            font-weight: 600;
        }}

        .ticker a {{
            text-decoration: none;
            color: var(--accent);
            transition: 200ms;
        }}

        .ticker a:hover {{
            color: var(--accent-hover);
            cursor: pointer;
        }}
        
        .loser-divider {{
            background: rgba(248, 81, 73, 0.1);
        }}
        
        .loser-divider td {{
            color: var(--negative);
            font-weight: 500;
            text-align: center;
            padding: 8px;
            font-size: 0.8rem;
        }}
        
        .interpretation {{
            padding: 20px;
            background: var(--bg-tertiary);
            border-radius: 8px;
            margin-top: 20px;
        }}
        
        .interpretation p {{
            margin-bottom: 8px;
        }}
        
        .interpretation p:last-child {{
            margin-bottom: 0;
        }}
        
        .sector-bar {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .sector-bar:last-child {{
            margin-bottom: 0;
        }}
        
        .sector-name {{
            width: 100px;
            font-size: 0.9rem;
        }}
        
        .sector-bar-container {{
            flex: 1;
            height: 24px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }}
        
        .sector-bar-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }}
        
        .sector-bar-fill.positive {{
            background: linear-gradient(90deg, var(--positive), rgba(63, 185, 80, 0.5));
        }}
        
        .sector-bar-fill.negative {{
            background: linear-gradient(90deg, var(--negative), rgba(248, 81, 73, 0.5));
        }}
        
        .sector-value {{
            width: 70px;
            text-align: right;
            font-weight: 500;
            font-size: 0.9rem;
        }}
        
        .breadth-visual {{
            display: flex;
            height: 40px;
            border-radius: 8px;
            overflow: hidden;
            margin: 20px 0;
        }}
        
        .breadth-advances {{
            background: var(--positive);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
        }}

        .breadth-unchanged {{
            background: var(--neutral);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
        }}
        
        .breadth-declines {{
            background: var(--negative);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
        }}
        
        .index-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}
        
        .index-item {{
            padding: 16px;
            background: var(--bg-tertiary);
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: var(--text-primary);
            transition: 200ms;
        }}

        .index-item:hover {{
            background: var(--bg-tertiary-hover);
        }}
        
        .index-name {{
            font-weight: 500;
        }}
        
        .index-value {{
            font-weight: 600;
            font-size: 1.1rem;
        }}
        
        footer {{
            text-align: center;
            padding: 30px 0;
            color: var(--text-secondary);
            font-size: 0.85rem;
            border-top: 1px solid var(--border-color);
            margin-top: 30px;
        }}
        
        @media (max-width: 768px) {{
            .comparison {{
                grid-template-columns: 1fr;
            }}
            
            .index-grid {{
                grid-template-columns: 1fr;
            }}
            
            table {{
                font-size: 0.8rem;
            }}
            
            th, td {{
                padding: 10px 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Portfolio Report</h1>
            <div class="date">{now.strftime('%A, %d %B %Y')}</div>
            <div class="status {'live' if is_live else 'closed'}">
                {'⚡ LIVE — Market Open' if is_live else '✅ Using Closing Prices'}
            </div>
        </header>
        
        <!-- Portfolio Summary -->
        <div class="grid">
            <div class="card">
                <h2><span class="icon">💰</span> Portfolio Value</h2>
                <div class="stat">
                    <div class="stat-label">Current Value</div>
                    <div class="stat-value large">{format_currency(total_value_today)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Total Invested</div>
                    <div class="stat-value">{format_currency(total_cost)}</div>
                </div>
            </div>
            
            <div class="card">
                <h2><span class="icon">📈</span> Total Returns</h2>
                <div class="stat">
                    <div class="stat-label">Profit/Loss</div>
                    <div class="stat-value large {color_class(total_profit)}">{minus(total_profit)}{format_currency(abs(total_profit))}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Return %</div>
                    <div class="stat-value {color_class(total_profit_perc)}">{format_percent(total_profit_perc)}</div>
                </div>
            </div>
            
            <div class="card">
                <h2><span class="icon">📅</span> Today's Change</h2>
                <div class="stat">
                    <div class="stat-label">Day P&L</div>
                    <div class="stat-value large {color_class(portfolio_return_amt)}">{minus(portfolio_return_amt)}{format_currency(abs(portfolio_return_amt))}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Day Return %</div>
                    <div class="stat-value {color_class(portfolio_return)}">{format_percent(portfolio_return)}</div>
                </div>
            </div>
        </div>
        
        <!-- Performance Comparison -->
        <div class="card" style="margin-bottom: 30px;">
            <h2><span class="icon">⚖️</span> Portfolio vs Nifty 50</h2>
            <div class="comparison">
                <div class="comparison-item">
                    <div class="period">1 Day</div>
                    <div class="value {color_class(portfolio_return)}">Portfolio: {format_percent(portfolio_return)}</div>
                    <div class="value {color_class(nifty_return)}" style="margin-top: 4px;">Nifty: {format_percent(nifty_return)}</div>
                    <div class="value {color_class(alpha)}" style="margin-top: 8px; font-size: 0.9rem;">Alpha: {format_percent(alpha)}</div>
                    <div class="value" style="margin-top: 8px; font-size: 0.8rem; opacity: 80%;">Participation: {format_percent(participation)}</div>
                    <div class="value" style="margin-top: 8px; font-size: 0.8rem; opacity: 40%;">{get_higher_lower(nifty_return)}</div>
                </div>
                <div class="comparison-item">
                    <div class="period">3 Days</div>
                    <div class="value {color_class(portfolio_return_3d)}">Portfolio: {format_percent(portfolio_return_3d)}</div>
                    <div class="value {color_class(nifty_return_3d)}" style="margin-top: 4px;">Nifty: {format_percent(nifty_return_3d)}</div>
                    <div class="value {color_class(alpha_3d)}" style="margin-top: 8px; font-size: 0.9rem;">Alpha: {format_percent(alpha_3d)}</div>
                    <div class="value" style="margin-top: 8px; font-size: 0.8rem; opacity: 80%;">Participation: {format_percent(participation_3d)}</div>
                    <div class="value" style="margin-top: 8px; font-size: 0.8rem; opacity: 40%;">{get_higher_lower(nifty_return_3d)}</div>
                </div>
                <div class="comparison-item">
                    <div class="period">5 Days</div>
                    <div class="value {color_class(portfolio_return_5d)}">Portfolio: {format_percent(portfolio_return_5d)}</div>
                    <div class="value {color_class(nifty_return_5d)}" style="margin-top: 4px;">Nifty: {format_percent(nifty_return_5d)}</div>
                    <div class="value {color_class(alpha_5d)}" style="margin-top: 8px; font-size: 0.9rem;">Alpha: {format_percent(alpha_5d)}</div>
                    <div class="value" style="margin-top: 8px; font-size: 0.8rem; opacity: 80%;">Participation: {format_percent(participation_5d)}</div>
                    <div class="value" style="margin-top: 8px; font-size: 0.8rem; opacity: 40%;">{get_higher_lower(nifty_return_5d)}</div>
                </div>
            </div>
            <div class="interpretation">
                {''.join(f'<p>{line}</p>' for line in interpretation_txt)}
            </div>
        </div>
        
        <!-- Stock Performance Table -->
        <div class="card" style="margin-bottom: 30px; overflow-x: auto;">
            <h2><span class="icon">📋</span> Stock Performance (Sorted by Day %)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Share</th>
                        <th>Invested</th>
                        <th>Current</th>
                        <th>Day P&L</th>
                        <th>Total P&L</th>
                        <th>Day %</th>
                        <th>Total %</th>
                    </tr>
                </thead>
                <tbody>
"""

# Add stock rows
loser_divider_added = False
for r in results:
    if r['daily_perc'] < 0 and not loser_divider_added:
        loser_divider_added = True
        html_content += """
                    <tr class="loser-divider">
                        <td colspan="8">📉 TODAY'S LOSERS</td>
                    </tr>
"""
    
    html_content += f"""
                    <tr>
                        <td class="ticker"><a target="_blank" href="https://in.tradingview.com/symbols/NSE-{r['ticker']}">{r['ticker']}</a></td>
                        <td>{r['share']:.1f}%</td>
                        <td>{format_currency(r['invested'])}</td>
                        <td>{format_currency(r['value_today'])}</td>
                        <td class="{color_class(r['daily_pnl'])}">{minus(r['daily_pnl'])}{format_currency(abs(r['daily_pnl']))}</td>
                        <td class="{color_class(r['total_pnl'])}">{minus(r['total_pnl'])}{format_currency(abs(r['total_pnl']))}</td>
                        <td class="{color_class(r['daily_perc'])}">{format_percent(r['daily_perc'])}</td>
                        <td class="{color_class(r['total_perc'])}">{format_percent(r['total_perc'])}</td>
                    </tr>
"""

html_content += """
                </tbody>
            </table>
        </div>
        
        <div class="grid">
"""

# Index Check Card
html_content += """
            <div class="card">
                <h2><span class="icon">📊</span> Index Performance</h2>
                <div class="index-grid">
"""

urls = [
    "https://in.tradingview.com/symbols/NSE-NIFTY",
    "https://in.tradingview.com/symbols/BSE-SENSEX",
    "https://in.tradingview.com/symbols/NSE-CNXMIDCAP",
    "https://in.tradingview.com/symbols/NSE-CNXSMALLCAP"
]
url_index = 0

for name, change in results_index.items():
    html_content += f"""
                    <a style="text-decoration: none;" href="{urls[url_index]}" target="_blank">
                        <div class="index-item">
                            <span class="index-name">{name}</span>
                            <span class="index-value {color_class(change)}">{format_percent(change)}</span>
                        </div>
                    </a>
"""
    url_index = url_index + 1

html_content += f"""
                </div>
                {'<div class="interpretation" style="margin-top: 16px;"><p>' + index_interpretation + '</p></div>' if index_interpretation else ''}
            </div>
"""

# Market Breadth Card
breadth_total = advances + declines + unchanged if (advances + declines) > 0 else 1
adv_percent = (advances / breadth_total) * 100
dec_percent = (declines / breadth_total) * 100
unc_percent = (unchanged / breadth_total) * 100

html_content += f"""
            <div class="card">
                <h2><span class="icon">📈</span> Market Breadth</h2>
                <div class="breadth-visual">
                    <div class="breadth-advances" style="width: {adv_percent}%; min-width: fit-content;"><span style="margin: 0 3px">{advances}</span></div>
                    <div class="breadth-unchanged" style="width: {unc_percent}%; min-width: fit-content;"><span style="margin: 0 3px">{unchanged}</span></div>
                    <div class="breadth-declines" style="width: {dec_percent}%; min-width: fit-content;"><span style="margin: 0 3px">{declines}</span></div>
                </div>
                <div style="display: flex; justify-content: space-between; color: var(--text-secondary); font-size: 0.85rem;">
                    <span>Advances: {advances}</span>
                    <span>Unchanged: {unchanged}</span>
                    <span>Declines: {declines}</span>
                </div>
                <div class="interpretation" style="margin-top: 16px;">
                    <p>{breadth_interpretation}</p>
                </div>
            </div>
        </div>
"""

# Sector Performance Card
max_sector_change = max(abs(s[1]) for s in sector_perf) if sector_perf else 1

html_content += """
        <div class="card" style="margin-top: 20px;">
            <h2><span class="icon">🏭</span> Sector Performance</h2>
"""

for name, change in sector_perf:
    bar_width = min(abs(change) / max_sector_change * 100, 100) if max_sector_change > 0 else 0
    html_content += f"""
            <div class="sector-bar">
                <span class="sector-name">{name}</span>
                <div class="sector-bar-container">
                    <div class="sector-bar-fill {color_class(change)}" style="width: {bar_width}%;"></div>
                </div>
                <span class="sector-value {color_class(change)}">{format_percent(change)}</span>
            </div>
"""

html_content += f"""
        </div>
        
        <footer>
            <p>Generated on {now.strftime('%d %B %Y at %I:%M %p IST')}</p>
            <p>Market Status: {market_status}</p>
        </footer>
    </div>
</body>
</html>
"""

# Write HTML reports
html_report_path = os.path.join(REPORT_DIR, HTML_REPORT_FILE)
daily_html_path = os.path.join(REPORT_DIR, DAILY_HTML_FILE)

with open(html_report_path, "w", encoding="utf-8") as f:
    f.write(html_content)

with open(daily_html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ HTML Report written")
print(f"📁 Reports saved to: {REPORT_DIR}/")
