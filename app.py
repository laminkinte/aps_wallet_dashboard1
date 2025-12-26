"""
APS Wallet - Annual Agent Performance Dashboard
Production-safe Streamlit App
"""

# =========================
# Imports
# =========================
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings("ignore")

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="APS Wallet | Agent Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Custom CSS
# =========================
def load_css():
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 700;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #374151;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #4F46E5, #7C3AED);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F3F4F6;
        border-radius: 5px 5px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4F46E5;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

load_css()

# =========================
# Utilities
# =========================
def format_number(x):
    return f"{int(x):,}"

def format_currency(x):
    return f"${x:,.2f}"

def format_percentage(x):
    return f"{x:.1f}%"

# =========================
# Data Loader
# =========================
class DataLoader:
    @staticmethod
    def load_csv(file, nrows=None):
        return pd.read_csv(file, low_memory=False, nrows=nrows)

# =========================
# Analytics Engine
# =========================
class AnalyticsEngine:
    def analyze(self, onboarding_df, transactions_df, year):
        results = {}
        
        # Process onboarding data
        onboarding_df["Registration Date"] = pd.to_datetime(
            onboarding_df["Registration Date"], errors="coerce"
        )
        
        # Process transaction data
        transactions_df["Created At"] = pd.to_datetime(
            transactions_df["Created At"], errors="coerce"
        )
        
        # Active agents & tellers
        results["total_active_agents"] = onboarding_df[
            (onboarding_df["Entity"] == "AGENT") &
            (onboarding_df["Status"] == "ACTIVE")
        ].shape[0]
        
        results["total_active_tellers"] = onboarding_df[
            (onboarding_df["Entity"].str.contains("TELLER", case=False, na=False)) &
            (onboarding_df["Status"] == "ACTIVE")
        ].shape[0]
        
        # Onboarded in selected year
        results["onboarded_year"] = onboarding_df[
            onboarding_df["Registration Date"].dt.year == year
        ].shape[0]
        
        # Agent hierarchy analysis
        active_agents = onboarding_df[
            (onboarding_df["Entity"] == "AGENT") &
            (onboarding_df["Status"] == "ACTIVE")
        ]
        results["total_active_agents"] = active_agents.shape[0]
        
        # Transactions summary
        year_tx = transactions_df[
            transactions_df["Created At"].dt.year == year
        ]
        
        results["total_transactions"] = year_tx.shape[0]
        results["total_volume"] = year_tx["Amount"].sum() if "Amount" in year_tx.columns else 0
        
        # Successful vs failed transactions
        if "Status" in year_tx.columns:
            results["successful_transactions"] = year_tx[
                year_tx["Status"].str.upper().str.contains("SUCCESS|COMPLETED", na=False)
            ].shape[0]
            results["failed_transactions"] = year_tx[
                year_tx["Status"].str.upper().str.contains("FAILED|DECLINED", na=False)
            ].shape[0]
        else:
            results["successful_transactions"] = 0
            results["failed_transactions"] = 0
        
        # Service breakdown
        if "Service Name" in year_tx.columns:
            service_summary = (
                year_tx.groupby("Service Name")["Amount"]
                .agg(["count", "sum"])
                .reset_index()
            )
            results["service_summary"] = service_summary
        else:
            results["service_summary"] = pd.DataFrame(columns=["Service Name", "count", "sum"])
        
        # Monthly trend
        year_tx["month"] = year_tx["Created At"].dt.month
        monthly = (
            year_tx.groupby("month")["Amount"]
            .agg(["count", "sum"])
            .reset_index()
        )
        monthly.columns = ["Month", "Transaction_Count", "Total_Amount"]
        
        # Add month names
        month_names = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }
        monthly["Month_Name"] = monthly["Month"].map(month_names)
        
        results["monthly_trend"] = monthly
        
        # Top performing agents
        if "User Identifier" in year_tx.columns and "Amount" in year_tx.columns:
            top_agents = (
                year_tx.groupby("User Identifier")["Amount"]
                .agg(["count", "sum"])
                .reset_index()
            )
            top_agents.columns = ["User Identifier", "Transaction_Count", "Total_Amount"]
            top_agents = top_agents.sort_values("Total_Amount", ascending=False).head(10)
            results["top_performing_agents"] = top_agents
        else:
            results["top_performing_agents"] = pd.DataFrame(
                columns=["User Identifier", "Transaction_Count", "Total_Amount"]
            )
        
        return results

# =========================
# UI Components
# =========================
def metric_card(title, value, subtitle=""):
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 1rem;
            text-align: center;">
            <div style="font-size: 0.9rem; opacity: 0.9;">{title}</div>
            <div style="font-size: 2rem; font-weight: 700;">{value}</div>
            <div style="font-size: 0.8rem;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# Sidebar
# =========================
st.sidebar.image(
    "https://img.icons8.com/color/96/wallet--v1.png",
    width=80
)

st.sidebar.markdown(
    "<h2 style='text-align:center;'>APS Wallet Dashboard</h2>",
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

st.sidebar.subheader("📁 Upload Data Files")
onboarding_file = st.sidebar.file_uploader(
    "Onboarding Data (CSV)",
    type=["csv"],
    help="Upload Onboarding.csv file"
)

transactions_file = st.sidebar.file_uploader(
    "Transaction Data (CSV)",
    type=["csv"],
    help="Upload Transaction.csv file"
)

st.sidebar.subheader("⚙️ Analysis Parameters")
analysis_year = st.sidebar.selectbox(
    "Select Year",
    [2025, 2024, 2023],
    index=0
)

min_deposits = st.sidebar.slider(
    "Minimum deposits for 'Active' status",
    min_value=1,
    max_value=100,
    value=20
)

process_btn = st.sidebar.button("🚀 Process Data", type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption(f"© {datetime.now().year} APS Wallet. All rights reserved.")

# =========================
# Session State
# =========================
if "results" not in st.session_state:
    st.session_state.results = None
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

# =========================
# Process Data
# =========================
if process_btn:
    if onboarding_file and transactions_file:
        with st.spinner("Processing data..."):
            loader = DataLoader()
            analytics = AnalyticsEngine()
            
            df_onboarding = loader.load_csv(onboarding_file)
            df_transactions = loader.load_csv(transactions_file, nrows=500_000)
            
            st.session_state.results = analytics.analyze(
                df_onboarding, df_transactions, analysis_year
            )
            st.session_state.data_loaded = True
            
        st.success("✅ Data processed successfully")
    else:
        st.warning("Please upload both CSV files")

# =========================
# Main Content
# =========================
st.markdown("<h1 class='main-header'>💰 APS WALLET - ANNUAL PERFORMANCE DASHBOARD</h1>", unsafe_allow_html=True)

if not st.session_state.data_loaded:
    # Welcome screen
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=200)
        st.markdown("""
        ### Welcome to APS Wallet Analytics
        
        To get started:
        1. Upload your data files in the sidebar
        2. Configure analysis parameters
        3. Click 'Process Data'
        
        Or use sample data to explore features.
        """)
        
        st.info("👈 Upload data files in the sidebar to begin analysis")
else:
    r = st.session_state.results
    
    # KPI Cards - First Row
    st.markdown("<h2 class='sub-header'>📊 Key Performance Indicators</h2>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        metric_card("Total Active Agents", format_number(r["total_active_agents"]))
    
    with col2:
        metric_card("Active Tellers", format_number(r["total_active_tellers"]))
    
    with col3:
        metric_card(f"{analysis_year} Onboarded", format_number(r["onboarded_year"]))
    
    with col4:
        metric_card("Transaction Volume", format_currency(r["total_volume"]))
    
    # KPI Cards - Second Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        metric_card("Total Transactions", format_number(r["total_transactions"]))
    
    with col2:
        if r["total_transactions"] > 0:
            success_rate = (r["successful_transactions"] / r["total_transactions"]) * 100
        else:
            success_rate = 0
        metric_card("Success Rate", format_percentage(success_rate))
    
    with col3:
        metric_card("Successful Tx", format_number(r["successful_transactions"]))
    
    with col4:
        metric_card("Failed Tx", format_number(r["failed_transactions"]))
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", 
        "👥 Agent Network", 
        "💰 Transactions", 
        "📅 Monthly Trends",
        "📊 Performance Matrix"
    ])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly transaction count chart
            if not r["monthly_trend"].empty:
                fig = px.bar(
                    r["monthly_trend"],
                    x='Month_Name',
                    y='Transaction_Count',
                    title='Monthly Transaction Count',
                    color='Transaction_Count',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Agent type distribution
            agent_data = pd.DataFrame({
                'Type': ['Active Agents', 'Active Tellers'],
                'Count': [r['total_active_agents'], r['total_active_tellers']]
            })
            
            fig = px.pie(
                agent_data,
                values='Count',
                names='Type',
                title='Active Agent Distribution',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("### Agent Network Overview")
        st.write(f"**Total Active Agents:** {format_number(r['total_active_agents'])}")
        st.write(f"**Total Active Tellers:** {format_number(r['total_active_tellers'])}")
        st.write(f"**New Onboardings ({analysis_year}):** {format_number(r['onboarded_year'])}")
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            # Transaction success/failure
            trans_data = {
                'Status': ['Successful', 'Failed'],
                'Count': [r['successful_transactions'], r['failed_transactions']]
            }
            df_trans = pd.DataFrame(trans_data)
            
            fig = px.pie(
                df_trans,
                values='Count',
                names='Status',
                title='Transaction Success Rate',
                hole=0.3,
                color_discrete_sequence=['#00CC96', '#EF553B']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Service breakdown
            if not r["service_summary"].empty:
                fig = px.bar(
                    r["service_summary"].head(10),
                    x="Service Name",
                    y="sum",
                    title="Top Services by Revenue",
                    color="sum",
                    color_continuous_scale="thermal"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        # Monthly trends comparison
        if not r["monthly_trend"].empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Bar(
                    x=r["monthly_trend"]['Month_Name'],
                    y=r["monthly_trend"]['Transaction_Count'],
                    name='Transaction Count',
                    marker_color='#636EFA'
                ),
                secondary_y=False
            )
            
            fig.add_trace(
                go.Scatter(
                    x=r["monthly_trend"]['Month_Name'],
                    y=r["monthly_trend"]['Total_Amount'],
                    name='Transaction Volume',
                    mode='lines+markers',
                    line=dict(color='#FFA15A', width=3)
                ),
                secondary_y=True
            )
            
            fig.update_layout(
                title='Monthly Trends: Transaction Count vs Volume',
                xaxis_title='Month',
                showlegend=True
            )
            
            fig.update_yaxes(title_text="Transaction Count", secondary_y=False)
            fig.update_yaxes(title_text="Transaction Volume ($)", secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab5:
        # Performance matrix
        st.markdown("### Top Performing Agents")
        
        if not r["top_performing_agents"].empty:
            # Display as table
            st.dataframe(
                r["top_performing_agents"].style.background_gradient(
                    subset=['Total_Amount'], 
                    cmap='YlOrRd'
                ).format({
                    'Total_Amount': '${:,.2f}',
                    'Transaction_Count': '{:,.0f}'
                }),
                use_container_width=True
            )
            
            # Performance scatter plot
            fig = px.scatter(
                r["top_performing_agents"].head(10),
                x='Transaction_Count',
                y='Total_Amount',
                size='Total_Amount',
                color='Total_Amount',
                hover_name='User Identifier',
                title='Top Performing Agents: Transactions vs Volume',
                labels={
                    'Transaction_Count': 'Number of Transactions',
                    'Total_Amount': 'Total Volume ($)'
                },
                color_continuous_scale='sunset'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No agent performance data available")
    
    # Data export section
    st.markdown("---")
    st.markdown("<h2 class='sub-header'>📥 Export Data</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Download Service Summary", use_container_width=True):
            csv = r["service_summary"].to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"aps_wallet_service_summary_{analysis_year}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("📈 Download Monthly Data", use_container_width=True):
            csv = r["monthly_trend"].to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"aps_wallet_monthly_{analysis_year}.csv",
                mime="text/csv",
                use_container_width=True
            )
