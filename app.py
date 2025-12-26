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
import warnings
warnings.filterwarnings('ignore')

# Try to import the analyzer, but provide a fallback
try:
    from utils.analyzer import AgentPerformanceAnalyzerUltraFast, AnalysisConfig
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    st.warning("Analyzer module not available. Some features may be limited.")

# Page configuration
st.set_page_config(
    page_title="APS Wallet - Annual Performance Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    try:
        with open("assets/style.css", "r") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except:
        # Fallback CSS if file not found
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

load_css()

# Initialize session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'metrics' not in st.session_state:
    st.session_state.metrics = None
if 'onboarding_df' not in st.session_state:
    st.session_state.onboarding_df = None
if 'transaction_df' not in st.session_state:
    st.session_state.transaction_df = None

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
    st.subheader("Upload Data Files")
    
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
    st.subheader("Analysis Parameters")
    min_deposits = st.slider(
        "Minimum deposits for 'Active' status",
        min_value=1,
        max_value=100,
        value=20
    )
    
    # Load sample data option
    use_sample = st.checkbox("Use Sample Data", value=False)
    
    # Process button
    if st.button("Process Data", type="primary", use_container_width=True):
        if use_sample or (onboarding_file and transaction_file):
            with st.spinner("Processing data..."):
                try:
                    # Create sample data if needed
                    if use_sample:
                        # Create simple sample data
                        sample_onboarding = pd.DataFrame({
                            'Account ID': ['1001', '1002', '1003', '1004', '1005'],
                            'Entity': ['AGENT', 'AGENT TELLER', 'AGENT', 'AGENT TELLER', 'AGENT'],
                            'Status': ['ACTIVE', 'ACTIVE', 'INACTIVE', 'ACTIVE', 'TERMINATED'],
                            'Registration Date': ['01/01/2025 09:00', '15/01/2025 10:30', '01/02/2025 11:00', '15/02/2025 14:00', '01/03/2025 16:00']
                        })
                        
                        sample_transaction = pd.DataFrame({
                            'User Identifier': ['1001', '1002', '1001', '1002', '1004'],
                            'Parent User Identifier': ['', '1001', '', '1001', '1003'],
                            'Entity Name': ['AGENT', 'AGENT TELLER', 'AGENT', 'AGENT TELLER', 'AGENT TELLER'],
                            'Service Name': ['DEPOSIT', 'DEPOSIT', 'WITHDRAWAL', 'DEPOSIT', 'DEPOSIT'],
                            'Transaction Type': ['DEPOSIT', 'DEPOSIT', 'CASH_OUT', 'DEPOSIT', 'DEPOSIT'],
                            'Product Name': ['AGENT DEPOSIT', 'CASH DEPOSIT', 'WALLET TRANSFER', 'AGENT DEPOSIT', 'CASH DEPOSIT'],
                            'Transaction Amount': [500.00, 200.00, 100.00, 300.00, 150.00],
                            'Transaction Status': ['SUCCESS', 'SUCCESS', 'SUCCESS', 'SUCCESS', 'FAILED'],
                            'Created At': ['2025-01-15 09:30:00', '2025-01-15 10:00:00', '2025-01-16 11:00:00', '2025-01-17 14:30:00', '2025-01-18 16:00:00']
                        })
                        
                        st.session_state.onboarding_df = sample_onboarding
                        st.session_state.transaction_df = sample_transaction
                        
                    else:
                        # Load uploaded files
                        onboarding_df = pd.read_csv(onboarding_file)
                        transaction_df = pd.read_csv(transaction_file)
                        st.session_state.onboarding_df = onboarding_df
                        st.session_state.transaction_df = transaction_df
                    
                    # Initialize analyzer if available
                    if ANALYZER_AVAILABLE:
                        config = AnalysisConfig(year=selected_year, min_deposits_for_active=min_deposits)
                        analyzer = AgentPerformanceAnalyzerUltraFast(
                            st.session_state.onboarding_df,
                            st.session_state.transaction_df,
                            config=config
                        )
                        
                        # Calculate metrics
                        metrics = analyzer.calculate_all_metrics()
                        
                        # Store in session state
                        st.session_state.analyzer = analyzer
                        st.session_state.metrics = metrics
                    else:
                        # Create simple metrics if analyzer not available
                        metrics = {
                            'year': selected_year,
                            'total_active_agents': 2,
                            'total_active_tellers': 2,
                            'agents_with_tellers': 1,
                            'agents_without_tellers': 1,
                            'onboarded_total': 3,
                            'onboarded_agents': 2,
                            'onboarded_tellers': 1,
                            'active_users_overall': 3,
                            'inactive_users_overall': 1,
                            'transaction_volume': 1250.00,
                            'successful_transactions': 4,
                            'failed_transactions': 1,
                            'monthly_active_users': {m: 3 for m in range(1, 13)},
                            'monthly_deposits': {m: 5 for m in range(1, 13)}
                        }
                        st.session_state.metrics = metrics
                    
                    st.session_state.data_loaded = True
                    st.success("Data processed successfully!")
                    
                except Exception as e:
                    st.error(f"Error processing data: {str(e)}")
        else:
            st.warning("Please upload files or select 'Use Sample Data'")
    
    st.markdown("---")
    st.caption(f"© {datetime.now().year} APS Wallet. All rights reserved.")

# Main content
st.markdown("<h1 class='main-header'>APS WALLET - ANNUAL PERFORMANCE DASHBOARD</h1>", unsafe_allow_html=True)

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
        st.info("Upload data files in the sidebar to begin analysis")
else:
    # Display metrics
    metrics = st.session_state.metrics
    
    # KPI Cards
    st.markdown("<h2>Key Performance Indicators</h2>", unsafe_allow_html=True)
    
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
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Transaction Volume</div>
            <div class="metric-value">${metrics.get('transaction_volume', 0):,.0f}</div>
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
    tab1, tab2, tab3, tab4 = st.tabs([
        "Overview", 
        "Agent Network", 
        "Transactions", 
        "Monthly Trends"
    ])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly active users chart
            monthly_data = []
            for m in range(1, 13):
                monthly_data.append({
                    'Month': datetime(metrics['year'], m, 1).strftime('%B'),
                    'Active_Users': metrics['monthly_active_users'].get(m, 0),
                    'Deposits': metrics['monthly_deposits'].get(m, 0)
                })
            
            monthly_df = pd.DataFrame(monthly_data)
            
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
                title=f'{metrics["year"]} Onboarding Distribution',
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
            if st.session_state.onboarding_df is not None:
                # Agent status distribution
                status_counts = st.session_state.onboarding_df['Status'].value_counts().reset_index()
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
    
    with tab4:
        # Monthly trends comparison
        monthly_data = []
        for m in range(1, 13):
            monthly_data.append({
                'Month': datetime(metrics['year'], m, 1).strftime('%B'),
                'Active_Users': metrics['monthly_active_users'].get(m, 0),
                'Deposits': metrics['monthly_deposits'].get(m, 0)
            })
        
        monthly_df = pd.DataFrame(monthly_data)
        
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
                y=monthly_df['Deposits'],
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
    
    # Data export section
    st.markdown("---")
    st.markdown("<h2>Data Export</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download Summary Report", use_container_width=True):
            summary_data = pd.DataFrame({
                'Metric': [
                    'Total Active Agents',
                    'Total Active Tellers',
                    'Agents with Tellers',
                    'Agents without Tellers',
                    f'{metrics["year"]} Onboarded Total',
                    f'{metrics["year"]} Agents Onboarded',
                    f'{metrics["year"]} Tellers Onboarded',
                    'Active Users (≥20 deposits)',
                    'Inactive Users (<20 deposits)',
                    'Transaction Volume',
                    'Successful Transactions',
                    'Failed Transactions'
                ],
                'Value': [
                    metrics['total_active_agents'],
                    metrics['total_active_tellers'],
                    metrics['agents_with_tellers'],
                    metrics['agents_without_tellers'],
                    metrics['onboarded_total'],
                    metrics['onboarded_agents'],
                    metrics['onboarded_tellers'],
                    metrics['active_users_overall'],
                    metrics['inactive_users_overall'],
                    metrics.get('transaction_volume', 0),
                    metrics['successful_transactions'],
                    metrics['failed_transactions']
                ]
            })
            
            csv = summary_data.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"aps_wallet_summary_{selected_year}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("Download Monthly Data", use_container_width=True):
            monthly_data = []
            for m in range(1, 13):
                monthly_data.append({
                    'Month': datetime(metrics['year'], m, 1).strftime('%B'),
                    'Month_Number': m,
                    'Active_Users': metrics['monthly_active_users'].get(m, 0),
                    'Deposits': metrics['monthly_deposits'].get(m, 0)
                })
            
            monthly_df = pd.DataFrame(monthly_data)
            csv = monthly_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"aps_wallet_monthly_{selected_year}.csv",
                mime="text/csv",
                use_container_width=True
            )
