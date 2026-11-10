# LifeLine — B2C Streamlit Dashboard

An editable, data-grounded dashboard shell based on the supplied **Customer_Churn_Dataset_Expanded (1).xlsx**. It uses a slate/violet design with responsive KPI cards, a customer signal carousel, chart tabs, and searchable customer accounts.

## Run in VS Code

1. Extract this project and open the `LifeLine_B2C_Dashboard` folder in VS Code.
2. Create a virtual environment (recommended): `python -m venv .venv` and activate it.
3. Install: `pip install -r requirements.txt`
4. Start: `streamlit run app.py`

The dataset is already included under `data/customer_churn.xlsx`.

## Integrate your models later

Edit **`integrations.py`** (and not the main dashboard layout):

- `get_predictions(customers)` → `None`, or DataFrame with `CustomerID`, `churn_probability` (0–1). Never use the actual `Churn` label as an inference feature.
- `get_ai_recommendations(segment_name, segment_stats)` → `None`, or list of `{'title': ..., 'reason': ...}` actions.
- `save_action(customer_id, action, status)` → `False` or your database write. *Currently the carousel saves a segment-level action and passes the segment name as the first argument; adapt this if you implement per-customer outreach.*

When predictions are integrated, the Accounts table gains a prediction column and is ordered by it. A future iteration can replace the historical segment metrics with actual model-scored estimates and individual SHAP explanations.

## What is and is not real

- Dataset: **10,500 customers**, **1,286 recorded churn cases** (12.2%).
- Supported fields: CustomerID, Age, Gender, Region, ContractType, MonthlyCharges, SignupDate, AgeMissing, AvgCallMinutes, AvgDataUsageGB, AvgSMS, TotalComplaints, MonthsOfData, Churn.
- Four homepage KPIs are computed directly from the workbook, not invented. The fourth KPI sums monthly charges among customers marked churned; it is **not** a forecast of future revenue loss.
- Five **overlapping** customer groups use quartile cutoffs or Monthly contract type. They are descriptive cohorts, **not verified causes** or SHAP attributions.
- The churn ring shows the **observed historical churn rate** of the selected group, **not** prediction probability.
- Suggested actions are labeled rule-based examples until an AI agent is connected.
- No invented time trends or 'past 30 days' comparisons: the dataset is customer-level and does not provide repeated daily observations.
- The workflow is a UI starter, not yet a production CRM.

## Files

```
app.py                       Streamlit UI, filtering, charts, styles
integrations.py              <-- ML MODEL / AI AGENT / DATABASE hooks
.streamlit/config.toml       Native Streamlit theme
data/customer_churn.xlsx     Uploaded dataset
requirements.txt             Dependencies
README.md                    Instructions
```
# LifelineCustomerChurn
