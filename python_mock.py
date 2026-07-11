"""
 Python/pandas: Raw Transaction Feed (~90 min)
Questions — answer in order:
Q1 (parse + clean). Explode record into columns: txn_id, country, merchant, currency, amount, status, method, txn_ts. Extract country from the txn id. 
Normalize: strip whitespace everywhere, amount → float (handle the comma and the empty one), status → lower, currency → upper, merchant → cleaned of the MERCH: prefix and title-cased, txn_ts → datetime. 
State how you handle the missing amount.
Q2 (dedupe + validate). There's a duplicate. Remove it, keeping one. How many rows remain? 
Then report how many transactions have a missing/null amount after cleaning.
Q3 (groupby + pivot). Total authorized amount per merchant × method, methods as columns, missing combos = 0.
Q4 (merge). Join the cleaned transactions to merchant_meta to attach country and tier. There's a join subtlety hiding in the merchant names — 
find it and say how you'd handle it. Which transactions, if any, fail to match?
Q5 (time-series). Daily total authorized amount across all merchants, every day 2024-03-01 → 2024-03-06 (missing days = 0), plus a 3-day rolling average (2 dp).
Q6 (insight). Compute each merchant's refund + chargeback rate (by count: (refunded + chargeback) ÷ total, %). Flag any merchant above 25% as "high risk." 
Who's flagged, and what would you tell the risk team?
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

#Q3
df = df[df['status']=='authorized'].pivot_table(index = 'merchant', columns = 'method',values = 'authorized_amount',aggfunc = 'sum', fill_value = 0).reset_index()

raw['authorized_amount'] = 0
raw.loc[raw['status']=='authorized','authorized_amount'] = raw['amount']
df = merchant_meta.merge(raw,on = ['merchant','country'], how = 'left')
df['method'] = df['method'].fillna('unknown')
df = df.pivot_table(index = 'merchant', columns = 'method',values = 'authorized_amount',aggfunc = 'sum', fill_value = 0).reset_index()

###
raw['auth_amt'] = raw['amount'].where(raw['status'] == 'authorized', 0)
q3 = (raw.pivot_table(index='merchant', columns='method',
                      values='auth_amt', aggfunc='sum', fill_value=0)
         .reindex(merchant_meta['merchant'].unique(), fill_value=0)   # forces all merchants
         .reset_index())

#Q4
result = pd.merge(raw,merchant_meta,on = ['merchant','country'],how = 'left') # there will be no issues since the merchant has already been cleaned in previous Q1 by str.title()
#Q5
daily = pd.DataFrame({'date':pd.date_range(start = '2024-03-01',end = '2024-03-06',freq = 'D')})
daily['date'] = daily['date'].dt.date
raw['date'] = raw['txn_ts'].dt.date
df2 =pd.merge(daily,raw, on='date',how= 'left')
df2['auth_amt'] = df2['amount'].where(df2['status'] == 'authorized', 0)
df2 = df2.groupby(['date']).agg(authorized_amount = ('auth_amt','sum')).reset_index() # Daily total authorized amount across all merchants,this I believe is ask for the total authorized amount for all merchants not total for each merchants, because if it is ask each merchant then i need to group by merchant too
df2['rolling3d'] = df2['authorized_amount'].rolling(window = 3, min_periods = 1).mean().round(2)


#Q6
raw['is_chargeback'] = raw['status'] == 'chargeback'
raw['is_refund'] = raw['status'] == 'refunded'
df3 = raw.groupby('merchant').agg(total_transaction = ('txn_id','size'), chargeback = ('is_chargeback','sum'), refunded = ('is_refund','sum')).reset_index()
df3['rate'] = (df3['chargeback'] + df3['refunded']) * 100 / df3['total_transaction'].replace(0,np.nan) 
df3['flag'] =  np.where(df3["rate"] > 25, "high risk", "low risk")
"""
: both flags are one event on a tiny denominator (Hooli = 1 chargeback of 2 txns, Globex = 1 refund of 3), so don't action on that little data — set a minimum-volume floor before flagging. And separate chargebacks from refunds: chargebacks carry card-network compliance risk (monitoring programs, fines above ~1%), refunds are usually benign merchant-initiated returns. Summing them into one "risk" number blurs a real distinction.
That reasoning — small-sample caution plus knowing why chargebacks ≠ refunds"""
