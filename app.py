"""LifeLine B2C — data-grounded Streamlit starter dashboard.

START HERE: integrations.py contains clearly marked AI, ML, and database hooks.
This dashboard NEVER presents historical churn as a predicted probability.
"""
from pathlib import Path
from html import escape
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from integrations import get_predictions, get_ai_recommendations, save_action

st.set_page_config(page_title="LifeLine | Action Center", page_icon="💜", layout="wide", initial_sidebar_state="expanded")

ROOT = Path(__file__).parent
DATA_PATH = ROOT / "data" / "customer_churn.xlsx"
C = {"bg":"#101429","sidebar":"#12162D","panel":"#1A2240","inset":"#141B34","line":"#303958","text":"#F4F3FB","muted":"#ABB3D1","violet":"#9B7CF5","green":"#54D2AF","amber":"#F3BD63","red":"#FA6B83","blue":"#77B3F6"}

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*='css'], [data-testid='stAppViewContainer'] {font-family:Inter,system-ui,sans-serif;}
.stApp { background:#101429; }
[data-testid='stSidebar']{background:#12162D;border-right:1px solid #303958;}
[data-testid='stSidebar'] .stRadio label{font-weight:500;}
.block-container{padding:2.0rem 2.0rem 5rem;max-width:1540px;}
h1,h2,h3{letter-spacing:-.025em;}
h1{font-size:2rem!important;}
h2{font-size:1.3rem!important;}
[data-testid='stHorizontalBlock']{align-items:stretch;}
[data-testid='stHorizontalBlock'] > div{min-width:0;}
[data-testid='stVerticalBlockBorderWrapper']{border-color:#303958!important;border-radius:16px!important;background:#1A2240!important;}
[data-testid='stMetric']{min-width:0;}
[data-testid='stMetricValue']{font-size:clamp(1.45rem,2.3vw,2.3rem)!important;overflow-wrap:anywhere;line-height:1.15!important;}
[data-testid='stMetricLabel']{font-size:.88rem!important;}
[data-testid='stDataFrame']{border:1px solid #303958;border-radius:10px;overflow:hidden;}
.stButton button{border-radius:9px;min-height:39px;}
.stTabs [data-baseweb='tab-list']{gap:14px;}
.stTabs [data-baseweb='tab']{font-weight:600;}
.ll-kpi{height:154px;box-sizing:border-box;background:#1A2240;border:1px solid #303958;border-radius:15px;padding:22px 22px;display:flex;flex-direction:column;justify-content:space-between;min-width:0;}
.ll-kpi-top{display:flex;gap:11px;align-items:center;min-width:0;}
.ll-icon{background:#352958;color:#BEA6FF;width:34px;height:34px;border-radius:11px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:18px;}
.ll-kpi-name{font-size:13px;color:#C5C9DE;font-weight:600;line-height:1.25;min-width:0;}
.ll-kpi-num{font-size:clamp(21px,2.3vw,35px);font-weight:800;line-height:1.05;letter-spacing:-.04em;white-space:nowrap;color:#F4F3FB;}
.ll-kpi-note{font-size:11px;color:#ADB5D1;line-height:1.35;}
.ll-panel-head{font-size:19px;font-weight:750;letter-spacing:-.02em;color:#F4F3FB;}
.ll-sub{font-size:12px;color:#AEB8D4;line-height:1.5;}
.ll-stat{background:#141B34;border:1px solid #303958;border-radius:12px;padding:14px 16px;margin:10px 0;min-width:0;}
.ll-small-label{font-size:12px;color:#AEB8D4;}
.ll-stat-number{font-size:clamp(19px,2.2vw,29px);font-weight:750;letter-spacing:-.03em;overflow-wrap:anywhere;}
.ll-factor{padding:9px 12px;background:#202945;border-radius:9px;border:1px solid #303958;font-size:12px;color:#D8DDF0;margin-bottom:8px;line-height:1.45;}
.ll-action{background:#202945;border:1px solid #394364;border-radius:12px;padding:15px 16px;margin:0 0 11px;}
.ll-action-title{font-weight:700;font-size:13px;margin-bottom:5px;}
.ll-action-body{font-size:12px;color:#B9C1D9;line-height:1.55;}
.ll-banner{border:1px solid #594581;border-radius:12px;background:#2B2448;padding:13px 17px;color:#E9E2FA;font-size:12px;line-height:1.55;}
.ll-spacer{height:24px;}
@media(max-width:1100px){.block-container{padding-left:1.25rem;padding-right:1.25rem;}.ll-kpi{padding:14px;height:136px;}.ll-kpi-num{font-size:clamp(19px,2vw,29px);}}
@media(max-width:680px){.ll-kpi{height:130px;}.ll-kpi-num{font-size:25px;}}
</style>""", unsafe_allow_html=True)


def h(s): return escape(str(s))

@st.cache_data(show_spinner=False)
def load_customers():
    if not DATA_PATH.exists():
        return pd.DataFrame()
    df = pd.read_excel(DATA_PATH, sheet_name="Customer Data")
    df["Churn"] = pd.to_numeric(df["Churn"], errors="coerce").fillna(0).astype(int)
    for col in ["MonthlyCharges","TotalComplaints","AvgCallMinutes","AvgDataUsageGB","AvgSMS"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["SignupDate"] = pd.to_datetime(df["SignupDate"], errors="coerce")
    return df


def segments(df):
    # Overlapping ANALYTICAL COHORTS, not verified causes of churn.
    # Quartiles are data-dependent, not ML thresholds.
    if df.empty: return {}
    return {
        "High Complaints": df["TotalComplaints"] >= df["TotalComplaints"].quantile(.75),
        "Low Data Usage": df["AvgDataUsageGB"] <= df["AvgDataUsageGB"].quantile(.25),
        "Low Call Activity": df["AvgCallMinutes"] <= df["AvgCallMinutes"].quantile(.25),
        "High Monthly Charges": df["MonthlyCharges"] >= df["MonthlyCharges"].quantile(.75),
        "Monthly Contracts": df["ContractType"].eq("Monthly"),
    }

RULE_ACTIONS = {
 "High Complaints": [("Review complaint history","Contact customers with unresolved service issues and determine what resolution they need."),("Prioritize follow-up","Route repeated complaints to customer support for timely investigation.")],
 "Low Data Usage": [("Check plan fit","Ask whether the plan still meets customers’ needs and offer usage guidance."),("Provide onboarding help","Share relevant features and setup assistance where appropriate.")],
 "Low Call Activity": [("Understand engagement","Check whether declining call activity reflects changing customer needs."),("Review product value","Explain services or features that may be more relevant to the customer.")],
 "High Monthly Charges": [("Review affordability","Check whether available plans better match customer usage and budgets."),("Explain plan value","Clarify plan benefits and billing before suggesting a change.")],
 "Monthly Contracts": [("Discuss plan options","Offer an optional review of available contract terms without assuming a switch is beneficial."),("Proactive satisfaction check","Ask about service quality before the next billing cycle.")],
}


def fmt_money(amount): return f"${amount:,.0f}"

def card(label, val, icon, foot):
    st.markdown(f'<div class="ll-kpi"><div class="ll-kpi-top"><div class="ll-icon">{h(icon)}</div><div class="ll-kpi-name">{h(label)}</div></div><div class="ll-kpi-num">{h(val)}</div><div class="ll-kpi-note">{h(foot)}</div></div>',unsafe_allow_html=True)

def chart_layout(fig, height=290):
    fig.update_layout(height=height,margin=dict(l=10,r=10,t=18,b=12),paper_bgcolor=C["panel"],plot_bgcolor=C["panel"],font=dict(family="Inter, sans-serif",color=C["muted"],size=12),showlegend=False)
    fig.update_xaxes(showgrid=False,zeroline=False,linecolor=C["line"])
    fig.update_yaxes(gridcolor="#303958",zeroline=False)
    return fig

def group_summary(df,mask):
    sub=df.loc[mask]
    churned=sub.loc[sub.Churn.eq(1)]
    return {"customers":len(sub),"churned":len(churned),"churn_rate":len(churned)/len(sub) if len(sub) else 0,
      "monthly_charges_churned":churned.MonthlyCharges.sum(),"complaints":sub.TotalComplaints.mean(),"usage":sub.AvgDataUsageGB.mean(),"calls":sub.AvgCallMinutes.mean(),"charges":sub.MonthlyCharges.mean()}


def sidebar():
    with st.sidebar:
        st.markdown('<div style="font-size:26px;font-weight:800;letter-spacing:-.04em;color:#EEEAFE;margin:5px 0 26px"><span style="color:#9B7CF5">∿</span> LifeLine</div>',unsafe_allow_html=True)
        p=st.radio("Navigation",["Action Center","Customer Segments","Predictive Insights","Accounts","Model + Settings"],label_visibility="collapsed",key="nav")
        st.markdown('<div style="height:22vh"></div><div style="font-size:12px;color:#AEB8D4">Predict. Understand. Retain.</div>',unsafe_allow_html=True)
        return p


def filter_df(df, key):
    with st.container(border=True):
        a,b,c,d=st.columns([1.2,1.2,1.2,1.6],gap="small")
        with a: contract=st.selectbox("Contract",["All"]+sorted(df.ContractType.dropna().unique().tolist()),key=f"{key}_contract")
        with b: region=st.selectbox("Region",["All"]+sorted(df.Region.dropna().unique().tolist()),key=f"{key}_region")
        with c: churn=st.selectbox("Recorded churn",["All","Churned","Retained"],key=f"{key}_churn")
        with d: search=st.text_input("Customer ID",placeholder="Search ID...",key=f"{key}_search")
        out=df.copy()
        if contract!="All":out=out[out.ContractType.eq(contract)]
        if region!="All":out=out[out.Region.eq(region)]
        if churn!="All":out=out[out.Churn.eq(int(churn=="Churned"))]
        if search:out=out[out.CustomerID.astype(str).str.contains(search,case=False,regex=False)]
    return out


def show_accounts(df, preds=None, key="accounts"):
    out=filter_df(df,key)
    if out.empty: st.info("No customers match the selected filters.");return
    if preds is not None:
        out=out.merge(preds[["CustomerID","churn_probability"]],on="CustomerID",how="left")
        out=out.sort_values("churn_probability",ascending=False)
        names={"churn_probability":"Predicted churn probability"}
        cols=["CustomerID","ContractType","Region","TotalComplaints","AvgDataUsageGB","MonthlyCharges","churn_probability","Churn"]
    else:
        # Review order is not a prediction. Relative complaint levels prioritize manual review.
        out=out.sort_values(["TotalComplaints","MonthlyCharges"],ascending=False)
        names={}
        cols=["CustomerID","ContractType","Region","TotalComplaints","AvgDataUsageGB","MonthlyCharges","Churn"]
    table=out[cols].rename(columns={"CustomerID":"Customer ID","ContractType":"Contract","Region":"Region","TotalComplaints":"Complaints","AvgDataUsageGB":"Avg. data (GB)","MonthlyCharges":"Monthly charge","Churn":"Recorded churn",**names})
    st.caption(f"{len(out):,} customers · " + ("Ordered by predicted churn probability" if preds is not None else "Ordered by complaints, then monthly charges — review heuristic only"))
    st.dataframe(table,use_container_width=True,hide_index=True,height=340,column_config={"Monthly charge":st.column_config.NumberColumn(format="$%.2f"),"Avg. data (GB)":st.column_config.NumberColumn(format="%.2f"),"Predicted churn probability":st.column_config.ProgressColumn(min_value=0,max_value=1,format="percent") } if preds is not None else {"Monthly charge":st.column_config.NumberColumn(format="$%.2f"),"Avg. data (GB)":st.column_config.NumberColumn(format="%.2f")})


def show_insights(df,masks):
    st.markdown('<div class="ll-panel-head">Predictive Insights</div><div class="ll-sub">Observed patterns from the customer data. Future model outputs will appear here once connected.</div>',unsafe_allow_html=True)
    t1,t2,t3=st.tabs(["Churn Overview","Revenue Exposure","Customer Signals"])
    with t1:
        ch=int(df.Churn.sum()); ret=len(df)-ch
        fig=go.Figure(go.Bar(y=["Customers"],x=[ret],name="Retained",orientation="h",marker_color=C["green"],text=[f"{ret:,} retained"],textposition="inside",textfont_color="#101429"))
        fig.add_trace(go.Bar(y=["Customers"],x=[ch],name="Churned",orientation="h",marker_color=C["red"],text=[f"{ch:,} churned"],textposition="inside"))
        fig.update_layout(barmode="stack",xaxis_title="Customers")
        st.plotly_chart(chart_layout(fig,260),use_container_width=True)
        st.caption("Actual churn labels (Churn=0 or 1), not predicted churn-risk categories.")
    with t2:
        g=df[df.Churn.eq(1)].groupby("ContractType").MonthlyCharges.sum().sort_values(ascending=False)
        fig=go.Figure(go.Bar(x=g.index,y=g.values,marker_color=[C["violet"],C["blue"],C["green"]][:len(g)],text=[fmt_money(v) for v in g],textposition="outside"))
        fig.update_layout(yaxis_title="Monthly charges ($)")
        st.plotly_chart(chart_layout(fig,280),use_container_width=True)
        st.caption("Sum of monthly charges for customers with recorded churn, by contract. Not a forecast of lost revenue.")
    with t3:
        rows=[]
        for name,mask in masks.items():
            m=group_summary(df,mask);rows.append((name,m["churn_rate"]*100,m["customers"]))
        rows.sort(key=lambda x:x[1],reverse=True)
        fig=go.Figure(go.Bar(y=[x[0] for x in rows][::-1],x=[x[1] for x in rows][::-1],orientation="h",marker_color=C["violet"],text=[f"{x[1]:.1f}% · n={x[2]:,}" for x in rows][::-1],textposition="outside"))
        fig.update_layout(xaxis_title="Observed churn rate (%)")
        st.plotly_chart(chart_layout(fig,310),use_container_width=True)
        st.caption("Cohorts overlap. These are correlations in the observed data, not validated causes or SHAP attributions.")


def segment_carousel(df,masks):
    stats={name:group_summary(df,m) for name,m in masks.items()}
    ordered=sorted(stats,key=lambda n:stats[n]["monthly_charges_churned"],reverse=True)
    if "seg_idx" not in st.session_state:st.session_state.seg_idx=0
    st.session_state.seg_idx %= len(ordered)
    a,b,c=st.columns([7.4,1.1,1.1],gap="small")
    with a:
        st.markdown('<div class="ll-panel-head">Customer Segment Preview</div><div class="ll-sub">Behavior-based customer groups, ranked by monthly charges tied to observed churn</div>',unsafe_allow_html=True)
    with b:
        if st.button("← Previous",use_container_width=True): st.session_state.seg_idx=(st.session_state.seg_idx-1)%len(ordered)
    with c:
        if st.button("Next →",use_container_width=True): st.session_state.seg_idx=(st.session_state.seg_idx+1)%len(ordered)
    name=ordered[st.session_state.seg_idx];s=stats[name]
    st.caption(f"Segment {st.session_state.seg_idx+1} of {len(ordered)}  ·  These groups can overlap")
    with st.container(border=True):
        left,right=st.columns([1,1],gap="large")
        with left:
            st.markdown(f'<div class="ll-panel-head">{h(name)}</div><div class="ll-sub">{s["customers"]:,} customers · {s["churned"]:,} with recorded churn</div>',unsafe_allow_html=True)
            k1,k2=st.columns(2)
            with k1:st.markdown(f'<div class="ll-stat"><div class="ll-small-label">Observed churn rate</div><div class="ll-stat-number">{s["churn_rate"]:.1%}</div></div>',unsafe_allow_html=True)
            with k2:st.markdown(f'<div class="ll-stat"><div class="ll-small-label">Monthly charges · churned</div><div class="ll-stat-number">{fmt_money(s["monthly_charges_churned"])}</div></div>',unsafe_allow_html=True)
            fig=go.Figure(go.Pie(values=[s["churned"],s["customers"]-s["churned"]],labels=["Churned","Retained"],hole=.74,marker_colors=[C["red"],C["green"]],textinfo="none",sort=False))
            fig.update_layout(annotations=[dict(text=f'<b>{s["churn_rate"]:.1%}</b><br>observed',x=.5,y=.5,font=dict(size=17,color=C["text"]),showarrow=False)])
            st.plotly_chart(chart_layout(fig,200),use_container_width=True,config={"displayModeBar":False})
            st.markdown('**Segment characteristics**')
            st.markdown(f'<div class="ll-factor">Average complaints: <b>{s["complaints"]:.1f}</b></div><div class="ll-factor">Average data usage: <b>{s["usage"]:.1f} GB</b></div><div class="ll-factor">Average monthly charge: <b>${s["charges"]:.2f}</b></div>',unsafe_allow_html=True)
        with right:
            st.markdown('#### Suggested actions')
            ai=get_ai_recommendations(name,s)  # << AI AGENT INTEGRATION POINT
            actions=ai if ai else [{"title":a,"reason":b} for a,b in RULE_ACTIONS[name]]
            st.caption("AI-generated" if ai else "Rule-based examples · AI agent not yet connected")
            for i,action in enumerate(actions):
                title=action["title"];reason=action["reason"]
                st.markdown(f'<div class="ll-action"><div class="ll-action-title">{h(title)}</div><div class="ll-action-body">{h(reason)}</div></div>',unsafe_allow_html=True)
                if st.button("Add to action plan",key=f"plan_{name}_{i}",use_container_width=True):
                    st.session_state.setdefault("action_plan",[]).append({"segment":name,"action":title})
                    save_action(name,title,"Planned") # << DATABASE WRITE INTEGRATION POINT
                    st.toast("Added to this session's action plan")
            st.markdown('<div class="ll-banner">Recommendations are starting points, not proven retention interventions. Verify customer needs before outreach.</div>',unsafe_allow_html=True)


def main():
    df=load_customers()
    if df.empty:st.error("Dataset missing: put Customer_Churn_Dataset_Expanded (1).xlsx at data/customer_churn.xlsx");st.stop()
    mask=segments(df)
    page=sidebar()
    # << ML MODEL INTEGRATION POINT — implement get_predictions() in integrations.py
    preds=get_predictions(df.copy())
    if preds is not None:
        if not isinstance(preds,pd.DataFrame) or not {"CustomerID","churn_probability"}.issubset(preds.columns):
            st.error("ML integration must return DataFrame with CustomerID and churn_probability.");st.stop()
        preds=preds[["CustomerID","churn_probability"]].drop_duplicates("CustomerID")
        preds["churn_probability"]=pd.to_numeric(preds["churn_probability"],errors="coerce")
        if not preds["churn_probability"].dropna().between(0,1).all():st.error("churn_probability must be between 0 and 1");st.stop()
    if page=="Action Center":
        st.title("Action Center")
        top1,top2,top3=st.columns([2.8,1.4,1],gap="medium")
        with top1:st.caption("Understand which B2C customers may need retention attention.")
        with top2:st.caption("Historical snapshot · no event-level time series")
        with top3:
            st.download_button("↓ Export customer CSV",df.to_csv(index=False).encode(),"lifeline_customers.csv","text/csv",use_container_width=True)
        st.markdown('<div class="ll-spacer"></div>',unsafe_allow_html=True)
        # Dataset values; no invented changes over time or future predictions.
        values=[("Total Customers",f"{len(df):,}","♙","Records in dataset"),("Recorded Churn",f"{int(df.Churn.sum()):,}","↗","Historical outcomes"),("Observed Churn Rate",f"{df.Churn.mean():.1%}","◈","Churned ÷ all customers"),("Churned Monthly Charges",fmt_money(df.loc[df.Churn.eq(1),"MonthlyCharges"].sum()),"$","Sum of monthly charges · not forecast")]
        cols=st.columns(4,gap="medium")
        for col,vals in zip(cols,values):
            with col:card(*vals)
        st.markdown('<div style="height:34px"></div>',unsafe_allow_html=True)
        segment_carousel(df,mask)
        st.markdown('<div style="height:34px"></div>',unsafe_allow_html=True)
        with st.container(border=True):show_insights(df,mask)
        st.markdown('<div style="height:34px"></div>',unsafe_allow_html=True)
        st.markdown('<div class="ll-panel-head">Customer Accounts</div><div class="ll-sub">Search and review individual customers. Model-based prioritization appears after integration.</div>',unsafe_allow_html=True)
        show_accounts(df,preds,key="home")
    elif page=="Customer Segments":
        st.title("Customer Segments")
        st.caption("Overlapping analytical cohorts based on available customer behavior columns.")
        rows=[]
        for name,m in mask.items():
            s=group_summary(df,m);rows.append({"Segment":name,"Customers":s["customers"],"Recorded churn":s["churned"],"Observed churn rate":round(100*s["churn_rate"],1),"Churned monthly charges ($)":round(s["monthly_charges_churned"],2)})
        st.dataframe(pd.DataFrame(rows).sort_values("Churned monthly charges ($)",ascending=False),use_container_width=True,hide_index=True)
        st.info("Segments are not mutually exclusive and do not establish causality. Quartile cutoffs adjust to the dataset.")
    elif page=="Predictive Insights":
        st.title("Predictive Insights")
        st.caption("Historical observations today. Prediction distributions, SHAP explanations, and model performance can be added later.")
        with st.container(border=True):show_insights(df,mask)
    elif page=="Accounts":
        st.title("Accounts")
        st.caption("Individual B2C customer records from the uploaded dataset.")
        show_accounts(df,preds,key="all")
    else:
        st.title("Model + Settings")
        st.markdown('<div class="ll-banner"><b>ML model: '+('Connected' if preds is not None else 'Not connected')+'</b><br>Implement <code>get_predictions(customers)</code> in <code>integrations.py</code>. Return a DataFrame with <code>CustomerID</code> and <code>churn_probability</code>.</div>',unsafe_allow_html=True)
        st.write(" ")
        st.markdown('<div class="ll-banner"><b>AI recommendations: Placeholder</b><br>Implement <code>get_ai_recommendations(segment_name, segment_stats)</code> in <code>integrations.py</code>. Until then, the carousel shows labeled rule-based examples.</div>',unsafe_allow_html=True)
        st.write(" ")
        st.markdown('<div class="ll-banner"><b>Database / CRM: Not connected</b><br>Implement <code>save_action(customer_id, action, status)</code> in <code>integrations.py</code>. Current action-plan selections are temporary and stored only in the Streamlit session.</div>',unsafe_allow_html=True)
        st.write(" ")
        plan=st.session_state.get("action_plan",[])
        st.markdown(f"**Current session action plan:** {len(plan)} item(s)")
        if plan:st.dataframe(pd.DataFrame(plan),hide_index=True,use_container_width=True)
        st.caption("The workbook does not include prediction scores, model explanations, interventions, historical daily snapshots or confirmed action outcomes.")

if __name__=="__main__":main()
