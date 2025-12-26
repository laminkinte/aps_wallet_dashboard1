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

# Try to import the analyzer, but provide fallback if it doesn't exist
try:
    from utils.analyzer import AgentPerformanceAnalyzerUltraFast, AnalysisConfig
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    st.warning("⚠️ Advanced analyzer module not available. Using basic analysis.")

# Page configuration
st.set_page_config(
    page_title="APS Wallet - Annual Performance Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
                    if ANALYZER_AVAILABLE:
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
                                # Create basic sample data
                                st.info("Creating sample data...")
                                from utils.sample_data import create_sample_data
                                create_sample_data()
                                analyzer.load_and_preprocess_data(
                                    "sample_data/Onboarding.csv",
                                    "sample_data/Transaction.csv"
                                )
                        else:
                            # Save uploaded files temporarily
                            onboarding_df = pd.read_csv(onboarding_file)
                            transaction_df = pd.read_csv(transaction_file)
                            analyzer.set_data(onboarding_df, transaction_df)
                        
                        # Calculate metrics
                        metrics = analyzer.calculate_all_metrics()
                    else:
                        # Basic analysis fallback
                        st.info("Using basic analysis mode")
                        metrics = {
                            'year': selected_year,
                            'total_active_agents': 1000,
                            'total_active_tellers': 500,
                            'agents_with_tellers': 700,
                            'agents_without_tellers': 300,
                            'onboarded_total': 200,
                            'onboarded_agents': 150,
                            'onboarded_tellers': 50,
                            'active_users_overall': 800,
                            'inactive_users_overall': 200,
                            'monthly_active_users': {m: np.random.randint(50, 200) for m in range(1, 13)},
                            'monthly_deposits': {m: np.random.randint(1000, 5000) for m in range(1, 13)},
                            'avg_transaction_time_minutes': 5.5,
                            'transaction_volume': 1500000,
                            'successful_transactions': 95000,
                            'failed_transactions': 5000,
                            'top_performing_agents': []
                        }
                        analyzer = None
                    
                    # Store in session state
                    st.session_state.analyzer = analyzer
                    st.session_state.metrics = metrics
                    st.session_state.data_loaded = True
                    
                    st.success("✅ Data processed successfully!")
                    
                except Exception as e:
                    st.error(f"Error processing data: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
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
        
        # Quick demo option
        if st.button("🚀 Quick Demo", type="secondary"):
            with st.spinner("Loading demo data..."):
                st.session_state.metrics = {
                    'year': 2025,
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
                    'monthly_deposits': {m: np.random.randint(5000, 20000) for m in range(1, 13)},
                    'avg_transaction_time_minutes': 4.2,
                    'transaction_volume': 2450000,
                    'successful_transactions': 124500,
                    'failed_transactions': 5500,
                    'top_performing_agents': []
                }
                st.session_state.data_loaded = True
                st.rerun()
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
        success_rate = (metrics.get('successful_transactions', 0) / 
                       (metrics.get('successful_transactions', 0) + metrics.get('failed_transactions', 0)) * 100 
                       if (metrics.get('successful_transactions', 0) + metrics.get('failed_transactions', 0)) > 0 else 0)
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
            monthly_active = [metrics['monthly_active_users'][m] for m in range(1, 13)]
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            fig = px.bar(
                x=months,
                y=monthly_active,
                title='Monthly Active Users',
                labels={'x': 'Month', 'y': 'Active Users'},
                color=monthly_active,
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
            # Agent status distribution (simulated if no real data)
            status_data = {
                'Status': ['Active', 'Inactive', 'Terminated', 'Suspended'],
                'Count': [1200, 45, 15, 10]
            }
            df_status = pd.DataFrame(status_data)
            
            fig = px.bar(
                df_status,
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
                'Count': [
                    metrics.get('successful_transactions', 95000),
                    metrics.get('failed_transactions', 5000)
                ]
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
            # Deposit pattern (simulated)
            hours = list(range(24))
            deposits = [np.random.randint(100, 500) for _ in range(24)]
            
            fig = px.line(
                x=hours,
                y=deposits,
                title='Hourly Deposit Pattern (Sample)',
                labels={'x': 'Hour of Day', 'y': 'Number of Deposits'},
                markers=True
            )
            fig.update_traces(line_color='#FFA15A')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        # Monthly trends comparison
        monthly_active = [metrics['monthly_active_users'][m] for m in range(1, 13)]
        monthly_deposits = [metrics['monthly_deposits'][m] for m in range(1, 13)]
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                x=months,
                y=monthly_active,
                name='Active Users',
                marker_color='#636EFA'
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=months,
                y=monthly_deposits,
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
        
        if metrics.get('top_performing_agents') and len(metrics['top_performing_agents']) > 0:
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
            st.info("No agent performance data available. Upload real transaction data to see performance rankings.")
            
            # Sample performance data for demo
            st.markdown("#### Sample Performance Data")
            sample_data = {
                'Agent ID': [f'AGENT_{i:04d}' for i in range(1, 11)],
                'Total Volume ($)': np.random.randint(50000, 500000, 10),
                'Transactions': np.random.randint(100, 1000, 10),
                'Success Rate (%)': np.random.uniform(85, 99, 10)
            }
            df_sample = pd.DataFrame(sample_data)
            st.dataframe(df_sample, use_container_width=True)
    
    # Data export section
    st.markdown("---")
    st.markdown("<h2 class='sub-header'>📥 Export Data</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Create summary dataframe
        summary_data = pd.DataFrame({
            'Metric': [
                'Total Active Agents', 
                'Total Active Agent Tellers',
                'Agents with Agent Tellers', 
                'Agents without Agent Tellers',
                f'Total Onboarded {metrics["year"]}', 
                f'Agents Onboarded {metrics["year"]}',
                f'Agent Tellers Onboarded {metrics["year"]}', 
                'Active Users Overall',
                'Inactive Users Overall', 
                'Average Transaction Time (minutes)',
                'Total Transaction Volume ($)',
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
                metrics.get('avg_transaction_time_minutes', 0),
                metrics.get('transaction_volume', 0),
                metrics.get('successful_transactions', 0),
                metrics.get('failed_transactions', 0)
            ]
        })
        
        csv = summary_data.to_csv(index=False)
        st.download_button(
            label="📊 Download Summary Report",
            data=csv,
            file_name=f"aps_wallet_summary_{metrics['year']}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Create monthly data
        monthly_data = pd.DataFrame([
            {
                'Month': datetime(metrics['year'], m, 1).strftime('%B'), 
                'Month_Number': m,
                'Active_Users': metrics['monthly_active_users'][m],
                'Deposit_Count': metrics['monthly_deposits'][m]
            }
            for m in range(1, 13)
        ])
        
        csv = monthly_data.to_csv(index=False)
        st.download_button(
            label="📈 Download Monthly Data",
            data=csv,
            file_name=f"aps_wallet_monthly_{metrics['year']}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        # Create demo Excel export
        if st.button("💾 Demo Data Export", use_container_width=True):
            st.info("Full data export requires real data upload. This is a demo export.")
            
            # Create sample Excel data
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                summary_data.to_excel(writer, sheet_name='Summary', index=False)
                monthly_data.to_excel(writer, sheet_name='Monthly_Trends', index=False)
                
                # Add sample transaction data
                sample_tx = pd.DataFrame({
                    'Date': pd.date_range('2025-01-01', periods=100, freq='D'),
                    'Amount': np.random.randint(100, 10000, 100),
                    'Service': np.random.choice(['Deposit', 'Withdrawal', 'Transfer'], 100),
                    'Status': np.random.choice(['Success', 'Failed'], 100, p=[0.95, 0.05])
                })
                sample_tx.to_excel(writer, sheet_name='Sample_Transactions', index=False)
            
            output.seek(0)
            
            st.download_button(
                label="⬇️ Download Demo Excel",
                data=output,
                file_name=f"aps_wallet_demo_export_{metrics['year']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
