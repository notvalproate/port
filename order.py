import pandas as pd
import os

PORTFOLIO_FILE = "portfolio.csv"

REQUIRED_COLUMNS = ["TICKER", "QUANTITY", "AVG_PRICE"]


# ======================================
# Load / Create Portfolio
# ======================================
def load_portfolio():

    if not os.path.exists(PORTFOLIO_FILE):
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        df.to_csv(PORTFOLIO_FILE, index=False)
        return df

    df = pd.read_csv(PORTFOLIO_FILE)

    # ensure columns exist
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = []

    return df


def save_portfolio(df):
    df.to_csv(PORTFOLIO_FILE, index=False)


# ======================================
# BUY ORDER
# ======================================
def buy_order(df):

    ticker = input("Ticker (ex: BEL): ").upper()
    price = float(input("Buy Price: "))
    qty = int(input("Quantity: "))

    if ticker in df["TICKER"].values:

        idx = df.index[df["TICKER"] == ticker][0]

        old_qty = df.at[idx, "QUANTITY"]
        old_avg = df.at[idx, "AVG_PRICE"]

        new_qty = old_qty + qty

        # weighted average
        new_avg = ((old_qty * old_avg) + (qty * price)) / new_qty

        df.at[idx, "QUANTITY"] = new_qty
        df.at[idx, "AVG_PRICE"] = round(new_avg, 2)

        print("✅ Position updated.")

    else:
        df.loc[len(df)] = {
            "TICKER": ticker,
            "QUANTITY": qty,
            "AVG_PRICE": price,
        }

        print("✅ New stock added.")

    return df


# ======================================
# SELL ORDER
# ======================================
def sell_order(df):

    ticker = input("Ticker to sell: ").upper()

    if ticker not in df["TICKER"].values:
        print("❌ Stock not found.")
        return df

    qty = int(input("Quantity to sell: "))
    price = float(input("Sell Price: "))

    idx = df.index[df["TICKER"] == ticker][0]
    current_qty = df.at[idx, "QUANTITY"]
    current_avg = df.at[idx, "AVG_PRICE"]

    if qty > current_qty:
        print("❌ Cannot sell more than owned.")
        return df

    remaining_qty = current_qty - qty

    if remaining_qty == 0:
        df = df[df["TICKER"] != ticker]
        print("✅ Position exited.")
    else:
        sold_amount = qty * price
        remaining_amount = (current_avg * current_qty) - sold_amount
        new_avg = remaining_amount / remaining_qty

        df.at[idx, "QUANTITY"] = remaining_qty
        df.at[idx, "AVG_PRICE"] = round(new_avg, 2)
        print("✅ Quantity reduced.")

    return df


# ======================================
# MENU
# ======================================
def menu():

    df = load_portfolio()

    while True:

        print("\n===== ORDER MENU =====")
        print("1. Buy Order")
        print("2. Sell Order")
        print("3. Exit")

        choice = input("Choose: ")

        if choice == "1":
            df = buy_order(df)
            save_portfolio(df)

        elif choice == "2":
            df = sell_order(df)
            save_portfolio(df)

        elif choice == "3":
            save_portfolio(df)
            print("Goodbye.")
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    menu()