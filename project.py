"""
Two frames. Transactions, and merchant metadata:
Note: `merchant_id = 40` (Umbrella) has **no transactions**, and merchant 20 has one **declined** txn. Both are deliberate.
**Task — produce one enriched row per authorized transaction, with these added columns:**

1. `merchant_name` and `country` joined in from the metadata.
2. `merchant_total` — each merchant's total authorized amount, **repeated on every one of that merchant's rows** (this is the `groupby().transform()` move — same value broadcast back to each row, like a SQL window `SUM() OVER (PARTITION BY merchant)`).
3. `pct_of_merchant` — this transaction's amount as a % of that merchant's authorized total, 2 decimals.
4. `is_first_txn` — boolean, `True` if this is the merchant's **earliest** authorized transaction by `txn_ts`.

- `txn_ts` is a string — you'll need `pd.to_datetime` for the "earliest" logic to sort correctly (string sort *happens* to work here, but don't rely on it — convert).
- Should the join be inner or left, given you only want rows for *authorized* transactions that have a merchant? Think about what happens to Umbrella (no txns) and the declined row.
- `is_first_txn`: the clean pandas idiom is `groupby(...)['txn_ts'].transform('min')` then compare — mirrors a window function. Or `rank`. Your call.
"""
import pandas as pd

txns = pd.DataFrame({
    'txn_id':      [1, 2, 3, 4, 5, 6, 7, 8],
    'merchant_id': [10, 10, 20, 20, 20, 30, 10, 30],
    'txn_ts':      ['2024-03-01 09:15', '2024-03-03 14:00', '2024-03-01 10:00',
                    '2024-03-02 11:30', '2024-03-05 16:45', '2024-03-02 08:00',
                    '2024-03-04 12:00', '2024-03-06 19:20'],
    'amount':      [100.0, 250.0, 80.0, 400.0, 120.0, 300.0, 175.0, 90.0],
    'status':      ['authorized', 'authorized', 'authorized', 'declined',
                    'authorized', 'authorized', 'authorized', 'authorized'],
})

merchants = pd.DataFrame({
    'merchant_id': [10, 20, 30, 40],
    'merchant_name': ['Acme', 'Globex', 'Initech', 'Umbrella'],
    'country':       ['US', 'GB', 'DE', 'US'],
})





"""
Task:
Create a new column called `failure_category` using this logic:

if error_message is null → "unknown"
if it contains "insufficient" → "insufficient_funds"
if it contains "fraud" or "risk" → "fraud"
if it contains "timeout" or "gateway" → "technical"
if it contains "issuer" → "issuer"
else → "other"

Then return a summary table by:

country
payment_method
failure_category
transaction_count
"""
import pandas as pd
df = pd.DataFrame({
    "transaction_id": [1, 2, 3, 4, 5, 6, 7],
    "country": ["US", "US", "US", "CA", "CA", "UK", "UK"],
    "payment_method": ["card", "wallet", "wallet", "card", "wallet", "card", "wallet"],
    "error_message": [
        None,
        "CARD_DECLINED: insufficient_funds",
        "timeout_gateway_adyen_us",
        "Fraud Blocked - risk_score=92",
        "card declined - INSUFFICIENT FUNDS",
        "issuer_unavailable",
        "TIMEOUT: gateway did not respond"
    ]
})
condition = [df['error_message'].isna(),
    df['error_message'].str.contains('insufficient',case = False, na = False),
             df['error_message'].str.contains('fraud|risk',case = False, na=False),
             df['error_message'].str.contains('timeout|gateway', case =False,na=False)
    df['error_message'].str.contains('issuer',case=False,na=False)]
             
choices = ['unknown', 'insufficient_funds', 'fraud','technical','issuer']
df['failure_category'] = np.select(condition,choices,default = 'other')

df = df.groupby(['country','payment_method','failure_category']).agg(
        transaction_count=("transaction_id", "count")
    ).reset_index()
"""
top failure reason by segment.**
Using the same dataframe after you created `failure_category`, return the **top failure category** for each:
country
payment_method

Output columns:
country
payment_method
failure_category
transaction_count
rank

Rules:
* Count transactions by `country`, `payment_method`, `failure_category`
* Rank failure categories within each `country + payment_method`
* Keep only rank = 1
* If there is a tie, keep all tied categories
"""
df = df.groupby(['country','payment_method','failure_category']).agg(
        transaction_count=("transaction_id", "count")).reset_index()

df['rank'] = df.groupby(['country','payment_method'])['trasaction_count'].rank(method = 'dense',ascending = False)
result = df[df['rank']==1]
