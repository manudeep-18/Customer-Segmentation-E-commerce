from flask import Flask, render_template, request, send_file
import pandas as pd
import numpy as np
import ast
import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import warnings
warnings.filterwarnings('ignore')

os.environ['MPLBACKEND'] = 'Agg'
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.ioff()

# Helper functions to parse and compute missing columns
def get_purchase_count(history):
    try:
        if history.startswith('['):
            return len(ast.literal_eval(history))
        else:
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
            return 1
    except:
        return 0

def extract_date_from_history(history):
    """Extract most recent date from purchase history"""
    try:
        if history.startswith('['):
            items = ast.literal_eval(history)
            if items and isinstance(items[0], dict):
                if 'Date' in items[0]:
                    return pd.to_datetime(items[0]['Date'])
                elif 'Purchase Date' in items[0]:
                    return pd.to_datetime(items[0]['Purchase Date'])
        else:
            if 'Purchase Date' in history:
                import re
                dates = re.findall(r'(\d{4}-\d{2}-\d{2})', history)
                if dates:
                    return pd.to_datetime(dates[0])
    except:
        pass
    return pd.Timestamp.now()

def calculate_rfm(data):
    """Calculate RFM (Recency, Frequency, Monetary) metrics"""
    reference_date = pd.Timestamp.now()
    
    # Extract purchase dates
    data['Purchase_Date'] = data['Purchase History'].apply(extract_date_from_history)
    
    # Recency (days since last purchase)
    data['Recency'] = (reference_date - data['Purchase_Date']).dt.days
    data['Recency'] = data['Recency'].clip(lower=1)  # Avoid 0 values
    
    # Frequency (number of purchases)
    data['Frequency'] = data['Purchase History'].apply(get_purchase_count)
    data['Frequency'] = data['Frequency'].clip(lower=1)
    
    # Monetary (total spending)
    data['Monetary'] = data['Purchase History'].apply(get_avg_spending)
    data['Monetary'] = data['Monetary'] * data['Frequency']
    data['Monetary'] = data['Monetary'].clip(lower=0.01)
    
    return data

def convert_usd_to_inr(value):
    try:
        return float(value) * 83
    except (TypeError, ValueError):
        return 0

def format_currency_inr(value, decimals=0):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "₹0"

    negative = number < 0
    number = abs(number)
    fmt = f"{number:.{decimals}f}"
    if "." in fmt:
        integer_part, fractional_part = fmt.split(".")
    else:
        integer_part, fractional_part = fmt, ""

    if len(integer_part) <= 3:
        grouped = integer_part
    else:
        last3 = integer_part[-3:]
        rest = integer_part[:-3]
        parts = []
        while len(rest) > 2:
            parts.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.append(rest)
        grouped = ",".join(reversed(parts)) + "," + last3

    if decimals and fractional_part:
        grouped = f"{grouped}.{fractional_part}"

    sign = "-" if negative else ""
    return f"₹{sign}{grouped}"

CHURN_RISK_LEVELS = ["High Risk", "Medium Risk", "Low Risk"]
CHURN_ACTIONS = {
    "High Risk": "Win-back campaign",
    "Medium Risk": "Engagement email",
    "Low Risk": "Loyalty rewards"
}

def get_churn_risk_level(probability):
    if probability > 0.7:
        return "High Risk"
    if probability >= 0.4:
        return "Medium Risk"
    return "Low Risk"

def build_churn_labels(data):
    """Approximate churn labels from RFM heuristics to bootstrap the classifier"""
    quantiles = data[["Recency", "Frequency", "Purchase_Intensity"]].quantile([0.25, 0.75])
    recency_thresh = quantiles.loc[0.75, "Recency"]
    frequency_thresh = quantiles.loc[0.25, "Frequency"]
    intensity_thresh = quantiles.loc[0.25, "Purchase_Intensity"]

    churn_flag = (
        (data["Recency"] >= recency_thresh) &
        (data["Frequency"] <= frequency_thresh) &
        (data["Purchase_Intensity"] <= intensity_thresh)
    ).astype(int)

    if churn_flag.nunique() < 2:
        pivot = len(churn_flag) // 2
        churn_flag = pd.Series([1 if i < pivot else 0 for i in range(len(churn_flag))], index=data.index)
    else:
        churn_flag.index = data.index

    return churn_flag

def train_churn_model(data, feature_cols):
    training_data = data[feature_cols].copy().fillna(0)
    labels = build_churn_labels(data)
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(training_data, labels)
    return model

def apply_churn_predictions(data, model, feature_cols):
    feature_values = data[feature_cols].copy().fillna(0)
    probabilities = model.predict_proba(feature_values)[:, 1]
    data["churn_probability"] = probabilities
    data["churn_risk_level"] = data["churn_probability"].apply(get_churn_risk_level)
    data["suggested_action"] = data["churn_risk_level"].map(CHURN_ACTIONS)
    return data

CLV_TIERS = ["High Value", "Medium Value", "Low Value"]

def build_clv_baseline(data, lifespan_months=12):
    safe_freq = data["Frequency"].replace(0, 1)
    data["avg_purchase_value"] = data["Monetary"] / safe_freq
    data["baseline_clv"] = data["avg_purchase_value"] * data["Frequency"] * lifespan_months
    return data

def train_clv_model(data, feature_cols, target):
    training_data = data[feature_cols].copy().fillna(0)
    model = RandomForestRegressor(n_estimators=150, random_state=42)
    model.fit(training_data, target)
    return model

def classify_value_tier(value, percentiles):
    p40, p75 = percentiles
    if value > p75:
        return "High Value"
    if value >= p40:
        return "Medium Value"
    return "Low Value"

def find_optimal_k(X_scaled, max_k=10):
    """Find optimal number of clusters using silhouette score"""
    silhouette_scores = []
    k_range = range(2, min(max_k + 1, len(X_scaled)))
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        silhouette_scores.append(score)
    
    optimal_k = list(k_range)[np.argmax(silhouette_scores)]
    return optimal_k

app = Flask(__name__)
app.add_template_filter(format_currency_inr, 'format_currency_inr')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    view_mode = request.form.get('view_mode', 'basic')
    file = request.files.get("file")

    def normalize_frame(df):
        df = df.copy()
        # Map common alternative column names to expected schema
        if 'CustomerID' in df.columns:
            df['Customer ID'] = df['CustomerID']
        if 'Customer ID' not in df.columns:
            if 'CustomerID' in df.columns:
                df['Customer ID'] = df['CustomerID']
            else:
                df['Customer ID'] = range(1, len(df) + 1)

        # Annual income: convert from k$ if needed
        if 'AnnualIncome(k$)' in df.columns:
            try:
                df['Annual Income'] = df['AnnualIncome(k$)'] * 1000
            except Exception:
                df['Annual Income'] = df['AnnualIncome(k$)']

        if 'Annual Income' not in df.columns:
            df['Annual Income'] = df.get('Annual Income', np.nan)

        # Purchase/Browsing history defaults
        if 'Purchase History' not in df.columns:
            df['Purchase History'] = '[]'
        if 'Browsing History' not in df.columns:
            df['Browsing History'] = '[]'
        if 'Product Reviews' not in df.columns:
            df['Product Reviews'] = ''

        # Time on Site: use SpendingScore if available
        if 'Time on Site' not in df.columns:
            if 'SpendingScore(1-100)' in df.columns:
                df['Time on Site'] = df['SpendingScore(1-100)']
            elif 'SpendingScore' in df.columns:
                df['Time on Site'] = df['SpendingScore']
            else:
                df['Time on Site'] = 0

        # Age/Gender/Location defaults
        if 'Age' not in df.columns:
            df['Age'] = np.nan
        if 'Gender' not in df.columns:
            df['Gender'] = 'Other'
        if 'Location' not in df.columns:
            df['Location'] = 'Unknown'

        return df

    if file and getattr(file, 'filename', ''):
        data = pd.read_csv(file)
        data = normalize_frame(data)
    else:
        base = os.path.dirname(__file__)
        f1 = os.path.join(base, 'data.csv')
        f2 = os.path.join(base, 'sample_customers.csv')
        f3 = os.path.join(base, 'realistic_customers.csv')
        frames = []
        if os.path.exists(f1):
            df1 = pd.read_csv(f1)
            frames.append(normalize_frame(df1))
        if os.path.exists(f2):
            df2 = pd.read_csv(f2)
            frames.append(normalize_frame(df2))
        if os.path.exists(f3):
            df3 = pd.read_csv(f3)
            frames.append(normalize_frame(df3))
        if not frames:
            return "No file uploaded and default CSVs not found.", 400
        data = pd.concat(frames, ignore_index=True, sort=False)

    # Fill missing non-critical fields with sensible defaults instead of dropping rows
    data = data.fillna({
        'Gender': 'Other',
        'Location': 'Unknown',
        'Purchase History': '[]',
        'Browsing History': '[]',
        'Product Reviews': '',
        'Time on Site': 0,
        'Annual Income': 0
    })

    # Compute missing columns
    data['Purchase Frequency'] = data['Purchase History'].apply(get_purchase_count)
    data['Spending Score'] = data['Purchase History'].apply(get_avg_spending)
    data['Pages Viewed'] = data['Browsing History'].apply(get_browsing_count)
    data['Time Spent'] = data['Time on Site']

    # Calculate RFM metrics
    data = calculate_rfm(data)

    # Feature Engineering
    data["Engagement_Score"] = data["Time Spent"] + data["Pages Viewed"]
    data["Purchase_Intensity"] = data["Frequency"] * data["Spending Score"]
    data["Customer_Value"] = data["Annual Income"] * data["Purchase_Intensity"]
    data["Monetary_INR"] = data["Monetary"] * 83
    churn_features = ["Recency", "Frequency", "Monetary", "Annual Income", "Engagement_Score", "Time on Site", "Purchase_Intensity"]
    churn_model = train_churn_model(data, churn_features)
    data = apply_churn_predictions(data, churn_model, churn_features)

    clv_features = ["Frequency", "Monetary", "avg_purchase_value", "Recency", "Annual Income", "Engagement_Score"]
    data = build_clv_baseline(data)
    data["avg_purchase_value_inr"] = data["avg_purchase_value"] * 83
    data["baseline_clv_inr"] = data["baseline_clv"] * 83
    clv_model = train_clv_model(data, clv_features, data["baseline_clv"])
    data["predicted_clv"] = clv_model.predict(data[clv_features].copy().fillna(0))
    data["predicted_clv_inr"] = data["predicted_clv"].apply(convert_usd_to_inr)
    clv_percentiles = np.nanpercentile(data["predicted_clv_inr"], [40, 75])
    data["value_tier"] = data["predicted_clv_inr"].apply(lambda x: classify_value_tier(x, clv_percentiles))

    # Combine RFM with KMeans features
    X = data[["Recency", "Frequency", "Monetary", "Engagement_Score", "Purchase_Intensity", "Customer_Value"]]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Find optimal K using silhouette score
    optimal_k = find_optimal_k(X_scaled, max_k=10)
    
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    data["Cluster"] = kmeans.fit_predict(X_scaled)

    # Segment names and marketing recommendations
    segment_info = {
        0: {"name": "Champions", "icon": "🏆", "color": "#FF6B6B", "description": "Highest value customers - VIP treatment"},
        1: {"name": "Loyal Customers", "icon": "💎", "color": "#4ECDC4", "description": "Consistent repeat buyers"},
        2: {"name": "At Risk", "icon": "⚠️", "color": "#FFE66D", "description": "Previously active, now dormant"},
        3: {"name": "Potential", "icon": "🌱", "color": "#95E1D3", "description": "New or infrequent buyers"},
        4: {"name": "Casual", "icon": "👤", "color": "#A8D8EA", "description": "Low engagement customers"},
    }
    
    # Map cluster names and colors
    if optimal_k < len(segment_info):
        cluster_map = {i: segment_info[i] for i in range(optimal_k)}
    else:
        cluster_map = {i: {"name": f"Segment {i}", "icon": "📊", "color": f"hsl({i*60}, 70%, 60%)", "description": f"Cluster {i}"} for i in range(optimal_k)}
    
    data["Cluster_Name"] = data["Cluster"].map(lambda x: cluster_map.get(x, {}).get("name", f"Cluster {x}"))
    data["Segment_Color"] = data["Cluster"].map(lambda x: cluster_map.get(x, {}).get("color", "#999"))
    data["Segment_Icon"] = data["Cluster"].map(lambda x: cluster_map.get(x, {}).get("icon", "📊"))

    # Generate visualizations
    generate_2d_visualizations(data, X_scaled, cluster_map)
    
    # Calculate segment summaries
    segment_summaries = calculate_segment_profiles(data, cluster_map)
    
    # Marketing recommendations
    marketing_recs = get_marketing_recommendations(segment_summaries)

    # RFM summary
    rfm_summary = data[["Cluster_Name", "Recency", "Frequency", "Monetary_INR"]].groupby("Cluster_Name").agg({
        "Recency": "mean",
        "Frequency": "mean", 
        "Monetary_INR": "mean"
    }).round(2).to_dict('index')

    churn_records = data[["Customer ID", "churn_probability", "churn_risk_level", "suggested_action"]].copy()
    churn_records_sorted = churn_records.sort_values("churn_probability", ascending=False)
    churn_display = churn_records_sorted.head(100).to_dict('records')
    churn_distribution = data["churn_risk_level"].value_counts().reindex(CHURN_RISK_LEVELS, fill_value=0).to_dict()
    churn_counts = [churn_distribution.get(level, 0) for level in CHURN_RISK_LEVELS]

    total_predicted_value = data["predicted_clv_inr"].sum()
    value_tier_counts = data["value_tier"].value_counts().reindex(CLV_TIERS, fill_value=0)
    clv_hist_counts, clv_bin_edges = np.histogram(data["predicted_clv_inr"], bins=12)
    clv_hist_labels = [
        f"{clv_bin_edges[i]:.1f} - {clv_bin_edges[i+1]:.1f}"
        for i in range(len(clv_bin_edges) - 1)
    ]
    clv_top10 = data.nlargest(10, "predicted_clv_inr")[["Customer ID", "predicted_clv_inr", "value_tier"]].to_dict('records')

    # Store latest analysis in app config for downloads
    try:
        app.config['LAST_ANALYSIS'] = {
            'data_csv': data.to_csv(index=False),
            'segment_summaries': segment_summaries,
            'marketing_recs': marketing_recs,
            'rfm_summary': rfm_summary,
            'optimal_k': optimal_k,
            'silhouette_score': float(silhouette_score(X_scaled, data["Cluster"].values)),
            'cluster_map': cluster_map,
            'churn_summary': churn_distribution,
            'churn_records': churn_records_sorted.head(25).to_dict('records'),
            'clv_summary': value_tier_counts.to_dict(),
            'clv_top10': clv_top10
        }
    except Exception:
        app.config.pop('LAST_ANALYSIS', None)

    return render_template(
        "result.html",
        view_mode=view_mode,
        optimal_k=optimal_k,
        cluster_map=cluster_map,
        segment_summaries=segment_summaries,
        marketing_recs=marketing_recs,
        rfm_summary=rfm_summary,
        data=data.to_dict('records'),
        churn_data=churn_display,
        churn_labels=CHURN_RISK_LEVELS,
        churn_counts=churn_counts,
        total_customers=len(data),
        silhouette_score=silhouette_score(X_scaled, data["Cluster"].values),
        total_predicted_value=total_predicted_value,
        clv_hist_labels=clv_hist_labels,
        clv_hist_counts=clv_hist_counts.tolist(),
        clv_top10=clv_top10,
        clv_value_tiers=[value_tier_counts.get(t, 0) for t in CLV_TIERS],
        clv_tier_labels=CLV_TIERS
    )

def calculate_segment_profiles(data, cluster_map):
    """Calculate detailed profiles for each segment"""
    profiles = {}
    
    for cluster_id in data["Cluster"].unique():
        segment_data = data[data["Cluster"] == cluster_id]
        cluster_name = cluster_map.get(cluster_id, {}).get("name", f"Cluster {cluster_id}")
        
        avg_income_inr = segment_data["Annual Income"].mean() * 83
        avg_monetary_inr = segment_data["Monetary_INR"].mean()
        profiles[cluster_name] = {
            "count": len(segment_data),
            "percentage": round((len(segment_data) / len(data) * 100), 1),
            "avg_age": round(segment_data["Age"].mean(), 1),
            "avg_income": round(avg_income_inr, 0),
            "avg_frequency": round(segment_data["Frequency"].mean(), 1),
            "avg_monetary": round(avg_monetary_inr, 2),
            "avg_recency": round(segment_data["Recency"].mean(), 1),
            "avg_engagement": round(segment_data["Engagement_Score"].mean(), 1),
            "color": cluster_map.get(cluster_id, {}).get("color", "#999"),
            "icon": cluster_map.get(cluster_id, {}).get("icon", "📊"),
        }
    
    return profiles

def get_marketing_recommendations(profiles):
    """Generate marketing recommendations based on segment profiles"""
    recommendations = {}
    
    for segment, data in profiles.items():
        if "Champions" in segment:
            recommendations[segment] = [
                "🎯 VIP exclusive perks and early access to new products",
                "💝 Personalized gifts and birthday discounts",
                "👥 Invite to exclusive events and product launches",
                "📊 Dedicated account manager for premium support"
            ]
        elif "Loyal" in segment:
            recommendations[segment] = [
                "🔄 Loyalty rewards program with point multipliers",
                "📧 Weekly personalized recommendations",
                "🎁 Cross-sell premium product bundles",
                "⭐ Exclusive member discounts (10-15%)"
            ]
        elif "At Risk" in segment:
            recommendations[segment] = [
                "⚡ Urgency-based re-engagement campaigns",
                "💰 Limited-time special offers (20-30% off)",
                "📞 Personal follow-up email from customer service",
                "🎯 Win-back incentives: Free shipping or gift"
            ]
        elif "Potential" in segment:
            recommendations[segment] = [
                "🌟 First-purchase incentive (10-15% off next order)",
                "📚 Educational content about products",
                "🚀 Free trial or sample offers",
                "💌 Welcome series emails with success stories"
            ]
        else:  # Casual
            recommendations[segment] = [
                "📱 Social media engagement campaigns",
                "🎉 Seasonal promotions and flash sales",
                "📧 Monthly newsletter with trending items",
                "🔗 Referral program incentives"
            ]
    
    return recommendations

def generate_2d_visualizations(data, X_scaled, cluster_map):
    """Generate 2D visualizations for clusters"""
    from sklearn.decomposition import PCA
    
    # PCA for 2D visualization
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    # Color map
    colors_list = [cluster_map.get(i, {}).get("color", "#999") for i in range(len(cluster_map))]
    
    plt.figure(figsize=(12, 7))
    for cluster_id in sorted(data["Cluster"].unique()):
        mask = data["Cluster"] == cluster_id
        plt.scatter(X_pca[mask, 0], X_pca[mask, 1], 
                   label=cluster_map.get(cluster_id, {}).get("name", f"Cluster {cluster_id}"),
                   alpha=0.7, s=80, color=colors_list[cluster_id])
    
    plt.xlabel(f"PCA Component 1 ({pca.explained_variance_ratio_[0]:.1%} variance)")
    plt.ylabel(f"PCA Component 2 ({pca.explained_variance_ratio_[1]:.1%} variance)")
    plt.title("Customer Segments - 2D Visualization", fontsize=14, fontweight='bold')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    scatter_path = os.path.join(os.path.dirname(__file__), 'static', 'scatter.png')
    plt.savefig(scatter_path, dpi=100, bbox_inches='tight')
    plt.close()

    # Distribution pie chart
    plt.figure(figsize=(10, 6))
    segment_counts = data["Cluster_Name"].value_counts()
    colors_pie = [cluster_map.get(data[data["Cluster_Name"]==name]["Cluster"].iloc[0], {}).get("color", "#999") 
                  for name in segment_counts.index]
    plt.pie(segment_counts.values, labels=segment_counts.index, autopct="%1.1f%%", 
            colors=colors_pie, startangle=90)
    plt.title("Customer Distribution by Segment", fontsize=14, fontweight='bold')
    plt.tight_layout()
    pie_path = os.path.join(os.path.dirname(__file__), 'static', 'pie.png')
    plt.savefig(pie_path, dpi=100, bbox_inches='tight')
    plt.close()

    # RFM heatmap
    rfm_data = data[["Cluster_Name", "Recency", "Frequency", "Monetary"]].groupby("Cluster_Name").mean()
    rfm_normalized = (rfm_data - rfm_data.min()) / (rfm_data.max() - rfm_data.min())
    
    plt.figure(figsize=(10, 6))
    im = plt.imshow(rfm_normalized.T, cmap='RdYlGn', aspect='auto')
    plt.colorbar(im, label='Normalized Value')
    plt.xticks(range(len(rfm_normalized)), rfm_normalized.index, rotation=45, ha='right')
    plt.yticks(range(len(rfm_normalized.columns)), rfm_normalized.columns)
    plt.title("RFM Profile by Segment", fontsize=14, fontweight='bold')
    plt.tight_layout()
    heatmap_path = os.path.join(os.path.dirname(__file__), 'static', 'rfm_heatmap.png')
    plt.savefig(heatmap_path, dpi=100, bbox_inches='tight')
    plt.close()

@app.route("/download_report/<format>", methods=["GET"])
def download_report(format):
    """Generate and download report in PDF or CSV format"""
    analysis = app.config.get('LAST_ANALYSIS')
    if not analysis:
        return "No analysis available. Please run an analysis first.", 400

    fmt = format.lower()
    if fmt == 'csv':
        csv_bytes = analysis.get('data_csv', '').encode('utf-8')
        return send_file(io.BytesIO(csv_bytes), mimetype='text/csv', as_attachment=True, download_name='segmentation_report.csv')

    if fmt == 'pdf':
        # Build PDF report
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=14, leading=16))
        elements = []

        # Title
        elements.append(Paragraph('Customer Segmentation Report', styles['Title']))
        elements.append(Spacer(1, 12))

        # Summary
        summary_text = f"Total Segments: {analysis.get('optimal_k', '')} — Silhouette: {analysis.get('silhouette_score', ''):.3f}"
        elements.append(Paragraph(summary_text, styles['Normal']))
        elements.append(Spacer(1, 12))

        # Add segment summary table
        segs = analysis.get('segment_summaries', {})
        if segs:
            table_data = [["Segment", "Count", "%", "Avg Age", "Avg Income", "Freq", "Monetary", "Recency"]]
            for seg_name, prof in segs.items():
                table_data.append([
                    seg_name,
                    str(prof.get('count', '')),
                    f"{prof.get('percentage', '')}%",
                    str(prof.get('avg_age', '')),
                    f"${prof.get('avg_income', '')}",
                    str(prof.get('avg_frequency', '')),
                    f"${prof.get('avg_monetary', '')}",
                    f"{prof.get('avg_recency', '')}d"
                ])

            t = Table(table_data, hAlign='LEFT')
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER')
            ]))
            elements.append(t)
            elements.append(Spacer(1, 12))

        # Marketing recommendations
        recs = analysis.get('marketing_recs', {})
        if recs:
            elements.append(Paragraph('Marketing Recommendations', styles['Heading2']))
            for seg, rec_list in recs.items():
                elements.append(Paragraph(f"<b>{seg}</b>", styles['Heading3']))
                for r in rec_list:
                    elements.append(Paragraph(f"• {r}", styles['Normal']))
                elements.append(Spacer(1, 6))
        churn_summary = analysis.get('churn_summary', {})
        if churn_summary:
            elements.append(Paragraph('Churn Risk Distribution', styles['Heading2']))
            table_data = [["Risk Level", "Count", "Suggested Action"]]
            for risk in CHURN_RISK_LEVELS:
                table_data.append([
                    risk,
                    str(churn_summary.get(risk, 0)),
                    CHURN_ACTIONS.get(risk, "")
                ])

            churn_table = Table(table_data, hAlign='LEFT')
            churn_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1d4ed8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER')
            ]))
            elements.append(churn_table)
            elements.append(Spacer(1, 12))

        # Include images if available
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        for img_name in ('pie.png', 'scatter.png', 'rfm_heatmap.png'):
            img_path = os.path.join(static_dir, img_name)
            if os.path.exists(img_path):
                try:
                    img = Image(img_path, width=6*inch, height=3*inch)
                    elements.append(PageBreak())
                    elements.append(img)
                    elements.append(Spacer(1, 12))
                except Exception:
                    pass

        doc.build(elements)
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='segmentation_report.pdf')

    return "Unsupported format", 400

# -------------------- Optional Local Run -------------------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
