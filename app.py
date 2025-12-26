import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="APS Wallet - Annual Performance Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1E3A8A;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: 700;
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
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
    selected_year = st.selectbox("Select Year", [2025, 2024, 2023], index=0)
    
    # File upload
    st.subheader("📁 Upload Data Files")
    uploaded_onboarding = st.file_uploader("Onboarding Data (CSV)", type=['csv'])
    uploaded_transactions = st.file_uploader("Transaction Data (CSV)", type=['csv'])
    
    # Demo data option
    use_demo = st.checkbox("Use Demo Data", value=True)
    
    if st.button("🚀 Process Data", type="primary", use_container_width=True):
        with st.spinner("Processing data..."):
            # Generate demo metrics
            demo_metrics = {
                'year': selected_year,
                'total_active_agents': 1245,
                'total_active_tellers': 876,
                'agents_with_tellers': 890,
                'agents_without_tellers': 355,
                'onboarded_total': 342,
                'onboarded_agents': 245,
                'onboarded_tellers': 97,
                'active_users_overall': 1123,
                'inactive_users_overall': 345,
                'monthly_active_users': {m: np.random.randint(200, 800) for m in range(1, 13)},
                'transaction_volume': 2450000,
                'successful_transactions': 124500,
                'failed_transactions': 5500,
            }
            
            st.session_state.metrics = demo_metrics
            st.session_state.data_loaded = True
            st.success("✅ Data processed successfully!")

# Main content
st.markdown("<h1 class='main-header'>💰 APS WALLET - ANNUAL PERFORMANCE DASHBOARD</h1>", unsafe_allow_html=True)

if not st.session_state.data_loaded:
    # Welcome screen
    st.info("👈 Upload data files or select 'Use Demo Data' in the sidebar to begin analysis")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=200)
        st.markdown("""
        ### Welcome to APS Wallet Analytics
        
        To get started:
        1. Upload your data files in the sidebar
        2. Or use demo data
        3. Click 'Process Data'
        """)
else:
    # Display metrics
    metrics = st.session_state.metrics
    
    # KPI Cards
    st.markdown("## 📊 Key Performance Indicators")
    
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
            <div class="metric-label">{metrics['year']} Onboarded</div>
            <div class="metric-value">{metrics['onboarded_total']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        success_rate = (metrics['successful_transactions'] / 
                       (metrics['successful_transactions'] + metrics['failed_transactions']) * 100 
                       if (metrics['successful_transactions'] + metrics['failed_transactions']) > 0 else 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Success Rate</div>
            <div class="metric-value">{success_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    st.markdown("## 📈 Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Monthly active users chart
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        active_users = [metrics['monthly_active_users'][m] for m in range(1, 13)]
        
        fig = px.bar(
            x=months,
            y=active_users,
            title='Monthly Active Users',
            labels={'x': 'Month', 'y': 'Active Users'},
            color=active_users,
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
            title=f'{metrics["year"]} Onboarding Distribution',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.markdown("## 📋 Monthly Data")
    monthly_data = pd.DataFrame({
        'Month': months,
        'Active Users': active_users,
        'Growth %': [round((active_users[i] - active_users[i-1])/active_users[i-1]*100 if i>0 else 0, 1) for i in range(12)]
    })
    st.dataframe(monthly_data, use_container_width=True)
    
    # Export
    st.markdown("## 📥 Export Data")
    csv = monthly_data.to_csv(index=False)
    st.download_button(
        label="Download Monthly Data (CSV)",
        data=csv,
        file_name=f"aps_wallet_data_{metrics['year']}.csv",
        mime="text/csv"
    )
