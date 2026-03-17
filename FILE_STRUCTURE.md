# Project File Structure

## Directory Tree

```
customer/
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
├── IMPLEMENTATION_GUIDE.md      # Feature implementation details
├── UI_VISUAL_GUIDE.md          # User interface design guide
├── FILE_STRUCTURE.md           # This file
├── load-data.py                # Data loading utility
│
└── customer_segmentation_app/
    ├── app.py                   # Main Flask application
    ├── data.csv                 # Sample customer dataset
    ├── realistic_customers.csv  # Alternative sample data
    ├── sample_customers.csv     # Basic sample data
    │
    ├── templates/
    │   ├── index.html           # Landing page template
    │   ├── result.html          # Results dashboard template
    │   └── style.css            # CSS styles
    │
    └── static/
        ├── style.css            # CSS styles
        ├── scatter.png          # PCA visualization
        ├── pie.png              # Segment distribution chart
        ├── rfm_heatmap.png      # RFM analysis heatmap
        ├── clv_histogram.png    # CLV distribution histogram
        ├── top_clv_customers.png # Top CLV customers chart
        └── churn_bar.png        # Churn risk analysis chart
```

## File Descriptions

### Root Directory

**README.md**
- Main project documentation
- Installation and usage instructions
- Feature overview and technical details

**requirements.txt**
- Python package dependencies
- Version specifications for all libraries

**IMPLEMENTATION_GUIDE.md**
- Technical implementation details
- Function descriptions and data flow
- Development and deployment notes

**UI_VISUAL_GUIDE.md**
- User interface design system
- Visual design principles
- Component specifications

**FILE_STRUCTURE.md**
- Project organization guide
- File and directory descriptions

**load-data.py**
- Data loading and preprocessing utilities
- Helper functions for data manipulation

### Application Directory

**app.py**
- Main Flask web application
- Route handlers and business logic
- Machine learning model implementations

**data.csv**
- Primary sample customer dataset
- Used for testing and demonstrations

**realistic_customers.csv**
- Alternative sample data with varied profiles
- Additional test scenarios

**sample_customers.csv**
- Basic customer data for simple testing
- Minimal dataset for quick validation

### Templates Directory

**index.html**
- Application landing page
- File upload interface
- View mode selection

**result.html**
- Analysis results dashboard
- Tabbed interface for different views
- Data visualization display

**style.css**
- CSS styles for templates
- Layout and visual styling

### Static Directory

**style.css**
- Main application styles
- Responsive design rules

**scatter.png**
- Generated PCA scatter plot
- 2D cluster visualization

**pie.png**
- Generated segment distribution chart
- Customer count by segment

**rfm_heatmap.png**
- Generated RFM analysis heatmap
- Metric comparison across segments

**clv_histogram.png**
- Generated CLV distribution histogram
- Customer value spread visualization

**top_clv_customers.png**
- Generated top CLV customers chart
- Highest value customer ranking

**churn_bar.png**
- Generated churn risk analysis chart
- Risk level distribution

## File Organization Principles

### Separation of Concerns
- Application logic in `app.py`
- Presentation in `templates/`
- Static assets in `static/`
- Documentation in root directory

### Naming Conventions
- Lowercase with underscores for Python files
- Lowercase with hyphens for HTML/CSS files
- Descriptive names indicating purpose

### File Size Guidelines
- Keep individual files focused on single responsibilities
- Split large functions into smaller, testable units
- Maintain readable code structure

### Version Control
- Include all source files
- Exclude generated files and temporary data
- Document dependencies clearly