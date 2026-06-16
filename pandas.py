"""
You have `sales` with columns: `product_id`, `region`, `month`, `revenue`.
Some `product_id` + `month` combinations have **duplicate rows** (data pipeline issue). 
Task:
1. Deduplicate by keeping the **highest revenue** row per `product_id` + `month` + `region` combination
2. Then for each `product_id`, calculate a **3-month rolling average** of revenue across months (in order)
3. Flag any product+month where rolling average **exceeds actual revenue by more than 20%** — label it `'Anomaly'`, else `'Normal'`
"""
df=sales.groupby(['product_id','month','region'],as_index=False).agg(revenue = ('revenue','max')) 
# df =df.drop_duplicates(subset=['product_id','month','region'])
df['month'] = pd.to_datetime(df['month']) 
df = df.set_index('month').sort_index() 
df['rolling'] = df.groupby(['product_id'])['revenue'].transform(lambda x: x.rolling("3M").mean())
#this 3M will force the rolling calculation based on 3 consecutive month and if there is a month skipped not showing it will still count it in like: (skipped+NonNANmonth+NoneNANmonth)/ 2 (since there are 2valid month)
df = df.reset_index() # brings 'month' back as a regular column
# or 
df = df.sort_values(['product_id', 'month'])
df['rolling'] = (
    df.groupby('product_id')['revenue']
    .transform(lambda x: x.rolling(3, min_periods=1).mean())
) # this will calculate as long as there is 1 month data not NAN and if there is a skipped month it will not detect and will just use next avaliable month

df['varian'] = (df['rolling'] - df['revenue'])/df['revenue'].replace(0,np.nan) 
df['flag'] = df['varian'].apply(lambda x: "Anomaly" if x > 0.2 else ("Normal" if x<=0.2 else "UNKNOWN"))
