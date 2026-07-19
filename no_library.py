tickets = [
    {"id": 101, "team": "Design",  "hours": 5,  "status": "closed"},
    {"id": 102, "team": "Billing", "hours": 12, "status": "open"},
    {"id": 103, "team": "Design",  "hours": 3,  "status": "open"},
    {"id": 104, "team": "Billing", "hours": 8,  "status": "closed"},
    {"id": 105, "team": "Infra",   "hours": 20, "status": "open"},
    {"id": 106, "team": "Design",  "hours": 2,  "status": "closed"},
]
#Total hours for tickets that are "open"
def total_hour(rows):
    total = 0
    for t in rows:
        if t['status'] == 'open':
            total = total + t['hours']
    return total
#Count by group. How many tickets per team, as a dict. (Answer: {'Design': 3, 'Billing': 2, 'Infra': 1})
def count_by_group(rows):
    count = {}
    for t in rows:
        team = t['team']
        count[team] = count.get(team,0) + 1
    return count
# Sum by group. Total hours per team, as a dict. (Answer: {'Design': 10, 'Billing': 20, 'Infra': 20})
def sum_by_group(rows):
    result = {}
    for t in rows:
        team = t['team']
        hours = t['hours']
        result[team] = result.get(team,0) + hours
    return result

#or 
def sum_by_group(rows):
    result = {}
    for t in rows:
        team = t['team']
        result[team] = result.get(team,0) + t['hours']
    return result
#Collect a list. The ids of tickets with at least 8 hours. (Answer: [102, 104, 105]) Read that boundary carefully.
def list_id(rows):
    result = []
    for t in rows:
        if t['hours'] >= 8:
            result.append(t['id'])
    return result
#The twist: percentage. What percent of tickets are "closed"? (Answer: 50.0) Shape: count the closed ones, divide by total, times 100. 
def percentage(rows):
    perc = 0
    for t in rows:
        if t['status'] == 'closed':
            perc = perc + 1
    return 100*perc/len(rows)

""" given a list of transactions write a function to return 
transactions = [
    ("Alice", 120),
    ("Bob", 50),
    ("Alice", 80),
    ("Charlie", 40),
    ("Bob", 70),
]
output:
{
    "Alice": 200,
    "Bob": 120,
    "Charlie": 40
}"""
from collections import defaultdict
def total_spending(transactions):
  result = {}
  for letter, number in transactions:
     result[letter] = result.get(letter, 0) + number
  return(dict(result))
from collections import Counter, defaultdict
import random, statistics
text = "apple pie"
# Count characters (including spaces)
char_counts = Counter(text)

data = ["apple", "banana", "apple", "cherry", "banana"]
# Remove duplicates using set
unique_data = list(set(data))


def max_sub_array_of_size_k(k, arr):
    if not arr or k > len(arr):
        return 0
    # 1. Calculate the sum of the very first window
    window_sum = sum(arr[:k])
    max_sum = window_sum
    # 2. Slide the window across the rest of the list
    for i in range(k, len(arr)):
        # Add the next element, subtract the element leaving the back
        window_sum += arr[i] - arr[i - k]
        max_sum = max(max_sum, window_sum)
    return max_sum
# Example usage:
nums = [2, 1, 5, 1, 3, 2]
k = 3
print(max_sub_array_of_size_k(k, nums))  # Output: 9 (from subarray)


def find_longest_substring(s: str) -> str:
    char_map = {}
    left = 0
    max_length = 0
    start_idx = 0
    for right, char in enumerate(s):
        if char in char_map and char_map[char] >= left:
            left = char_map[char] + 1
        char_map[char] = right
        if (right - left + 1) > max_length:
            max_length = right - left + 1
            start_idx = left
    return s[start_idx : start_idx + max_length]
print(find_longest_substring("pwwkew"))  # Output: "wke"


# ---- Our "table": a list of dicts. Each dict = one row. ----

customers = [
    {"id": 1, "name": "Acme",     "plan": "Enterprise", "seats": 120, "region": "US", "arr": 240000},
    {"id": 2, "name": "Globex",   "plan": "Pro",        "seats": 12,  "region": "EU", "arr": 3600},
    {"id": 3, "name": "Initech",  "plan": "Enterprise", "seats": 80,  "region": "US", "arr": 160000},
    {"id": 4, "name": "Umbrella", "plan": "Pro",        "seats": 25,  "region": "APAC","arr": 7500},
    {"id": 5, "name": "Soylent",  "plan": "Org",        "seats": 45,  "region": "EU", "arr": 54000},
    {"id": 6, "name": "Hooli",    "plan": "Pro",        "seats": 8,   "region": "US", "arr": 2400},
]

print("="*60); print("1. LOOP + ACCUMULATE  (the foundation)")
total_seats = 0
for c in customers:
    total_seats += c["seats"]
print("total seats:", total_seats)

print("="*60); print("2. FILTER via comprehension  (SQL WHERE)")
us_customers = [c for c in customers if c["region"] == "US"]
print("US names:", [c["name"] for c in us_customers])

print("="*60); print("3. GROUP + COUNT  (df.groupby.size / COUNT GROUP BY)")
plan_counts = Counter(c["plan"] for c in customers)
print("counts by plan:", dict(plan_counts))
print("most common plan:", plan_counts.most_common(1))

print("="*60); print("4. GROUP + SUM  (df.groupby.sum / SUM GROUP BY)")
arr_by_region = defaultdict(float)
for c in customers:
    arr_by_region[c["region"]] += c["arr"]
print("ARR by region:", dict(arr_by_region))

print("="*60); print("5. GROUP + collect rows  (groupby -> list)")
by_plan = defaultdict(list)
for c in customers:
    by_plan[c["plan"]].append(c["name"])
print("names by plan:", dict(by_plan))

print("="*60); print("6. SORT with key  (ORDER BY)")
top = sorted(customers, key=lambda c: c["arr"], reverse=True)
print("by ARR desc:", [(c["name"], c["arr"]) for c in top])
# multi-key: region asc, then arr desc
multi = sorted(customers, key=lambda c: (c["region"], -c["arr"]))
print("region asc, arr desc:", [(c["region"], c["name"]) for c in multi])

print("="*60); print("7. TOP-K  (sort then slice, or heapq)")
top3 = sorted(customers, key=lambda c: c["arr"], reverse=True)[:3]
print("top 3 by ARR:", [c["name"] for c in top3])

print("="*60); print("8. MIN / MAX / SUM with key")
biggest = max(customers, key=lambda c: c["seats"])
print("most seats:", biggest["name"], biggest["seats"])
print("total arr:", sum(c["arr"] for c in customers))

print("="*60); print("9. RATIO  (watch float division!)")
pro = [c for c in customers if c["plan"] == "Pro"]
pct_pro = 100.0 * len(pro) / len(customers)
print("pct on Pro:", round(pct_pro, 1))

print("="*60); print("10. DEDUP  (set / dict)")
regions = set(c["region"] for c in customers)
print("distinct regions:", sorted(regions))
# dedup rows on a business key, keeping first seen
seen, unique_rows = set(), []
for c in customers + customers:      # simulate duplicates
    if c["id"] not in seen:
        seen.add(c["id"]); unique_rows.append(c)
print("unique row count after dedup:", len(unique_rows))

print("="*60); print("11. SET math  (customers in both months / churn)")
month1 = {1, 2, 3, 4, 5}
month2 = {1, 3, 5, 6, 7}
print("retained:", sorted(month1 & month2))   # intersection
print("churned :", sorted(month1 - month2))   # left only
print("new     :", sorted(month2 - month1))   # right only

print("="*60); print("12. DICT lookup with default  (.get)")
prices = {"Pro": 15, "Org": 45}
print("Pro price:", prices.get("Pro", 0))
print("Enterprise price (missing):", prices.get("Enterprise", 0))

print("="*60); print("13. BUILD a lookup table  (dict comprehension / merge key)")
name_by_id = {c["id"]: c["name"] for c in customers}
print("id 3 ->", name_by_id[3])

print("="*60); print("14. RUNNING / CUMULATIVE total")
monthly = [100, 120, 90, 150]
running, cum = [], 0
for m in monthly:
    cum += m
    running.append(cum)
print("cumulative:", running)

print("="*60); print("15. zip + enumerate")
for i, c in enumerate(customers[:3], start=1):
    print(f"  #{i}: {c['name']}")
seats = [c["seats"] for c in customers]
arrs  = [c["arr"]   for c in customers]
arr_per_seat = [round(a/s, 1) for s, a in zip(seats, arrs)]
print("arr per seat:", arr_per_seat)

print("="*60); print("16. SAMPLING  (random)")
random.seed(42)
sample = random.sample(customers, 2)
print("sampled names:", [c["name"] for c in sample])
print("one random choice:", random.choice(customers)["name"])

print("="*60); print("17. BASIC STATS without numpy  (statistics module)")
s = [c["seats"] for c in customers]
print("mean:", round(statistics.mean(s), 1), "| median:", statistics.median(s))
# or by hand:
print("mean by hand:", round(sum(s)/len(s), 1))

print("="*60); print("18. FUNCTION that ties it together")
def arr_by_plan(rows):
    out = defaultdict(float)
    for r in rows:
        out[r["plan"]] += r["arr"]
    return dict(out)
print(arr_by_plan(customers))

## merge intervals
class Solution:
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        if not intervals:
            return []
        intervals.sort(key=lambda interval:interval[0]) 
        result = [intervals[0]]
        for start,end in intervals[1:]:
            last_end = result[-1][1] #get the last item's second value
            if start > last_end:
                result.append([start,end])
            else:
                result[-1][1] = max(last_end,end)
        return result

orders = [
    {"product": "Design",  "amount": 50},
    {"product": "FigJam",  "amount": 20},
    {"product": "Design",  "amount": 30},
    {"product": "Dev Mode","amount": 40},
]
#Write a function that returns the total amount across all orders. 
def total_revenue(rows):
    total = 0
    for t in rows:
        total = total + t["amount"]
    return total
 
print("1. total:", total_revenue(orders))
#Same orders list. Write a function that returns how many orders have an amount of 40 or more.
def count_big(rows):
    count = 0
    for t in rows:
        if t["amount"] >= 40:
            count = count + 1
    return count
 
print("2. count > 100:", count_big(orders))
#Problem 3 is the group-by — the different one. Not a single count, but a total per product returned as a dictionary. 
def revenue_per_customer(rows):
    totals = {}
    for t in rows:
        name = t["product"]
        totals[name] = totals.get(name, 0) + t["amount"]
    return totals
 
print("3. per customer:", revenue_per_customer(orders))

events = [
    {"user_id": 1, "event": "file_created"},
    {"user_id": 1, "event": "file_shared"},
    {"user_id": 1, "event": "file_shared"},
    {"user_id": 2, "event": "file_created"},
    {"user_id": 3, "event": "file_shared"},
    {"user_id": 2, "event": "comment_added"},
]
#return the number of unique users who performed each event.

from collections import defaultdict
def count_unique_users_by_event(events):
    result = {}
    unique_values = defaultdict(set)
    for t in events:
      unique_values[t['event']].add(t['user_id'])
    result = {event: len(user_id) for event, user_id in unique_values.items()}  
    return result
count_unique_users_by_event(events)
{
    "file_created": 2,
    "file_shared": 2,
    "comment_added": 1
}
#return
{
    "file_created":{
        "unique_users":2,
        "total_events":2
    },
    "file_shared":{
        "unique_users":2,
        "total_events":3
    },
    "comment_added":{
        "unique_users":1,
        "total_events":1
    }
}
def count_unique_users_by_event(events):
    result = {}
    unique_values = defaultdict(set)
    total_counts = defaultdict(int)
    for t in events:
        event = t['event']
        id = t['user_id']
        unique_values[t['event']].add(t['user_id'])
        total_counts[event] += 1
    result = {event: {
        'unique_user': len(user_id),
        'total': total_counts[event]
    }
    for event, user_id in unique_values.items()
} 
    return result
count_unique_users_by_event(events)

#return group by (user_id,event)
{
    (1, "file_created"): 1,
    (1, "file_shared"): 2,
    (2, "file_created"): 1,
    (2, "comment_added"): 1,
    (3, "file_shared"): 1
}
def count_unique_users_by_event(events):
    result = {}
    unique_values = defaultdict(set)
    for row in events:
        key = (row["user_id"], row["event"])
        result[key] = result.get(key, 0) + 1
    return result

#return sorted by count descending event ascending
[
    ("file_shared",2),
    ("file_created",2),
    ("comment_added",1)
]
def count_unique_users_by_event(events):
    result = []
    unique_values = defaultdict(set)
    for t in events:
      unique_values[t['event']].add(t['user_id'])
    result = [(event, len(user_id)) for event, user_id in unique_values.items()]  
    result = sorted(result, key=lambda x: (-x[1], x[0]))
    return result
count_unique_users_by_event(events)
