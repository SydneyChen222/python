"""
Two frames. Transactions, and merchant metadata:
Note: `merchant_id = 40` (Umbrella) has **no transactions**, and merchant 20 has one **declined** txn. Both are deliberate.

**Task — produce one enriched row per authorized transaction, with these added columns:**
1. `merchant_name` and `country` joined in from the metadata.
2. `merchant_total` — each merchant's total authorized amount, **repeated on every one of that merchant's rows** 
(this is the `groupby().transform()` move — same value broadcast back to each row, like a SQL window `SUM() OVER (PARTITION BY merchant)`).
3. `pct_of_merchant` — this transaction's amount as a % of that merchant's authorized total, 2 decimals.
4. `is_first_txn` — boolean, `True` if this is the merchant's **earliest** authorized transaction by `txn_ts`.

- `txn_ts` is a string — you'll need `pd.to_datetime` for the "earliest" logic to sort correctly 
(string sort *happens* to work here, but don't rely on it — convert).
- Should the join be inner or left, given you only want rows for *authorized* transactions that have a merchant? 
Think about what happens to Umbrella (no txns) and the declined row.
- `is_first_txn`: the clean pandas idiom is `groupby(...)['txn_ts'].transform('min')` then compare — 
mirrors a window function. Or `rank`.
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

txns['txn_ts'] = pd.to_datetime(txns['txn_ts'])
txns = txns[txns['status'] == 'authorized']
txns['is_first_txn'] = txns['txn_ts'] == txns.groupby('merchant_id')['txn_ts'].transform('min')
txns['merchant_total'] = txns.groupby(['merchant_id'])['amount'].transform('sum')
txns['pct_of_merchant'] = (txns['amount']/txns['merchant_total'].replace(0,np.nan)).round(2)
df = pd.merge(merchants,txns,on = 'merchant_id', how ='right')


#authorized amount percentage 
txns['txn_ts'] = pd.to_datetime(txns['txn_ts'])
txns['merchant_total'] = txns.groupby(['merchant_id'])['amount'].transform('sum')
authorized = txns["amount"].where(txns["status"] == "authorized", 0)
txns['authorized_amount'] = authorized.groupby(txns['merchant_id']).sum()
txns['is_first_txn'] = txns['txn_ts'] == txns.groupby('merchant_id')['txn_ts'].transform('min')
df = pd.merge(merchants,txns,on = 'merchant_id', how ='left')
df = df.fillna(0)
df['pct_of_merchant'] = (df['authorized_amount']/df['merchant_total'].replace(0,np.nan)).round(2)








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
"""
Exactly. That is the correct answer.

> “I used `dense` ranking because the requirement says to keep all tied categories. If two failure categories have the same highest transaction count within a country and payment method, both receive rank 1 and are retained.”

One nuance: for **only keeping rank 1**, `rank(method="min")` would also keep all top ties. `dense` becomes especially useful if we later keep multiple ranks, because it produces consecutive ranks after ties.

For example, counts `10, 10, 5`:

```text
dense → 1, 1, 2
min   → 1, 1, 3
first → 1, 2, 3
```

## messy join and duplicate detection
You now receive two dataframes:
Business asks:
> Add the **latest risk score** to every transaction. 
Keep **all transactions**, including transactions with no risk score.

Return:
transaction_id
merchant_id
amount
latest_risk_score
"""

transactions = pd.DataFrame({
    "transaction_id": [101, 102, 103, 104, 105],
    "merchant_id": ["M1", "M1", "M1", "M2", "M2"],
    "amount": [100, 200, 150, 300, 250]
})

risk_scores = pd.DataFrame({
    "transaction_id": [101, 102, 102, 103, 105, 105],
    "model_version": ["v1", "v1", "v2", "v1", "v1", "v2"],
    "score_time": [
        "2026-01-01 10:00",
        "2026-01-01 11:00",
        "2026-01-01 11:05",
        "2026-01-01 12:00",
        "2026-01-01 13:00",
        "2026-01-01 13:10"
    ],
    "risk_score": [20, 85, 40, 60, 90, 95]
})
risk_scores["score_time"] = pd.to_datetime(risk_scores["score_time"])

risk_scores['latest'] = risk_scores.groupby(['transaction_id'],as_index=False)['score_time'].transform('max')

risk["model_num"] = risk["model_version"].str.extract(r"(\d+)").astype(int)

risk = risk_scores[risk_scores['latest'] == risk_scores['score_time']]
#At this point, if multiple rows share the same latest timestamp for one transaction, I would not randomly drop one. I’d ask for a tie-breaker rule
risk = (
    risk.sort_values(
        ["transaction_id", "model_num"],
        ascending=[True, False]
    ).drop_duplicates("transaction_id", keep="first")
)
result = pd.merge(transactions,risk[['transaction_id','risk_score']],on = 'transaction_id',how = "left")

result = result[['transaction_id','merchant_id','amount','risk_score']]
result = result.rename(columns = {'risk_score':'latest_risk_score'})

#If multiple records share the same latest timestamp but have different risk scores, I would not arbitrarily drop one. 
#I’d flag those transactions as ambiguous and either ask for a deterministic tie-breaker, such as model priority or event ID,
#or return them separately for data quality review.
duplicate_latest = (
    risk.groupby("transaction_id")["risk_score"]
    .nunique()
    .reset_index(name="latest_score_count")
)

problem_ids = duplicate_latest[
    duplicate_latest["latest_score_count"] > 1
]["transaction_id"]

ambiguous_latest = latest_risk[
    latest_risk["transaction_id"].isin(problem_ids)
]

