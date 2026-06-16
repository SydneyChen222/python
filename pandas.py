"""
Mock Problem 3 — Apply/Custom Logic
You have shipments with columns: shipment_id, carrier, cost, weight_kg.
Task: Add a column cost_tier that labels each shipment as 'Low' if cost_per_kg < 5, 'Medium' if 5–15, 'High' if > 15. (cost_per_kg = cost / weight_kg)
Write it two ways: once using apply, once using np.select or pd.cut — and briefly say which you'd actually use in practice and why.
"""
shipments['cost_per_kg'] = shipments['cost']/shipments['weight_kg'].replace(0,np.nan) 
conditions=[(shipments['cost_per_kg'] <5 ), (shipments['cost_per_kg'] >=5) & (shipments['cost_per_kg'] <=15), (shipments['cost_per_kg'] >15) ]  
choice = ['Low','Medium','High'] 
shipments['cost_tier'] = np.select(conditions, choices, default='UNKNOWN')


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
#this 3M will force the rolling calculation based on 3 consecutive month and if there is a month skipped not showing it will still count it in like: (skipped+M1+M2)/ 2 (since there are 2valid month)
df = df.reset_index() # brings 'month' back as a regular column
# or 
df = df.sort_values(['product_id', 'month'])
df['rolling'] = (
    df.groupby('product_id')['revenue']
    .transform(lambda x: x.rolling(3, min_periods=1).mean())
) # this will calculate as long as there is 1 month data not NAN and if there is a skipped month it will not detect and will just use next avaliable month

df['varian'] = (df['rolling'] - df['revenue'])/df['revenue'].replace(0,np.nan) 
df['flag'] = df['varian'].apply(lambda x: "Anomaly" if x > 0.2 else ("Normal" if x<=0.2 else "UNKNOWN"))


"""
You have `parts_supply` with columns: `part_id`, `supplier_id`, `delivery_days`, `defect_rate`, `cost_per_unit`.
The data is messy:
- `delivery_days` has some negative values (data entry errors)
- `defect_rate` is between 0–1 but some rows have values > 1 (bad data)
- `cost_per_unit` has outliers — anything beyond 3 standard deviations from the mean is suspect

Task:
1. Clean all three columns — handle invalid values as `NaN`
2. For `cost_per_unit`, after cleaning, **normalize it** between 0 and 1 (min-max scaling)
3. Create a `risk_score` column = `0.5 * defect_rate + 0.3 * normalized_cost + 0.2 * (delivery_days / delivery_days.max())`
"""
parts_supply['delivery_days'] = parts_supply['delivery_days'].mask(parts_supply['delivery_days']<0, np.nan) 
parts_supply['defect_rate'] = parts_supply['defect_rate'].mask(parts_supply['defect_rate']>1,np.nan) 
std = parts_supply['cost_per_unit'].std() 
mean = parts_supply['cost_per_unit'].mean() 
parts_supply['cost_per_unit'] = parts_supply['cost_per_unit'].mask(parts_supply['cost_per_unit'].abs() - mean)>3*std, np.nan )
min_cost = df['cost_per_unit'].min() 
max_cost = df['cost_per_unit'].max() 
df['normal'] = (df['cost_per_unit'] - min_cost)/ ((max_cost - min_cost) if (max_cost - min_cost) != 0 else np.nan)
delivery_max = df['delivery_days'].max()
df['risk_score'] = 0.5 * df['defect_rate'] + 0.3 *df['normal'] + 0.2* (df['delivery_days']/(delivery_max if delievery_max !=0 else np.nan))
