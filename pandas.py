"""
You have shipments with columns: shipment_id, carrier, cost, weight_kg.
Task: Add a column cost_tier that labels each shipment as 'Low' if cost_per_kg < 5, 'Medium' if 5–15, 'High' if > 15. (cost_per_kg = cost / weight_kg)
Write it two ways: once using apply, once using np.select or pd.cut — and briefly say which you'd actually use in practice and why.
"""
shipments['cost_per_kg'] = shipments['cost']/shipments['weight_kg'].replace(0,np.nan) 
conditions=[(shipments['cost_per_kg'] <5 ), (shipments['cost_per_kg'] >=5) & (shipments['cost_per_kg'] <=15), (shipments['cost_per_kg'] >15) ]  
choice = ['Low','Medium','High'] 
shipments['cost_tier'] = np.select(conditions, choices, default='UNKNOWN')
#or
shipments['cost_tier'] = shipments['cost_per_kg'].apply(lambda x: 'Low' if x<5, else ('Medium' if x<=15 and x>=5 else( 'High' if x>15 else 'unknown')))

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

"""
You have orders with columns: customer_id, region, order_date, order_amount.
Each customer has many orders (multiple rows). Task:

Compute total order amount per customer (customers belong to multiple region)
Also compute their order count (number of orders)
Filter out customers with fewer than 3 orders (low-activity, exclude them)
Rank the remaining customers by total amount within each region, ties share the same rank
Keep only the top 3 per region
Sort by region (A→Z), then rank ascending
"""


df = df.groupby(['customer_id','region']).agg(total_order_per_region = ("order_amount","sum"),
                                              total_count_per_region = ("order_amount","size")).reset_index() # not sure how do we want to deal with NaN in order amount, based on my understanding, this could be size or count if we just ignore those NaN then use count but I think we want all order number so I use size
df['total_order'] = df.groupby('customer_id')['total_count_per_region'].transform('sum') #getting the total order number per customer
df = df.loc[df['total_order']>=3] #exclude customers with fewer than 3 orders company-wide

df['rank'] = df.groupby('region')['total_order_per_region'].rank(method = 'min',ascending=False)
df = df.loc[df['rank']<=3]
df = df.sort_values(['region','rank'],ascending = [True,True])

"""
You are given a DataFrame called df:

order_date	customer_id	product_category	revenue
2026-01-01	101	Electronics	100
2026-01-05	101	Electronics	150
2026-01-10	102	Furniture	200
2026-02-01	101	Electronics	120
2026-02-15	102	Furniture	300
2026-02-20	103	Electronics	180

The business team wants to identify high-value customers and monthly revenue trends.

Interview Questions
Question 1
Convert order_date to datetime and create two new columns:
order_month
day_of_week

Question 2
Calculate monthly revenue by customer.
Expected output columns:
customer_id
order_month
monthly_revenue

Question 3
For each customer, calculate running cumulative revenue over time.
Expected output columns:
customer_id
order_month
monthly_revenue
running_revenue

Question 4
Rank customers within each month by monthly_revenue, highest revenue first.
If two customers tie, they should share the same rank and the next rank should be skipped, like SQL RANK().
Create a new column:
monthly_rank

Question 5
Return the top 2 customers per month by monthly revenue, including ties.
Expected logic:
monthly_rank <= 2

Question 6
Create a pivot table showing monthly revenue by customer.
Expected format:
customer_id	2026-01	2026-02
101	250	120
102	200	300
103	0	180

Question 7
Create a new column:
customer_avg_monthly_revenue
It should show each customer's average monthly revenue repeated on every row.

Question 8
Create a flag:
above_customer_avg
where the row is True if:
monthly_revenue > customer_avg_monthly_revenue
Then return only the rows where the customer performed above their own average.

Question 9
For each customer, calculate month-over-month revenue change.
Create two columns:
prev_month_revenue
mom_change_pct
Formula:
mom_change_pct = (monthly_revenue - prev_month_revenue) / prev_month_revenue
Question 10
Return the top 1 customer per month by monthly revenue, but do not include ties.
Return exactly one customer per month.
"""
import pandas as pd
import numpy as np
df['order_date'] = pd.to_datetime(df['order_date'])
df['order_month'] = df['order_date'].dt.to_period('M')
df['day_of_week'] = df['order_date'].dt.day_name()
monthly = (
    df.groupby(['customer_id', 'order_month'], as_index=False)
      .agg(monthly_revenue=('revenue', 'sum'))
)
monthly = monthly.sort_values(['customer_id', 'order_month'])
monthly['running_revenue'] = (
    monthly.groupby('customer_id')['monthly_revenue']
           .cumsum()
)
monthly['monthly_rank'] = (
    monthly.groupby('order_month')['monthly_revenue']
           .rank(method='min', ascending=False)
)
top2 = monthly[
    monthly['monthly_rank'] <= 2
]

pivot = (
    monthly.pivot_table(
        index='customer_id',
        columns='order_month',
        values='monthly_revenue',
        aggfunc='sum',
        fill_value=0
    )
    .reset_index()
)
monthly['customer_avg_monthly_revenue'] = (
    monthly.groupby('customer_id')['monthly_revenue']
           .transform('mean')
)
monthly['above_customer_avg'] = (
    monthly['monthly_revenue'] >
    monthly['customer_avg_monthly_revenue']
)
above_avg = monthly[
    monthly['above_customer_avg']
]
monthly = monthly.sort_values(['customer_id', 'order_month'])

monthly['prev_month_revenue'] = (
    monthly.groupby('customer_id')['monthly_revenue']
           .shift(1)
)
monthly['mom_change_pct'] = (
    (monthly['monthly_revenue'] - monthly['prev_month_revenue'])
    / monthly['prev_month_revenue'].replace(0, np.nan)
)
monthly = monthly.sort_values(
    ['order_month', 'monthly_revenue'],
    ascending=[True, False]
)
monthly['rank'] = (
    monthly.groupby('order_month')['monthly_revenue']
           .rank(method='first', ascending=False)
)
top1 = monthly[
    monthly['rank'] == 1
]
"""
**Mock Round — Realistic Multi-Step #1**
`shipments`:
- `shipment_id`, `supplier_id`, `part_id`, `ship_date` (string), `cost`, `units`

`suppliers`:
- `supplier_id`, `supplier_name`, `country`

Tasks:
1. Convert `ship_date` to datetime, and create a `month` column (e.g. the year-month period)
2. Join the supplier names and countries onto the shipments
3. Compute `cost_per_unit` for each shipment (guard against divide-by-zero)
4. For each `supplier_name`, compute: total cost, total units, average cost_per_unit, and number of shipments — in one agg call
5. Flag the **top 3 suppliers by total cost** with a `tier` column = `"Key"`, everyone else `"Standard"`
6. Return that supplier summary sorted by total cost descending
"""
shipments['ship_date'] = pd.to_datetime(shipments['ship_date'])  
shipments['month'] = shipments['ship_date'].dt.to_period('M') 
df= pd.merge(shipments,suppliers,on='supplier_id',how='left')  
df['cost_per_unit'] = df['cost']/df['units'].replace(0,np.nan) 
df = df.groupby('supplier_name',as_index= False).agg(total_cost=("cost","sum"),
                                                     total_units = ("units","sum"),
                                                     average_cost_per_unit=("cost_per_unit","mean"), 
                                                     num_of_shipments=("shipment_id","size")) #I assume the shipment_id is a column without nulls so I use size, if there is null then I will use count   
df['rank'] = df['total_cost'].rank(method='min',ascending = False)  
df['tier'] = np.where(df['rank']<=3,"Key","Standard")  
result = df.sort_values(['total_cost'],ascending =False) # for Q5 not sure how we deal with ties so I assume the top 3 means the top 3 revenue so I use min to get the ties also showed up, but if we only want to get 3 rows in result no matter if there is ties then i will use 'first'






