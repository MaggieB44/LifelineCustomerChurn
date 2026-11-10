"""FUTURE AI / ML INTEGRATION POINTS — implement these three functions later.

No AI or model is called by this starter. No fake predictions are generated.
"""


def get_predictions(customers):
    """FUTURE ML MODEL.

    Return a pandas DataFrame with CustomerID and churn_probability (0.0–1.0),
    and optionally top_driver, or return None while the model is disconnected.

    IMPORTANT: Do not pass the historical `Churn` label or other leaked future
    information as an input feature at inference time.
    """
    return None


def get_ai_recommendations(segment_name, segment_stats):
    """FUTURE AI AGENT.

    Return list of dicts: [{'title': '...', 'reason': '...'}, ...].
    The current UI uses explicitly labeled rule-based example suggestions.
    """
    return None


def save_action(customer_id, action, status):
    """FUTURE DATABASE WRITE.

    Persist outreach activity to database/CRM. The starter only stores actions
    temporarily in Streamlit session state.
    """
    return False
