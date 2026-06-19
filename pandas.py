"""
The goal is to swap the id for each 2 department if the total department number is odd, and keep last department id not swapped
| id | swapped_id | name    | swapped_name |
| -- | ---------- | ------- | ------------ |
| 1  | 2          | HR      | Finance      |
| 2  | 1          | Finance | HR           |
| 3  | 4          | Ops     | Sales        |
| 4  | 3          | Sales   | Ops          |
| 5  | 5          | Legal   | Legal        |

"""
import pandas as pd

df = pd.DataFrame({
    "id": [1, 2, 3, 4, 5],
    "name": ["HR", "Finance", "Ops", "Sales", "Legal"]
})
df = df.sort_values("id").reset_index(drop=True)
df["swapped_id"] = df["id"]
df["swapped_name"] = df["name"]
# odd-position rows: take next row
mask_odd = df.index % 2 == 0
df.loc[mask_odd, "swapped_id"] = df["id"].shift(-1)
df.loc[mask_odd, "swapped_name"] = df["name"].shift(-1)

# even-position rows: take previous row
mask_even = df.index % 2 == 1

df.loc[mask_even, "swapped_id"] = df["id"].shift(1)
df.loc[mask_even, "swapped_name"] = df["name"].shift(1)
# if last row has no pair, keep itself
df["swapped_id"] = df["swapped_id"].fillna(df["id"]).astype(int)
df["swapped_name"] = df["swapped_name"].fillna(df["name"])

result = df[["id", "swapped_id", "name", "swapped_name"]]



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

"""
You have `daily_sales` with columns: `store_id`, `region`, `date` (string), `revenue`.
assume each store belongs to exactly one region
Multiple rows per store (one per day). Work through these — and for **each step, before you write code, say one word: "collapse" or "keep"** (i.e. does this step reduce to fewer rows, or keep all rows?). That's the muscle I want you to build.
1. Convert `date` to datetime and sort by `store_id`, `date`
2. Add a `cumulative_revenue` column — running total of revenue per store over time
3. Add a `rolling_7day_avg` — 7-day rolling average of revenue per store
4. Compute total revenue per store (one number per store)
5. Add a column `pct_of_region` — each store's total as a % of its region's total revenue
6. Find stores in the **top 10%** by total revenue (the 90th percentile threshold and above)
"""
daily_sales['date'] = pd.to_datetime(daily_sales['date'])  
daily_sales = daily_sales.sort_values(['store_id','date'],ascending = [True,True]) 
daily_sales['cumulative_revenue'] = daily_sales.groupby('store_id')['revenue'].cumsum() # keep all rows but running total by store which means the store_id will be the partition by in SQL and cumsum() is the one that expanding the same rows.
daily_sales['rolling_7day_avg'] = daily_sales.groupby('store_id')['revenue'].transform(lambda x : x.rolling('7').mean()) # keep all rows but again we need reset by store so i need groupby and also here I do not know if we care about the data leakage or not, if we calculate the 7 days rolling average without current day then I will need to do x.shift(1).rolling(7)
daily_sales['total_rev_store'] = daily_sales.groupby('store_id')['revenue'].transform('sum') # keep all rows since we are going to use this total_revenue_per_store in next part. so I use transform('sum') to expanding all rows with the total per store. # pause here i will be back for Q5 and 5
daily_sales['total_rev_region'] = daily_sales.groupby('region')['revenue'].transform('sum')
daily_sales['pct_of_region'] = daily_sales['total_rev_store']/daily_sales['total_rev_region'].replace(0,np.nan)
store_totals = daily_sales[['store_id', 'total_rev_store']].drop_duplicates() # make sure we have clean data when we want to doany distribution calculation or it will find wrong one with duplicates data
top_rev = daily_sales['total_rev_store'].quantile(0.9) 
result = daily_sales[daily_sales['total_rev_store']>=top_rev]
"""
 top n stores within region if one store could show up in multiple regions
"""
# Step 1: collapse to store + region grain (revenue per store IN each region)
store_region = (
    daily_sales.groupby(['region', 'store_id'], as_index=False)['revenue'].sum()
)
# Step 2: rank stores WITHIN each region
store_region['rank'] = (
    store_region.groupby('region')['revenue'].rank(method='min', ascending=False)
)
# Step 3: keep top 3 per region
result = store_region[store_region['rank'] <= 3].sort_values(
    ['region', 'rank'], ascending=[True, True]
)

"""
You have remanufacture_log with columns: part_id, supplier_id, defect_type, remfg_date (string), cost_to_remfg, redeployed (bool), defected_again (bool — True if it failed again after redeployment).
The data is messy (some NaNs). 

Clean: convert remfg_date to datetime; rows where part_id is null should be dropped; fill missing cost_to_remfg with the median
Compute, per supplier_id: total parts remanufactured, the re-defect rate (% of redeployed parts that defected again), and total remfg cost
Flag suppliers with a re-defect rate above the 75th percentile as "High Risk"
Among only "High Risk" suppliers, find the single defect_type that appears most often
"""
df['remfg_date'] = pd.to_datetime('df['remfg_date']')  
df=df.dropna(subset = ['part_id']) 
med = df['cost_to_remfg'].median()  
df['cost_to_remfg'] = df['cost_to_remfg'].fillna(med)
result = df.groupby('supplier_id',as_index=False).agg(total_remfg = ("part_id","size"),
                                                      re_defect = ("defected_again","sum"),
                                                      total_remfg_cost=("cost_to_remfg","sum"),
                                                      redeployed=("redeployed","sum"))  
result['re_defect_rate'] = result['re_defect'] / result['redeployed'].replace(0,np.nan) # here I am thinking about the redefect rate, so that means a parts has to be redeployed and then re defect again so redeployed is the mandatory request for being redefect so I do not have to think about if a part is not redeployed but redefect. 
threshold = result['re_defect_rate'].quantile(0.75)  
result['flag'] = np.where(result['re_defect_rate']>threshold,'High Risk','Low Risk') 

df1 = result.loc[result['flag']=='High Risk'] 
#or we do not need to merge but 
"""high_risk_ids = result.loc[result['flag'] == 'High Risk', 'supplier_id']
final = df[df['supplier_id'].isin(high_risk_ids)]"""

final = pd.merge(df1[['supplier_id']],df[['supplier_id','defect_type']], on='supplier_id',how='left') 
final = final.groupby('defect_type').agg(number = ("supplier_id","count")).reset_index()  
final = final.sort_values('number',ascending = False).head(1)


"""
**Grain Drill — spot the trap at each step**
You have `enrollments` with columns: `student_id`, `school`, `district`, `course`, `tuition_paid`.
Each student takes multiple courses (so multiple rows per student). A student belongs to one school; a school belongs to one district.
For each step, the question is the same: **do I need to dedupe/aggregate to a particular grain first, or can I work on the raw rows?** Say your reasoning, then code.
1. Total tuition collected per district
2. The **average tuition per student** within each district (i.e. average of each student's *total* tuition, across students in that district)
3. The **median student total tuition** across the whole dataset
4. Each student's tuition as a **% of their school's total tuition**
"""
df = enrollments.groupby('district',as_index = False).agg(total_tuition = ("tuition_paid","sum"))
enrollments['district_tuition'] = enrollments.groupby('district')['tuition_paid'].transform('sum')
enrollments['student_total'] = enrollments.groupby('student_if')['tuition_paid'].transform('sum')
# Stage 1: each student's TOTAL (sum their courses)
student_totals = enrollments.groupby(['district','student_id'], as_index=False).agg(
    student_total=("tuition_paid","sum")
)
# Stage 2: average those student totals within district
df2 = student_totals.groupby('district', as_index=False).agg(
    avg_per_student=("student_total","mean")
)
student_totals = enrollments.groupby('student_id', as_index=False).agg(
    student_total=("tuition_paid", "sum")
)
med = student_totals['student_total'].median()
df3 = enrollments.groupby(['student_id','school'],as_index=False).agg(student_school_paid = ("tuition_paid","sum"))
df3['school_total'] = df3.groupby('school')['student_school_paid'].transform('sum')
df3['perc'] = df3['tuition_paid']/df3['school_total'].replace(0,np.nan)







