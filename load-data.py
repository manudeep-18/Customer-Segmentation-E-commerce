import pandas as pd
import ast

# read the data
data = pd.read_csv("data.csv")

# show first 5 rows
print(data.head())

# remove empty rows
data = data.dropna()

# check size
print("Rows and Columns:", data.shape)

# Helper functions to parse and compute missing columns
def get_purchase_count(history):
    try:
        if history.startswith('['):
            return len(ast.literal_eval(history))
        else:
            # Count occurrences of 'Purchase Date' for comma-separated dicts
            return history.count('Purchase Date')
    except:
        return 0

def get_avg_spending(history):
    try:
        if history.startswith('['):
            items = ast.literal_eval(history)
            prices = [item.get('Price', 0) for item in items]
            return sum(prices) / len(prices) if prices else 0
        else:
            # Parse comma-separated dicts
            parts = history.split('},{')
            prices = []
            for part in parts:
                if 'Price' in part:
                    start = part.find("'Price': ") + 9
                    end = part.find(',', start)
                    if end == -1:
                        end = part.find('}', start)
                    price_str = part[start:end].strip()
                    try:
                        prices.append(float(price_str))
                    except:
                        pass
            return sum(prices) / len(prices) if prices else 0
    except:
        return 0

def get_browsing_count(history):
    try:
        if history.startswith('['):
            return len(ast.literal_eval(history))
        else:
            return 1  # Assume 1 for single dict
    except:
        return 0

# Compute missing columns
data['Purchase Frequency'] = data['Purchase History'].apply(get_purchase_count)
data['Spending Score'] = data['Purchase History'].apply(get_avg_spending)
data['Pages Viewed'] = data['Browsing History'].apply(get_browsing_count)
data['Time Spent'] = data['Time on Site']  # Map existing column

# Now select features (using the computed/mapped columns)
features = data[
    ["Time Spent", "Pages Viewed", "Purchase Frequency", "Spending Score", "Annual Income"]
]

print(features.head())

# create new smart features
data["Engagement_Score"] = data["Time Spent"] + data["Pages Viewed"]
data["Purchase_Intensity"] = data["Purchase Frequency"] * data["Spending Score"]
data["Customer_Value"] = data["Annual Income"] * data["Purchase_Intensity"]

print(data[["Engagement_Score", "Purchase_Intensity", "Customer_Value"]].head())

from sklearn.preprocessing import StandardScaler

X = data[["Engagement_Score", "Purchase_Intensity", "Customer_Value"]]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(X_scaled[:5])

from sklearn.cluster import KMeans

kmeans = KMeans(n_clusters=4, random_state=42)
data["Cluster"] = kmeans.fit_predict(X_scaled)

print(data[["Customer_Value", "Cluster"]].head())

import matplotlib.pyplot as plt

# draw picture
plt.scatter(
    data["Engagement_Score"],
    data["Customer_Value"],
    c=data["Cluster"]
)

plt.xlabel("Engagement Score")
plt.ylabel("Customer Value")
plt.title("Customer Segments")
plt.show()

# understand each cluster
cluster_summary = data.groupby("Cluster").mean(numeric_only=True)
print(cluster_summary)
