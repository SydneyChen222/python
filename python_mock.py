"""
 Python/pandas: Raw Transaction Feed (~90 min)
Questions — answer in order:
Q1 (parse + clean). Explode record into columns: txn_id, country, merchant, currency, amount, status, method, txn_ts. Extract country from the txn id. 
Normalize: strip whitespace everywhere, amount → float (handle the comma and the empty one), status → lower, currency → upper, merchant → cleaned of the MERCH: prefix and title-cased, txn_ts → datetime. 
State how you handle the missing amount.
Q2 (dedupe + validate). There's a duplicate. Remove it, keeping one. How many rows remain? 
Then report how many transactions have a missing/null amount after cleaning.
Q3 (groupby + pivot). Total authorized amount per merchant × method, methods as columns, missing combos = 0.
Q4 (merge). Join the cleaned transactions to merchant_meta to attach country and tier. There's a join subtlety hiding in the merchant names — find it and say how you'd handle it. Which transactions, if any, fail to match?
Q5 (time-series). Daily total authorized amount across all merchants, every day 2024-03-01 → 2024-03-06 (missing days = 0), plus a 3-day rolling average (2 dp).
"""
import pandas as pd
import numpy as np

raw = pd.DataFrame({
    'record': [
        'TXN-2024-US-1001|MERCH:Acme Corp|USD|1,200.00|authorized|card|2024-03-01 09:15',
        'txn-2024-gb-1002 | MERCH:Globex Ltd | GBP | 2,000.00 | AUTHORIZED | card | 2024-03-01 14:00',
        'TXN-2024-US-1003|MERCH:acme corp|USD|500.00|DECLINED|card|2024-03-03 11:00',
        'TXN-2024-DE-1004|MERCH:Initech GmbH|EUR|  400.00 |authorized|wallet|2024-03-01 07:00',
        'TXN-2024-GB-1005|MERCH:Globex Ltd|GBP|900.00|refunded|wallet|2024-03-02 16:45',
        'TXN-2024-US-1001|MERCH:Acme Corp|USD|1,200.00|authorized|card|2024-03-01 09:15',  # dup
        'TXN-2024-GB-1006|MERCH:Hooli Inc|GBP|3,000.00|authorized|card|2024-03-01 20:00',
        'TXN-2024-DE-1007|MERCH:Initech GmbH|EUR|650.00|authorized|wallet|2024-03-02 09:30',
        'TXN-2024-GB-1008|MERCH:Hooli Inc|GBP|1,800.00|chargeback|wallet|2024-03-03 09:00',
        'TXN-2024-US-1009|MERCH:Acme Corp|USD||authorized|card|2024-03-04 08:30',  # missing amount
        'TXN-2024-GB-1010|MERCH:Globex Ltd|GBP|1,100.00|authorized|card|2024-03-05 12:00',
        'TXN-2024-DE-1011|MERCH:Initech GmbH|EUR|380.00|authorized|card|2024-03-06 18:00',
    ]
})

merchant_meta = pd.DataFrame({
    'merchant': ['Acme Corp', 'Globex Ltd', 'Initech Gmbh', 'Hooli Inc', 'Umbrella Llc'],
    'country':  ['US', 'GB', 'DE', 'GB', 'US'],
    'tier':     ['gold', 'silver', 'gold', 'silver', 'bronze'],
})
#Q1
raw[['txn_id', 'merchant', 'currency', 'amount', 'status', 'method', 'txn_ts']] = raw["record"].str.split("|", expand=True)
raw['txn_id'] = raw['txn_id'].str.strip()
raw['country'] = raw['txn_id'].str.split("-").str[2].str.upper()
raw['txn_id'] = raw['txn_id'].str.upper()
raw['merchant'] = raw['merchant'].str.strip()
raw['merchant'] = raw['merchant'].str.replace('MERCH:', '', regex=False).str.title()
raw['currency'] = raw['currency'].str.strip()
raw['amount'] = raw['amount'].str.strip().str.replace(",","",regex=False)
raw['amount'] = pd.to_numeric(raw['amount'], errors='coerce')
raw['status'] = raw['status'].str.lower().str.strip()
raw['method'] = raw['method'].str.lower().str.strip()
raw['txn_ts'] = raw['txn_ts'].str.strip()
raw['txn_ts'] = pd.to_datetime(raw['txn_ts'])
#Q2
raw = raw.drop_duplicates(subset=['txn_id'], keep='first')
len(raw)
nan_count = raw['amount'].isna().sum()



