LTCG_TAX_RATE = 12.5
LTCG_TAX_EXEMPTION = 125000.0

def tax_paid_by_not_reinvesting(capital, period, cagr):
    final_capital = capital * ((1 + (cagr / 100.0)) ** period)
    delta_capital = final_capital - capital

    if delta_capital <= LTCG_TAX_EXEMPTION:
        return 0
    
    taxable_amt = delta_capital - LTCG_TAX_EXEMPTION

    return (taxable_amt * LTCG_TAX_RATE) / 100.0

def tax_paid_by_reinvesting(capital, period, cagr):
    total_tax = 0
    capital_n = capital

    for i in range(1, period + 1):
        profit_n = (capital_n * cagr) / 100

        print(f"Profit after year {i}: ₹{profit_n:,.2f}")

        if profit_n <= LTCG_TAX_EXEMPTION:
            print(f"No tax for year {i}\n")
            capital_n = capital_n + profit_n
        else:
            taxable_amt = profit_n - LTCG_TAX_EXEMPTION
            tax_n = (taxable_amt * LTCG_TAX_RATE) / 100.0

            print(f"Tax paid after year {i}: ₹{tax_n:,.2f}\n")

            total_tax += tax_n
            capital_n = capital_n + profit_n - tax_n

    print(f">>> Total tax paid: ₹{total_tax:,.2f}")



capital = float(input("Enter starting capital: ₹"))
period = int(input("Enter horizon in years: "))
cagr = float(input("Enter the CAGR in %: "))

print(f"\n>>> Tax paid if redeemed once at end: ₹{tax_paid_by_not_reinvesting(capital, period, cagr):,.2f}\n")
tax_paid_by_reinvesting(capital, period, cagr)