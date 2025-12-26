<<<<<<< HEAD
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import altair as alt
from datetime import datetime, timedelta
import time
import io
from utils.analyzer import AgentPerformanceAnalyzerUltraFast, AnalysisConfig
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="APS Wallet - Annual Performance Dashboard",
    page_icon="💰",
=======
"""
APS Wallet - Annual Agent Performance Dashboard
Production-safe Streamlit App
Python 3.11 compatible
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
>>>>>>> d69c7e99ef9c39de5c30cdd325ca3da41cb193c4
    layout="wide",
    initial_sidebar_state="expanded"
)

<<<<<<< HEAD
# Custom CSS
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

# Initialize session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'metrics' not in st.session_state:
    st.session_state.metrics = None

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/6676/6676796.png", width=100)
    st.title("APS Wallet Dashboard")
    st.markdown("---")
    
    # Year selection
    selected_year = st.selectbox(
        "Select Year",
        options=[2025, 2024, 2023],
        index=0
    )
    
    # File upload
    st.subheader("📁 Upload Data Files")
    
    onboarding_file = st.file_uploader(
        "Onboarding Data (CSV)",
        type=['csv'],
        help="Upload Onboarding.csv file"
    )
    
    transaction_file = st.file_uploader(
        "Transaction Data (CSV)",
        type=['csv'],
        help="Upload Transaction.csv file"
    )
    
    # Analysis parameters
    st.subheader("⚙️ Analysis Parameters")
    min_deposits = st.slider(
        "Minimum deposits for 'Active' status",
        min_value=1,
        max_value=100,
        value=20
    )
    
    # Load sample data option
    use_sample = st.checkbox("Use Sample Data", value=False)
    
    # Process button
    if st.button("🚀 Process Data", type="primary", use_container_width=True):
        if use_sample or (onboarding_file and transaction_file):
            with st.spinner("Processing data..."):
                try:
                    config = AnalysisConfig(year=selected_year, min_deposits_for_active=min_deposits)
                    analyzer = AgentPerformanceAnalyzerUltraFast(config=config)
                    
                    if use_sample:
                        # Load sample data from sample_data folder
                        import os
                        if os.path.exists("sample_data/Onboarding.csv") and os.path.exists("sample_data/Transaction.csv"):
                            analyzer.load_and_preprocess_data(
                                "sample_data/Onboarding.csv",
                                "sample_data/Transaction.csv"
                            )
                        else:
                            st.error("Sample data not found. Please upload your files.")
                            st.stop()
                    else:
                        # Save uploaded files temporarily
                        onboarding_df = pd.read_csv(onboarding_file)
                        transaction_df = pd.read_csv(transaction_file)
                        analyzer.set_data(onboarding_df, transaction_df)
                    
                    # Calculate metrics
                    metrics = analyzer.calculate_all_metrics()
                    
                    # Store in session state
                    st.session_state.analyzer = analyzer
                    st.session_state.metrics = metrics
                    st.session_state.data_loaded = True
                    
                    st.success("✅ Data processed successfully!")
                    
                except Exception as e:
                    st.error(f"Error processing data: {str(e)}")
        else:
            st.warning("Please upload files or select 'Use Sample Data'")
    
    st.markdown("---")
    st.caption(f"© {datetime.now().year} APS Wallet. All rights reserved.")

# Main content
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
        
        # Quick stats placeholder
        st.info("👈 Upload data files in the sidebar to begin analysis")
else:
    # Display metrics
    metrics = st.session_state.metrics
    analyzer = st.session_state.analyzer
    
    # KPI Cards
    st.markdown("<h2 class='sub-header'>📊 Key Performance Indicators</h2>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Active Agents</div>
            <div class="metric-value">{metrics['total_active_agents']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Tellers</div>
            <div class="metric-value">{metrics['total_active_tellers']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">2025 Onboarded</div>
            <div class="metric-value">{metrics['onboarded_total']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Transaction Volume</div>
            <div class="metric-value">${metrics['transaction_volume']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Second row of KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Users</div>
            <div class="metric-value">{metrics['active_users_overall']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        success_rate = (metrics['successful_transactions'] / 
                       (metrics['successful_transactions'] + metrics['failed_transactions']) * 100 
                       if (metrics['successful_transactions'] + metrics['failed_transactions']) > 0 else 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Success Rate</div>
            <div class="metric-value">{success_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        agents_with_tellers_pct = (metrics['agents_with_tellers'] / metrics['total_active_agents'] * 100 
                                  if metrics['total_active_agents'] > 0 else 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Agents with Tellers</div>
            <div class="metric-value">{agents_with_tellers_pct:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        growth_rate = (metrics['onboarded_total'] / metrics['total_active_agents'] * 100 
                      if metrics['total_active_agents'] > 0 else 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Growth Rate</div>
            <div class="metric-value">{growth_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
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
            # Monthly active users chart
            monthly_df = analyzer.get_monthly_dataframe()
            fig = px.bar(
                monthly_df,
                x='Month',
                y='Active_Users',
                title='Monthly Active Users',
                color='Active_Users',
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Onboarding pie chart
            fig = px.pie(
                values=[
                    metrics['onboarded_agents'],
                    metrics['onboarded_tellers']
                ],
                names=['Agents', 'Tellers'],
                title='2025 Onboarding Distribution',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Agent hierarchy visualization
            hierarchy_data = {
                'Type': ['Agents with Tellers', 'Agents without Tellers', 'Active Tellers'],
                'Count': [
                    metrics['agents_with_tellers'],
                    metrics['agents_without_tellers'],
                    metrics['total_active_tellers']
                ]
            }
            df_hierarchy = pd.DataFrame(hierarchy_data)
            
            fig = px.treemap(
                df_hierarchy,
                path=['Type'],
                values='Count',
                title='Agent Network Hierarchy',
                color='Count',
                color_continuous_scale='RdBu'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Agent status distribution
            if analyzer.onboarding_df is not None:
                status_counts = analyzer.onboarding_df['Status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                
                fig = px.bar(
                    status_counts.head(10),
                    x='Status',
                    y='Count',
                    title='Agent Status Distribution',
                    color='Count',
                    color_continuous_scale='thermal'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            # Transaction success/failure
            trans_data = {
                'Status': ['Successful', 'Failed'],
                'Count': [metrics['successful_transactions'], metrics['failed_transactions']]
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
            # Deposit pattern
            if hasattr(analyzer, 'deposit_df') and not analyzer.deposit_df.empty:
                if 'Hour' in analyzer.deposit_df.columns:
                    hour_counts = analyzer.deposit_df['Hour'].value_counts().sort_index().reset_index()
                    hour_counts.columns = ['Hour', 'Count']
                    
                    fig = px.line(
                        hour_counts,
                        x='Hour',
                        y='Count',
                        title='Hourly Deposit Pattern',
                        markers=True
                    )
                    fig.update_traces(line_color='#FFA15A')
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        # Monthly trends comparison
        monthly_df = analyzer.get_monthly_dataframe()
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                x=monthly_df['Month'],
                y=monthly_df['Active_Users'],
                name='Active Users',
                marker_color='#636EFA'
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=monthly_df['Month'],
                y=monthly_df['Deposit_Count'],
                name='Deposits',
                mode='lines+markers',
                line=dict(color='#FFA15A', width=3)
            ),
            secondary_y=True
        )
        
        fig.update_layout(
            title='Monthly Trends: Active Users vs Deposits',
            xaxis_title='Month',
            showlegend=True
        )
        
        fig.update_yaxes(title_text="Active Users", secondary_y=False)
        fig.update_yaxes(title_text="Deposit Count", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab5:
        # Performance matrix
        st.markdown("### Agent Performance Ranking")
        
        if metrics['top_performing_agents']:
            top_agents_df = pd.DataFrame(metrics['top_performing_agents'])
            
            # Display as table
            st.dataframe(
                top_agents_df.style.background_gradient(
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
                top_agents_df.head(20),
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
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Download Summary Report", use_container_width=True):
            summary_df = analyzer.get_summary_dataframe()
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"aps_wallet_summary_{selected_year}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("📈 Download Monthly Data", use_container_width=True):
            monthly_df = analyzer.get_monthly_dataframe()
            csv = monthly_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"aps_wallet_monthly_{selected_year}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        if st.button("💾 Full Data Export", use_container_width=True):
            raw_data = analyzer.get_raw_data_for_export()
            
            # Create Excel writer
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for sheet_name, df in raw_data.items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
            
            output.seek(0)
            st.download_button(
                label="Download Excel",
                data=output,
                file_name=f"aps_wallet_full_export_{selected_year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
=======
# =========================
# Utilities
# =========================
def format_number(x):
    return f"{int(x):,}"

def format_currency(x):
    return f"GMD {x:,.2f}"

def format_percentage(x):
    return f"{x:.2f}%"

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

        onboarding_df["Registration Date"] = pd.to_datetime(
            onboarding_df["Registration Date"], errors="coerce"
        )

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

        # Transactions summary
        year_tx = transactions_df[
            transactions_df["Created At"].dt.year == year
        ]

        results["total_transactions"] = year_tx.shape[0]
        results["total_volume"] = year_tx["Amount"].sum()

        # Service breakdown
        service_summary = (
            year_tx.groupby("Service Name")["Amount"]
            .agg(["count", "sum"])
            .reset_index()
        )

        results["service_summary"] = service_summary

        # Monthly trend
        year_tx["month"] = year_tx["Created At"].dt.month
        monthly = (
            year_tx.groupby("month")["Amount"]
            .sum()
            .reset_index()
        )

        results["monthly_trend"] = monthly

        return results

# =========================
# UI Components
# =========================
def metric_card(title, value, subtitle=""):
    st.markdown(
        f"""
        <div style="
            background:white;
            padding:20px;
            border-radius:12px;
            box-shadow:0 4px 14px rgba(0,0,0,0.08);
            text-align:center;">
            <h4 style="color:#1E3A8A;margin-bottom:8px;">{title}</h4>
            <h2 style="margin:0;">{value}</h2>
            <p style="color:#6B7280;margin:0;">{subtitle}</p>
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
    "<h2 style='text-align:center;'>APS Wallet</h2>",
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

onboarding_file = st.sidebar.file_uploader(
    "Upload Onboarding CSV",
    type=["csv"]
)

transactions_file = st.sidebar.file_uploader(
    "Upload Transactions CSV",
    type=["csv"]
)

analysis_year = st.sidebar.selectbox(
    "Analysis Year",
    [2023, 2024, 2025],
    index=2
)

process_btn = st.sidebar.button("🚀 Process Data")

st.sidebar.markdown("---")

st.sidebar.markdown(
    "<p style='text-align:center;font-size:12px;'>APS Wallet Analytics v2.5</p>",
    unsafe_allow_html=True
)

# =========================
# Session State
# =========================
if "results" not in st.session_state:
    st.session_state.results = None

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

        st.success("✅ Data processed successfully")
    else:
        st.warning("Please upload both CSV files")

# =========================
# Main Content
# =========================
st.markdown(
    f"""
    <h1 style="text-align:center;">
        APS Wallet Annual Report {analysis_year}
    </h1>
    <p style="text-align:center;color:#6B7280;">
        Last updated: {datetime.now().strftime('%d %B %Y')}
    </p>
    """,
    unsafe_allow_html=True
)

if st.session_state.results:
    r = st.session_state.results

    # KPIs
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card("Active Agents", format_number(r["total_active_agents"]))
    with col2:
        metric_card("Active Tellers", format_number(r["total_active_tellers"]))
    with col3:
        metric_card("Onboarded This Year", format_number(r["onboarded_year"]))
    with col4:
        metric_card("Total Transactions", format_number(r["total_transactions"]))

    st.markdown("### 💰 Transaction Volume")
    st.metric(
        "Total Volume",
        format_currency(r["total_volume"])
    )

    # Service Breakdown
    st.markdown("### 🧾 Service Breakdown")
    fig_service = px.bar(
        r["service_summary"],
        x="Service Name",
        y="sum",
        text="count",
        labels={"sum": "Total Amount"},
        title="Transaction Value by Service"
    )
    st.plotly_chart(fig_service, use_container_width=True)

    # Monthly Trend
    st.markdown("### 📅 Monthly Transaction Trend")
    fig_month = px.line(
        r["monthly_trend"],
        x="month",
        y="Amount",
        markers=True,
        title="Monthly Transaction Volume"
    )
    st.plotly_chart(fig_month, use_container_width=True)

    # Downloads
    st.markdown("### 📥 Downloads")

    csv_data = r["service_summary"].to_csv(index=False)
    st.download_button(
        "Download Service Summary (CSV)",
        data=csv_data,
        file_name="service_summary.csv",
        mime="text/csv"
    )

else:
    st.info("Upload data and click **Process Data** to begin.")
>>>>>>> d69c7e99ef9c39de5c30cdd325ca3da41cb193c4
