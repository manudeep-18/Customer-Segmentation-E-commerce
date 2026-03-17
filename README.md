# Customer Segmentation Application

## Project Overview

A comprehensive web application for customer segmentation analysis using machine learning and data visualization. The application processes customer data to identify distinct segments, predict customer lifetime value, and provide actionable marketing insights.

### Key Capabilities

- Customer segmentation using K-means clustering
- RFM (Recency, Frequency, Monetary) analysis
- Customer lifetime value prediction with machine learning
- Churn risk assessment
- Interactive data visualizations
- Marketing recommendation engine
- Report generation and export

## Project Structure

```
customer/
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
├── IMPLEMENTATION_GUIDE.md      # Feature documentation
├── UI_VISUAL_GUIDE.md          # Design system guide
├── FILE_STRUCTURE.md           # File organization guide
├── load-data.py                # Data loading utility
│
└── customer_segmentation_app/
    ├── app.py                   # Flask web application
    ├── data.csv                 # Sample customer data
    ├── realistic_customers.csv  # Alternative sample data
    ├── sample_customers.csv     # Basic sample data
    │
    ├── templates/
    │   ├── index.html           # Landing page
    │   ├── result.html          # Results dashboard
    │   └── style.css            # Stylesheet
    │
    └── static/
        ├── style.css            # CSS styles
        ├── scatter.png          # PCA visualization
        ├── pie.png              # Segment distribution
        ├── rfm_heatmap.png      # RFM analysis
        ├── clv_histogram.png    # CLV distribution
        ├── top_clv_customers.png # Top CLV customers
        └── churn_bar.png        # Churn risk analysis
```

## Features

### 1. Customer Segmentation
- K-means clustering algorithm
- Automatic optimal cluster selection using silhouette score
- Segment profiling with key metrics
- Color-coded segment visualization

### 2. RFM Analysis
- Recency: Days since last purchase
- Frequency: Number of purchases
- Monetary: Total spending value
- Heatmap visualization for segment comparison

### 3. Customer Lifetime Value Prediction
- Machine learning model using RandomForest
- Features: Frequency, Monetary, Recency, Income, Engagement
- Value tier classification (High/Medium/Low)
- Predictive analytics for customer valuation

### 4. Churn Risk Assessment
- ML-based churn probability prediction
- Risk level classification
- Actionable recommendations for retention

### 5. Marketing Recommendations
- Segment-specific marketing strategies
- Personalized recommendations based on customer profiles
- Actionable insights for each customer group

### 6. Data Visualization
- Interactive charts and graphs
- PCA scatter plots for cluster visualization
- Distribution histograms and bar charts
- Heatmaps for metric analysis

### 7. Report Generation
- CSV and PDF export functionality
- Comprehensive analysis reports
- Downloadable visualizations

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation Steps

1. Clone or download the project directory
2. Navigate to the project directory
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   cd customer_segmentation_app
   python app.py
   ```
5. Open web browser and navigate to `http://localhost:5000`

## Usage Instructions

### Basic Workflow

1. **Upload Data**: Select or drag-and-drop a CSV file containing customer data
2. **Choose View Mode**:
   - Basic: Overview and key insights
   - Advanced: Detailed analysis including RFM and churn
3. **Start Analysis**: Click "Start Analysis" to process the data
4. **Explore Results**:
   - Overview: Charts and segment distributions
   - Segment Profiles: Detailed customer group analysis
   - Customer Value: CLV predictions and value tiers
   - RFM Analysis: Recency, frequency, monetary metrics
   - Churn Risk: Customer retention analysis
   - Marketing Recommendations: Actionable strategies
5. **Export Results**: Download CSV or PDF reports

### File Upload Requirements

- File format: CSV
- Minimum records: 2 customers
- Required columns: Customer ID, purchase history data
- Supported: Drag-and-drop or file selection

## Technical Stack

### Backend
- **Framework**: Flask
- **Data Processing**: Pandas, NumPy
- **Machine Learning**: Scikit-learn (KMeans, RandomForest, PCA)
- **Visualization**: Matplotlib
- **PDF Generation**: ReportLab

### Frontend
- **HTML5**: Semantic markup
- **CSS**: Tailwind CSS framework
- **JavaScript**: Vanilla JS for interactions
- **Icons**: Font Awesome

### Data Processing
- **Input**: CSV files with customer data
- **Processing**: In-memory data analysis
- **Output**: JSON for templates, PNG for charts

## API Endpoints

### Routes

- `GET /` - Home page with file upload form
- `POST /analyze` - Process uploaded CSV and generate analysis
- `GET /download_report/<format>` - Download reports (CSV/PDF)

### Request Parameters

**POST /analyze**
- `file`: CSV file (multipart/form-data)
- `view_mode`: "basic" or "advanced" (string)

### Response Data

The analysis endpoint returns processed data including:
- Customer segments and profiles
- CLV predictions and value tiers
- RFM metrics and analysis
- Churn risk assessments
- Marketing recommendations
- Visualization file paths

## Data Requirements

### Input CSV Format

**Required Columns:**
- `Customer ID` - Unique customer identifier
- `Age` - Customer age (numeric)
- `Gender` - Customer gender (text)
- `Annual Income` - Income amount (numeric)
- `Purchase History` - JSON array of purchases

**Optional Columns:**
- `Location` - Geographic location
- `Time on Site` - Engagement metric
- `Browsing History` - Website activity
- `Product Reviews` - Customer feedback

**Sample Data Structure:**
```csv
Customer ID,Age,Gender,Annual Income,Purchase History
1001,28,Female,52000,"[{""Product Category"": ""Clothing"", ""Purchase Date"": ""2022-05-15"", ""Price"": 34.56}]"
1002,35,Male,68000,"[{""Product Category"": ""Electronics"", ""Purchase Date"": ""2022-06-20"", ""Price"": 125.00}]"
```

### Data Validation

- CSV format validation
- Minimum record count checking
- Required column presence verification
- Data type validation for numeric fields

## Visualizations

### 1. PCA Scatter Plot
- Shows customer distribution in 2D space
- Color-coded by segment membership
- Displays cluster separation quality

### 2. Segment Distribution Chart
- Pie chart showing customer count per segment
- Percentage labels for each segment
- Color-coded segments

### 3. RFM Heatmap
- Normalized RFM values across segments
- Color gradient from low to high values
- Comparative segment analysis

### 4. CLV Distribution Histogram
- Customer lifetime value distribution
- Frequency of CLV ranges
- Value concentration analysis

### 5. Top CLV Customers Chart
- Horizontal bar chart of highest value customers
- Customer IDs and CLV amounts
- Ranking visualization

### 6. Churn Risk Distribution
- Customer count by risk level
- High/Medium/Low risk categories
- Risk assessment visualization

## Security Considerations

- Input validation for uploaded files
- File type restriction to CSV only
- No persistent data storage
- In-memory processing only
- Safe file handling practices
- Error handling for malformed data
- No external API dependencies

## Future Enhancements

- Database integration for data persistence
- User authentication and multi-user support
- Real-time dashboard updates
- Advanced statistical modeling
- API endpoints for external integrations
- Automated report scheduling
- Custom visualization themes
- Integration with marketing platforms