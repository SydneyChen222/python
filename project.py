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
**Drill 5 — Pivot + rank within group**
New frame. Daily processing volume by merchant and payment method:
**Task — two parts:**

**(a)** Build a summary table: total amount per `merchant` × `method`, 
with methods as **columns** (one column `card`, one column `wallet`), merchants as rows. 
Missing combos should be `0`, not NaN. This is the `pivot_table` move.
**(b)** From the long (pre-pivot) per-merchant-per-method totals, add a column `rank_in_merchant`
that ranks each method **within its merchant** by total amount, highest = rank 1. This is `groupby().rank()`

Hints before you swing:
- **(a)** `pivot_table(index=..., columns=..., values=..., aggfunc='sum', fill_value=0)`. 
Think about which arg each of merchant/method/amount maps to.
- **(b)** First collapse to per-merchant-per-method totals (`groupby(['merchant','method'])['amount'].sum()`), *then* rank. 
For rank direction, `rank(ascending=False)` puts the largest at 1. `method='dense'` vs default matters if there are ties — mention which you'd pick and why.
"""
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'merchant':      ['Acme','Acme','Acme','Globex','Globex','Globex','Initech','Initech'],
    'method':        ['card','card','wallet','card','wallet','wallet','card','wallet'],
    'txn_date':      ['2024-04-01','2024-04-01','2024-04-02',
                      '2024-04-01','2024-04-01','2024-04-02',
                      '2024-04-01','2024-04-02'],
    'amount':        [200.0, 150.0, 300.0, 500.0, 100.0, 250.0, 80.0, 120.0],
})

summary = df.pivot_table(index = "merchant", columns = "method", values = "amount",
                        aggfunc = "sum",fill_value = 0).reset_index()
totals = df.groupby(['merchant', 'method'], as_index=False)['amount'].sum()
totals['rank'] = totals.groupby('merchant')['amount'].rank(method='dense', ascending=False)
result = totals[totals['rank'] == 1]


"""
Resample to daily, fill gaps, 3-day rolling average**
Transactions at irregular timestamps, with **missing days** 

Note: **May 3 and May 5 have no transactions at all**, and there's a declined txn on May 2. Both deliberate.

**Task:**
1. Keep only authorized transactions.
2. Produce a **daily** series of total authorized `amount`, covering **every day** from May 1 to May 6 — including May 3 and May 5, 
which must show `0` (this is where resample earns its keep: it fills the calendar automatically, unlike a plain groupby).
3. Add a **3-day rolling average** of daily amount (`roll_3d`), rounded to 2 decimals.

"""
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'txn_ts': ['2024-05-01 09:00', '2024-05-01 15:30', '2024-05-02 11:00',
               '2024-05-04 10:00', '2024-05-04 14:00', '2024-05-04 18:00',
               '2024-05-06 08:00'],
    'amount': [100.0, 200.0, 150.0, 300.0, 100.0, 50.0, 400.0],
    'status': ['authorized','authorized','declined',
               'authorized','authorized','authorized','authorized'],
})
df = df[df['status']=='authorized']
df['txn_ts'] = pd.to_datetime(df['txn_ts'])
df['txn_ts'] = df['txn_ts'].dt.date
df = df.groupby('txn_ts').agg(total_amount=('amount','sum')).reset_index()
daily = pd.date_range(start = '2024-05-01',end = '2024-05-06',freq = 'D',name = 'txn_ts')
daily = daily.to_frame(index=False)
final_df = pd.merge(daily, df, on=['txn_ts'], how='left').fillna(0)
final_df = final_df.sort_values(by='txn_ts')
final_df['roll_3d'] = final_df['total_amount'].rolling(3,min_periods = 1).mean()
final_df['roll_3d'] = final_df['roll_3d'].round(2)


auth = df[df['status'] == 'authorized'].copy()
auth['txn_ts'] = pd.to_datetime(auth['txn_ts'])
daily = (
    auth.set_index('txn_ts')
        .resample('D')['amount'].sum()      # auto-fills May 3 & 5 with 0
        .rename('total_amount')
        .reset_index()
)
daily['roll_3d'] = daily['total_amount'].rolling(3, min_periods=1).mean().round(2)


"""
 Monthly revenue + month-over-month growth**

Transactions spanning several months, irregular timestamps:
Note: **March has no transactions at all**, and there's a declined txn in February. 
Both deliberate — March is the resample test (it must appear as a month), the declined row is the filter test.
**Task:**
1. Authorized only.
2. **Monthly** total authorized revenue, every month from Jan to May — **March must appear as `0`** (this is `resample('ME')`).
3. Add `mom_growth` — month-over-month growth as a **percentage**: `(this month − last month) / last month × 100`, rounded to 2 decimals. 
First month is NaN (no prior month).

Hints before you swing:
- MoM growth needs the **previous month's value on the same row** — that's `.shift(1)` (pandas cousin of SQL `LAG`).
`prev = series.shift(1)`, then `(curr - prev) / prev × 100`.
- Watch the March trap: March = 0, so **April's growth divides by... wait, no** — April's *previous* month is March = 0. `(april - 0) / 0` → division by zero. 
How do you want to handle a MoM growth where the prior month was 0? Think about it — 
there's no single "right" answer, but you should *make a choice and name it*. This is exactly the kind of edge case the skills interview probes.
"""
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'txn_ts': ['2024-01-05', '2024-01-20', '2024-02-03', '2024-02-15',
               '2024-02-28', '2024-04-10', '2024-04-22', '2024-05-01'],
    'amount': [1000.0, 500.0, 800.0, 1200.0, 300.0, 2000.0, 600.0, 900.0],
    'status': ['authorized','authorized','authorized','declined',
               'authorized','authorized','authorized','authorized'],
})
df = df[df['status']=='authorized']
df['txn_ts'] = pd.to_datetime(df['txn_ts'])

mtm = df.set_index('txn_ts').resample('MS')['amount'].sum().rename('monthly_amount').reset_index() #sorted 
mtm['previous'] = mtm['monthly_amount'].shift(periods = 1) # since first month should be NaN
mtm['mom_growth'] = ((mtm['monthly_amount'] - mtm['previous']) / mtm['previous'].replace(0,np.nan) * 100).round(2) #for March edge case, we would like to show NaN


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

"""
### Task 1 — Clean the basic fields

Using the `payments` dataframe, create these four columns:

created_date
week_start
status_clean
is_authorized

Rules:

* Convert `created_at` to datetime.
* `created_date` should contain only the calendar date.
* `week_start` should be the Monday of that week.
* `status_clean` should be lowercase with extra spaces removed.
* `is_authorized` should be a boolean column.

Expected structure:

"""
import pandas as pd
import numpy as np

payments = pd.DataFrame({
    "transaction_id": [1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1012],
    "merchant_id": ["M1","M1","M1","M1","M2","M2","M2","M2","M1","M1","M2","M2"],
    "created_at": [
        "2026-02-01 10:01", "2026-02-01 10:05", "2026-02-02 09:30",
        "2026-02-03 12:20", "2026-02-03 15:00", "2026-02-04 16:10",
        "2026-02-05 11:40", "2026-02-05 11:45", "2026-02-08 13:00",
        "2026-02-08 13:05", "2026-02-09 14:30", "2026-02-10 17:20"
    ],
    "payment_reference": [
        "US-CARD-VISA-2026", "us_wallet_applepay_2026", "CA-WALLET-PAYPAL-2026",
        "UK-card-mastercard-2026", "DE_wallet_paypal_2026", "US-CARD-AMEX-2026",
        "FR-WALLET-APPLEPAY-2026", None, "US_wallet_applepay_2026",
        "US-WALLET-APPLEPAY-2026", "DE-card-visa-2026", "FR_wallet_paypal_2026"
    ],
    "status": [
        "AUTHORIZED", "failed", "Failed", "authorized", "FAILED", "authorized",
        "failed", "FAILED", "failed", "authorized", "failed", "FAILED"
    ],
    "amount": [100, 80, 120, 200, 150, 300, 90, 60, 110, 130, 70, 95],
    "currency": ["USD","USD","CAD","GBP","EUR","USD","EUR","EUR","USD","USD","EUR","EUR"],
    "error_message": [
        None,
        "CARD_DECLINED: insufficient_funds",
        "timeout_gateway_adyen_us",
        None,
        "Fraud Blocked - risk_score=92",
        None,
        "TIMEOUT: gateway did not respond",
        "issuer_unavailable",
        "card declined - INSUFFICIENT FUNDS",
        None,
        "risk_rule_blocked",
        "gateway timeout"
    ]
})
payments['created_at'] = pd.to_datetime(payments['created_at'])
payments['create_date'] = payments['created_at'].dt.date
payments['week_start'] = payments['created_at'].dt.to_period('W').dt.to_timestamp(how="start") # we have to use timestamp to get to_period and need to convert back to timestamp from period to get the week start date
payments['status_clean'] = payments['status'].str.strip().str.lower()
payments['is_authorized'] = payments['status_clean']=='authorized'
"""what if the status is not clean but shows as below:
AUTHORIZED
AUTHORIZED_SUCCESS
PARTIALLY_AUTHORIZED
then we need to align the business rules first

The business says:
"Different merchants send us payment references in different formats. We need to standardize them."
Create four columns
country
payment_type
provider
year
| payment_reference       | country | payment_type | provider | year |
| ----------------------- | ------- | ------------ | -------- | ---- |
| US-CARD-VISA-2026       | US      | card         | visa     | 2026 |
| uk_wallet_applepay_2026 | UK      | wallet       | applepay | 2026 |
| ...                     |         |              |          |      |
For NULL
country = unknown
payment_type = unknown
provider = unknown
year = NaN
Try without using .apply().
Use pandas string methods.
"""
payments = pd.DataFrame({
    "transaction_id":[
        1,2,3,4,5,6,7,8,9,10
    ],
    "payment_reference":[
        "US-CARD-VISA-2026",
        "uk_wallet_applepay_2026",
        "CA-CARD-MASTERCARD-2025",
        "DE_wallet_paypal_2026",
        "US-CARD-AMEX-2026",
        None,
        "  fr-wallet-paypal-2026 ",
        "UK_CARD_VISA_2026",
        "DE-card-mastercard-2026",
        "US__wallet__applepay__2026"
    ]
})
payments['payment_reference'] = payments['payment_reference'].str.strip()
payments['payment_reference'] = payments['payment_reference'].str.replace(r"[_-+]", "-", regex=True)
# we need to standardize the - and _ also there are multiple _ or - also need to standardized, so we need to use r"-+" for multiplt - and _
payments['country'] = payments['payment_reference'].str.upper().str.split("-").str[0].fillna("unknown")
payments['payment_type'] = payments['payment_reference'].str.lower().str.split("-").str[1].fillna("unknown")
payments['provider'] = payments['payment_reference'].str.lower().str.split("-").str[2].fillna("unknown")
payments['year'] = payments['payment_reference'].str.split("-").str[3].fillna(np.nan)
# Use .split() if your data is cleanly separated by a specific character (like a hyphen or comma). Use .extract() if your data is messy, lacks a uniform delimiter, or requires complex pattern matching

######better solution #############
#######because missing values are already null, and the year may otherwise remain a string. errors="coerce" also safely converts invalid years to NaN.
payments["component_count"] = (
    payments["payment_reference_clean"]
    .str.split("-")
    .str.len()
)
payments["is_valid_reference"] = payments["component_count"] == 4
### we need to check the data structure and see to validate the number of components
parts = payments["payment_reference_clean"].str.split("-", expand=True)
payments["country"] = parts[0].str.upper().fillna("unknown")
payments["payment_type"] = parts[1].str.lower().fillna("unknown")
payments["provider"] = parts[2].str.lower().fillna("unknown")
payments["year"] = pd.to_numeric(parts[3], errors="coerce")


"""
## Task 3 — Failure classification
Using the same `payments` dataframe, create a new column:
failure_category
Rules:

if is_authorized is True
→ "authorized"
else if error_message is null
→ "unknown"
else if error_message contains "insufficient" or "declined"
→ "insufficient_funds"
else if error_message contains "fraud" or "risk"
→ "fraud_risk"
else if error_message contains "timeout" or "gateway"
→ "technical"

else if error_message contains "issuer"
→ "issuer"
else
→ "other"
Important:

* Use vectorized logic.
* Condition order matters.
* Keep authorized transactions as `"authorized"` even if `error_message` contains text.
"""
condtions = [payments['is_authorized']==True,
             payments['error_message'].isna(),
             ((payments['error_message'].str.contains('insufficient',  case=False,
    na=False)) | (payments['error_message'].str.contains('declined',  case=False,
    na=False))),
             ((payments['error_message'].str.contains('fraud',  case=False,
    na=False)) | (payments['error_message'].str.contains('risk',  case=False,
    na=False))),
             ((payments['error_message'].str.contains('timeout',  case=False,
    na=False)) | (payments['error_message'].str.contains('gateway',  case=False,
    na=False))),
             (payments['error_message'].str.contains('issuer',  case=False,
    na=False))
]
choices = ['authorized','unknown','insufficient_funds','fraud_risk','technical','issuer']
payments['failure_category'] = np.select(conditions,choices,default = 'other')


"""
we don't care about keywords anymore."
Instead, they send you this lookup table
Marketing changes these mappings every week
would you redesign your solution?
If the mapping changes frequently, I would avoid hardcoding it in Python because every business change would require a code deployment and additional testing.

Instead, I would ask the business to maintain the mapping in a reference table or configuration file. 
My pipeline would load the mapping dynamically so that future updates only require changing the reference table rather than modifying application code.
Because the relationship is based on substring matching rather than an equality key, I wouldn't use a simple merge. 
Instead, I'd drive the matching logic from the reference table so that business users can update mappings without requiring code changes
"""
failure_mapping = pd.DataFrame({

"pattern":[
"insufficient",
"declined",
"fraud",
"risk",
"timeout",
"gateway",
"issuer"
],

"failure_category":[
"insufficient_funds",
"insufficient_funds",
"fraud_risk",
"fraud_risk",
"technical",
"technical",
"issuer"
]
})
mapping = {
    "insufficient": "insufficient_funds",
    "declined": "insufficient_funds",
    "fraud": "fraud_risk",
    "risk": "fraud_risk",
    ...
}
conditions = []
choices = []

for pattern, category in mapping.items():
    conditions.append(
        payments["error_message"].str.contains(
            pattern,
            case=False,
            na=False
        )
    )
    choices.append(category)



"""
# Task 4 — Weekly Merchant KPI
> "Build a weekly KPI table that will feed our dashboard."
You already have these columns:
week_start
merchant_id
payment_type
is_authorized
amount

Build the following output:
| week_start | merchant_id | payment_type | attempted_transactions | authorized_transactions | authorization_rate | attempted_amount | authorized_amount |
| ---------- | ----------- | ------------ | ---------------------- | ----------------------- | ------------------ | ---------------- | ----------------- |

Rules:
* attempted_transactions = number of transactions
* authorized_transactions = number of authorized transactions
* authorization_rate = authorized_transactions / attempted_transactions
* attempted_amount = total amount
* authorized_amount = sum(amount) where authorized

### Interview twist
You **cannot** use `.apply()`.
Try to solve it using one `groupby().agg()`.
"""
attempted = df.groupby(['week_start','merchant_id','payment_type']).agg(attempted_transaction = ('amount','size'),attempted_amount = ('amount','sum')).reset_index()
authorized = df[df['is_authorized'] == True]
authorized = authorized.groupby(['week_start','merchant_id','payment_type']).agg(authorized_transactions = ('amount','size'), authorized_amount = ('amount','sum')).reset_index()
result = attempted.merge(authorized, on = ['week_start','merchant_id','payment_type'],how = 'left')
result[["authorized_transactions", "authorized_amount"]] = (
    result[["authorized_transactions", "authorized_amount"]]
    .fillna(0)
)
result['authorization_rate'] = result['authorized_transactions'].replace(0,np.nan) / result['attempted_transactions'].replace(0,np.nan)
###########
df['authorized_amount'] = df['amount'].where(df['is_authorized'],0)
result = df.groupby(['week_start','merchant_id','payment_type']).agg(
    attempted_transaction = ('amount','size'),
    attempted_amount = ('amount','sum'),
    authorized_transactions = ('is_authorized','sum'),
    authorized_amount = ('authorized_amount','sum')
).reset_index()
result['authorization_rate'] = result['authorized_transactions'] / result['attempted_transactions'].replace(0,np.nan)
"""
## Task 5 — Top failure category by week and payment type
Using the same `payments` dataframe, keep only failed transactions and return the top failure category for each:

week_start
payment_type

Output:
week_start
payment_type
failure_category
transaction_count
rank

Rules:
* Exclude authorized transactions.
* Count transactions by `week_start`, `payment_type`, and `failure_category`.
* Rank categories within each `week_start + payment_type`.
* Keep all tied categories at rank 1.
* Use pandas only.
"""
failure = payments[payments['status_clean']!='authorized']
failure = failure.groupby(['week_start','payment_type','failure_category']).agg(transaction_count=('transaction_id','size')).reset_index()
failure['rank'] = failure.groupby(['week_start','payment_type'])['transaction_count'].rank(method='dense',ascending = False)
result = failure[failure['rank']==1]

"""
Rolling Authorization Rate
"Our dashboard currently shows daily authorization rate.
We think it is too noisy.
Please calculate a rolling 3-day authorization rate.
| created_date | payment_type | attempted_transactions | authorized_transactions |
| ------------ | ------------ | ---------------------- | ----------------------- |

For each payment_type calculate

rolling_attempted_transactions
rolling_authorized_transactions
rolling_authorization_rate

where
rolling_authorization_rate
=
rolling_authorized_transactions
/
rolling_attempted_transactions

expected output:
| created_date | payment_type | attempted_transactions | authorized_transactions | rolling_attempted_transactions | rolling_authorized_transactions | rolling_authorization_rate |
| ------------ | ------------ | ---------------------: | ----------------------: | -----------------------------: | ------------------------------: | -------------------------: |

"""
df = payments.groupby(['created_date','payment_type']).agg(
    attempted_transactions=('transaction_id','size'),
    authorized_transactions=('is_authorized','sum')
).reset_index()
df = df.sort_values(by=['payment_type','created_date'])
df['rolling_attempted_transactions'] = df.groupby('payment_type')['attempted_transactions'].transform(lambda x: x.rolling(3,min_periods = 1).sum())
df['rolling_authorized_transactions'] = df.groupby('payment_type')['authorized_transactions'].transform(lambda x: x.rolling(3,min_periods = 1).sum())
df['rolling_authorization_rate'] = df['rolling_authorized_transactions'] / df['rolling_attempted_transactions'].replace(0,np.nan)

"""
A merchant says:

"Our wallet authorization rate suddenly dropped this week."
You receive two dataframes.
transactions
"""
transactions = pd.DataFrame({
    "transaction_id":[1,2,3,4,5,6,7,8],
    "merchant_id":["M1","M1","M1","M1","M1","M2","M2","M2"],
    "payment_method":[
        "Wallet",
        "wallet",
        "WALLET",
        "Card",
        "card",
        "wallet",
        "Wallet",
        "Card"
    ],
    "country":[
        "US ",
        "us",
        "US",
        "CA",
        "CA ",
        "DE",
        " DE",
        "DE"
    ],
    "created_at":[
        "2026-02-01",
        "2026-02-01",
        "2026-02-02",
        "2026-02-02",
        "2026-02-03",
        "2026-02-03",
        "2026-02-04",
        "2026-02-04"
    ],
    "amount":[100,80,120,150,180,130,140,200]
})
payment_events = pd.DataFrame({
    "transaction_id":[
        1,2,2,3,4,5,6,7,7,8
    ],
    "event_time":[
        "2026-02-01 10:00",
        "2026-02-01 11:00",
        "2026-02-01 11:05",
        "2026-02-02 09:00",
        "2026-02-02 13:00",
        "2026-02-03 09:00",
        "2026-02-03 11:00",
        "2026-02-04 10:00",
        "2026-02-04 10:05",
        "2026-02-04 12:00"
    ],
    "status":[
        "authorized",
        "failed",
        "authorized",
        "failed",
        "authorized",
        "authorized",
        "failed",
        "failed",
        "failed",
        "authorized"
    ]
})
###Part A clean
transactions['payment_method'] = transactions['payment_method'].str.lower(),str.strip()
transactions['country'] = transactions['country'].str.upper().str.strip()
###Part B -- Find the latest status of every transaction.
payment_events["event_time"] = pd.to_datetime(
    payment_events["event_time"]
)
payment_events = payments_events.sort_values(by=['transaction_id','event_time'])
latest = payment_events.drop_duplicates(subset=['transaction_id'], keep="last")
###Part C  Merge into transactions.
df = pd.merge(transactions,latest,on='transaction_id',how ='left',validate="one_to_one")  #Before merging, verify that the relationship between these two tables matches my expectation. If not, raise an error instead of silently producing bad data.
###Part D   Build
#|country|payment_method|attempted|authorized|authorization_rate|
df['is_authorized'] = df['status'] == 'authorized'
df = df.groupby(['country','payment_method'],as_index = False).agg(
    attempted = ('transaction_id','size'),
    authorized = ('is_authorized','sum')
)
df['authorization_rate'] = df['authorized'] / df['attempted'].replace(0,np.nan)

"""Part E
Business asks:
"Which segment should we investigate first?"
Return
|country|payment_method|authorization_rate|
"""
result = df.sort_values(['authorization_rate']).head(1)


"""
Clean payment_info.
Requirements:
mixed case
"Apple Pay" / "ApplePay" / "APPLE PAY" should become
apple_pay
"Master Card" and "MasterCard" should become
mastercard
None>>unknown

Create:
country
payment_method
device
"""
import pandas as pd
payments = pd.DataFrame({
"transaction_id":[
1001,1002,1003,1004,1005,
1006,1007,1008,1009,1010,
1011,1012
],
"merchant":[
"M1","M1","M1","M1","M1","M2","M2","M2","M2","M2","M2","M1"
],
"created_at":[
"2026-02-01","2026-02-01",
"2026-02-02","2026-02-03","2026-02-03","2026-02-04","2026-02-05",
"2026-02-05","2026-02-06","2026-02-07","2026-02-07","2026-02-08"
],

"payment_info":[
"US|Apple Pay|iOS",
"US|apple pay|IOS",
"US|Visa|Card",
"CA|ApplePay|IOS",
"CA|MasterCard|Card",
"DE|APPLE PAY|Android",
"DE|Visa|Card",
"DE|Master Card|Card",
"US|ApplePay|Android",
"US|Visa|Card",
None,"US|Apple Pay|IOS"
],
"status":[
"AUTHORIZED","FAILED","AUTHORIZED","FAILED","AUTHORIZED","FAILED","AUTHORIZED",
"AUTHORIZED","FAILED","AUTHORIZED","FAILED","AUTHORIZED"
],
"amount":[
100,80,120,90,200,130,180,140,60,210,75,160]})
#"I used regex because the input has inconsistent formatting. The same logical value appears with different capitalization and spacing, such as Apple Pay, ApplePay, and APPLE PAY. A regex with an optional whitespace pattern allows me to normalize all variants using one rule instead of maintaining multiple replacement statements. That makes the solution easier to extend if more formatting variations appear
payments[[ 'country', 'payment_method', 'device']] = payments["payment_info"].str.split("|", expand=True)
payments['payment_method'] = payments['payment_method'].str.strip().str.lower()
payments['payment_method'] = payments['payment_method'].str.replace(r"(?i)apple\s*pay", "apple_pay", regex=True)
payments['payment_method'] = payments['payment_method'].str.replace(r"(?i)master\s*card", "mastercard", regex=True)
payments['payment_method'] = payments['payment_method'].fillna('unknown')
payments['device'] = payments['device'].str.strip().str.replace(r"(?i)ios", "iOS", regex=True)
payments['device'] = payments['device'].str.strip().str.replace(r"(?i)android", "Android", regex=True)
payments['device'] = payments['device'].str.strip().str.replace(r"(?i)card", "Card", regex=True)
payments['device'] = payments['device'].fillna('unknown')
payments['country'] = payments['country'].str.strip().str.upper()

"""calculate the Apple Pay authorization rate by country."
Requirements:
Output:

country	attempted_transactions	authorized_transactions	authorization_rate

Rules:
Use only payment_method == "apple_pay".
Use the cleaned columns from Question 1.
Return the countries sorted by lowest authorization rate first.
payments['country'] = payments['country'].fillna('unknown')"""

