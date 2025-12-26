"""
APS Wallet - Annual Agent Performance Dashboard
Production-ready Streamlit Application
"""

# =========================
# Core Imports
# =========================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import io
import warnings
warnings.filterwarnings('ignore')

# =========================
# Page Configuration
# =========================
st.set_page_config(
    page_title="APS Wallet - Annual Performance Dashboard",
    page_icon="💰",
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
    /* Fix for sidebar spacing */
    .css-1d391kg {
        padding-top: 3.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

load_css()

# =========================
# Analytics Engine
# =========================
class AnalyticsEngine:
    def __init__(self, year=2025, min_deposits_for_active=20):
        self.year = year
        self.min_deposits = min_deposits_for_active
        self.onboarding_df = None
        self.transaction_df = None
        self.deposit_df = None
        
    def load_data(self, onboarding_file, transaction_file):
        """Load and preprocess data"""
        try:
            # Load CSV files
            self.onboarding_df = pd.read_csv(onboarding_file)
            self.transaction_df = pd.read_csv(transaction_file)
            
            # Clean column names
            self.onboarding_df.columns = self.onboarding_df.columns.str.strip()
            self.transaction_df.columns = self.transaction_df.columns.str.strip()
            
            # Convert date columns
            if 'Registration Date' in self.onboarding_df.columns:
                self.onboarding_df['Registration Date'] = pd.to_datetime(
                    self.onboarding_df['Registration Date'], errors='coerce'
                )
            
            if 'Created At' in self.transaction_df.columns:
                self.transaction_df['Created At'] = pd.to_datetime(
                    self.transaction_df['Created At'], errors='coerce'
                )
            
            # Extract year and month
            self.transaction_df['Transaction_Year'] = self.transaction_df['Created At'].dt.year
            self.transaction_df['Transaction_Month'] = self.transaction_df['Created At'].dt.month_name()
            self.transaction_df['Transaction_Hour'] = self.transaction_df['Created At'].dt.hour
            
            # Create deposit dataframe
            self.deposit_df = self.transaction_df[
                self.transaction_df['Transaction_Year'] == self.year
            ].copy()
            
            return True
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return False
    
    def calculate_metrics(self):
        """Calculate all key metrics"""
        metrics = {}
        
        try:
            # Basic counts
            metrics['total_agents'] = len(self.onboarding_df[
                self.onboarding_df['Entity'] == 'AGENT'
            ]) if 'Entity' in self.onboarding_df.columns else 0
            
            metrics['active_agents'] = len(self.onboarding_df[
                (self.onboarding_df['Entity'] == 'AGENT') & 
                (self.onboarding_df['Status'] == 'ACTIVE')
            ]) if all(col in self.onboarding_df.columns for col in ['Entity', 'Status']) else 0
            
            metrics['active_tellers'] = len(self.onboarding_df[
                (self.onboarding_df['Entity'].str.contains('TELLER', na=False)) &
                (self.onboarding_df['Status'] == 'ACTIVE')
            ]) if all(col in self.onboarding_df.columns for col in ['Entity', 'Status']) else 0
            
            # Onboarding metrics
            if 'Registration Date' in self.onboarding_df.columns:
                metrics['onboarded_this_year'] = len(self.onboarding_df[
                    self.onboarding_df['Registration Date'].dt.year == self.year
                ])
            else:
                metrics['onboarded_this_year'] = 0
            
            # Transaction metrics
            year_transactions = self.transaction_df[
                self.transaction_df['Transaction_Year'] == self.year
            ]
            
            metrics['total_transactions'] = len(year_transactions)
            metrics['transaction_volume'] = year_transactions['Amount'].sum() if 'Amount' in year_transactions.columns else 0
            
            # Success/Failure metrics
            if 'Status' in self.transaction_df.columns:
                metrics['successful_transactions'] = len(year_transactions[
                    year_transactions['Status'].str.contains('SUCCESS', case=False, na=False)
                ])
                metrics['failed_transactions'] = len(year_transactions[
                    year_transactions['Status'].str.contains('FAIL', case=False, na=False)
                ])
            else:
                metrics['successful_transactions'] = 0
                metrics['failed_transactions'] = 0
            
            # Agent performance ranking
            if 'User Identifier' in year_transactions.columns and 'Amount' in year_transactions.columns:
                agent_performance = year_transactions.groupby('User Identifier').agg({
                    'Amount': ['sum', 'count']
                }).reset_index()
                agent_performance.columns = ['User Identifier', 'Total_Amount', 'Transaction_Count']
                metrics['top_performing_agents'] = agent_performance.sort_values('Total_Amount', ascending=False).head(20).to_dict('records')
            else:
                metrics['top_performing_agents'] = []
            
            # Monthly data
            monthly_data = []
            months = ['January', 'February', 'March', 'April', 'May', 'June', 
                     'July', 'August', 'September', 'October', 'November', 'December']
            
            for i, month in enumerate(months, 1):
                month_transactions = year_transactions[
                    year_transactions['Transaction_Month'] == month
                ]
                monthly_data.append({
                    'Month': month,
                    'Transaction_Count': len(month_transactions),
                    'Transaction_Volume': month_transactions['Amount'].sum() if 'Amount' in month_transactions.columns else 0,
                    'Active_Users': month_transactions['User Identifier'].nunique() if 'User Identifier' in month_transactions.columns else 0
                })
            
            metrics['monthly_data'] = monthly_data
            
            # Service breakdown
            if 'Service Name' in year_transactions.columns:
                service_breakdown = year_transactions.groupby('Service Name').agg({
                    'Amount': ['sum', 'count']
                }).reset_index()
                service_breakdown.columns = ['Service Name', 'Total_Amount', 'Transaction_Count']
                metrics['service_breakdown'] = service_breakdown.to_dict('records')
            else:
                metrics['service_breakdown'] = []
            
            return metrics
            
        except Exception as e:
            st.error(f"Error calculating metrics: {str(e)}")
            return None
    
    def get_monthly_dataframe(self):
        """Get monthly data as DataFrame"""
        if hasattr(self, 'metrics') and 'monthly_data' in self.metrics:
            return pd.DataFrame(self.metrics['monthly_data'])
        return pd.DataFrame()
    
    def get_summary_dataframe(self):
        """Get summary data as DataFrame"""
        summary_data = []
        if hasattr(self, 'metrics'):
            for key, value in self.metrics.items():
                if key not in ['monthly_data', 'top_performing_agents', 'service_breakdown']:
                    summary_data.append({'Metric': key, 'Value': value})
        return pd.DataFrame(summary_data)

# =========================
# Initialize Session State
# =========================
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/6676/6676796.png", width=100)
    st.title("APS Wallet Dashboard")
    st.markdown("---")
    
    # Year selection
    selected_year = st.selectbox(
        "📅 Select Year",
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
        "Minimum transactions for active status",
        min_value=1,
        max_value=100,
        value=20
    )
    
    # Sample data toggle
    use_sample = st.checkbox("Use Sample Data for Demo", value=False)
    
    # Process button
    if st.button("🚀 Process & Analyze", type="primary", use_container_width=True):
        if use_sample or (onboarding_file is not None and transaction_file is not None):
            with st.spinner("🔍 Processing data... This may take a moment..."):
                try:
                    # Initialize analyzer
                    analyzer = AnalyticsEngine(year=selected_year, min_deposits_for_active=min_deposits)
                    
                    if use_sample:
                        # Create sample data
                        st.info("Using demo data for preview")
                        
                        # Create sample onboarding data
                        sample_onboarding = pd.DataFrame({
                            'User Identifier': [f'USER{i:04d}' for i in range(1, 101)],
                            'Entity': ['AGENT'] * 70 + ['TELLER'] * 30,
                            'Status': ['ACTIVE'] * 85 + ['INACTIVE'] * 15,
                            'Registration Date': pd.date_range('2024-01-01', periods=100, freq='D')
                        })
                        
                        # Create sample transaction data
                        sample_transactions = pd.DataFrame({
                            'User Identifier': np.random.choice([f'USER{i:04d}' for i in range(1, 101)], 5000),
                            'Amount': np.random.exponential(1000, 5000),
                            'Service Name': np.random.choice(['Deposit', 'Withdrawal', 'Transfer', 'Payment'], 5000),
                            'Status': np.random.choice(['SUCCESS', 'FAILED'], 5000, p=[0.95, 0.05]),
                            'Created At': pd.date_range('2024-01-01', periods=5000, freq='H')
                        })
                        
                        # Save to files in memory
                        onboarding_buffer = io.StringIO()
                        transaction_buffer = io.StringIO()
                        sample_onboarding.to_csv(onboarding_buffer, index=False)
                        sample_transactions.to_csv(transaction_buffer, index=False)
                        
                        # Reset buffer positions
                        onboarding_buffer.seek(0)
                        transaction_buffer.seek(0)
                        
                        # Load sample data
                        success = analyzer.load_data(onboarding_buffer, transaction_buffer)
                    else:
                        # Load uploaded files
                        success = analyzer.load_data(onboarding_file, transaction_file)
                    
                    if success:
                        # Calculate metrics
                        metrics = analyzer.calculate_metrics()
                        
                        if metrics:
                            # Store in session state
                            st.session_state.analyzer = analyzer
                            st.session_state.metrics = metrics
                            st.session_state.data_loaded = True
                            st.session_state.analyzer.metrics = metrics  # Store metrics in analyzer
                            
                            st.success("✅ Data processed successfully!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Failed to calculate metrics")
                    else:
                        st.error("Failed to load data")
                        
                except Exception as e:
                    st.error(f"❌ Error processing data: {str(e)}")
        else:
            st.warning("⚠️ Please upload files or select 'Use Sample Data'")

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
        1. 📤 Upload your data files in the sidebar
        2. ⚙️ Configure analysis parameters
        3. 🚀 Click 'Process & Analyze'
        
        Or use sample data for a demo experience.
        """)
        
        with st.expander("📋 Expected Data Format"):
            st.markdown("""
            **Onboarding Data should contain:**
            - User Identifier
            - Entity (AGENT/TELLER)
            - Status (ACTIVE/INACTIVE)
            - Registration Date
            
            **Transaction Data should contain:**
            - User Identifier
            - Amount
            - Service Name
            - Status
            - Created At
            """)
        
        st.info("👈 Upload data files in the sidebar to begin analysis")
else:
    # Display metrics
    metrics = st.session_state.metrics
    analyzer = st.session_state.analyzer
    
    # KPI Cards - Row 1
    st.markdown("<h2 class='sub-header'>📊 Key Performance Indicators</h2>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Agents</div>
            <div class="metric-value">{metrics.get('active_agents', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Tellers</div>
            <div class="metric-value">{metrics.get('active_tellers', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{selected_year} Onboarded</div>
            <div class="metric-value">{metrics.get('onboarded_this_year', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        volume = metrics.get('transaction_volume', 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Transaction Volume</div>
            <div class="metric-value">${volume:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # KPI Cards - Row 2
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_users = 0
        if 'monthly_data' in metrics:
            for month_data in metrics['monthly_data']:
                active_users = max(active_users, month_data.get('Active_Users', 0))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Peak Active Users</div>
            <div class="metric-value">{active_users:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        successful = metrics.get('successful_transactions', 0)
        failed = metrics.get('failed_transactions', 0)
        total = successful + failed
        success_rate = (successful / total * 100) if total > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Success Rate</div>
            <div class="metric-value">{success_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        agents_with_tellers = 0  # Placeholder - would need actual data
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Transactions</div>
            <div class="metric-value">{metrics.get('total_transactions', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        growth_rate = (metrics.get('onboarded_this_year', 0) / metrics.get('active_agents', 1) * 100)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">YoY Growth</div>
            <div class="metric-value">{growth_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", 
        "👥 Agent Network", 
        "💰 Transactions", 
        "📅 Monthly Trends",
        "🏆 Top Performers"
    ])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly active users chart
            monthly_df = analyzer.get_monthly_dataframe()
            if not monthly_df.empty:
                fig = px.bar(
                    monthly_df,
                    x='Month',
                    y='Active_Users',
                    title='Monthly Active Users',
                    color='Active_Users',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No monthly data available")
        
        with col2:
            # Onboarding pie chart
            fig = px.pie(
                values=[
                    metrics.get('active_agents', 0),
                    metrics.get('active_tellers', 0)
                ],
                names=['Agents', 'Tellers'],
                title='Active User Distribution',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Entity distribution
            if analyzer.onboarding_df is not None and 'Entity' in analyzer.onboarding_df.columns:
                entity_counts = analyzer.onboarding_df['Entity'].value_counts().reset_index()
                entity_counts.columns = ['Entity', 'Count']
                
                fig = px.treemap(
                    entity_counts,
                    path=['Entity'],
                    values='Count',
                    title='User Entity Distribution',
                    color='Count',
                    color_continuous_scale='RdBu'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Entity data not available")
        
        with col2:
            # Status distribution
            if analyzer.onboarding_df is not None and 'Status' in analyzer.onboarding_df.columns:
                status_counts = analyzer.onboarding_df['Status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                
                fig = px.bar(
                    status_counts.head(10),
                    x='Status',
                    y='Count',
                    title='User Status Distribution',
                    color='Count',
                    color_continuous_scale='thermal'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Status data not available")
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            # Transaction success/failure
            trans_data = {
                'Status': ['Successful', 'Failed'],
                'Count': [
                    metrics.get('successful_transactions', 0),
                    metrics.get('failed_transactions', 0)
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
            # Service breakdown
            if 'service_breakdown' in metrics and metrics['service_breakdown']:
                service_df = pd.DataFrame(metrics['service_breakdown'])
                fig = px.bar(
                    service_df,
                    x='Service Name',
                    y='Total_Amount',
                    title='Transaction Volume by Service',
                    color='Transaction_Count',
                    labels={'Total_Amount': 'Total Amount', 'Transaction_Count': 'Transaction Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Service breakdown data not available")
    
    with tab4:
        # Monthly trends comparison
        monthly_df = analyzer.get_monthly_dataframe()
        
        if not monthly_df.empty and 'Transaction_Volume' in monthly_df.columns:
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
                    y=monthly_df['Transaction_Volume'],
                    name='Transaction Volume',
                    mode='lines+markers',
                    line=dict(color='#FFA15A', width=3)
                ),
                secondary_y=True
            )
            
            fig.update_layout(
                title='Monthly Trends: Active Users vs Transaction Volume',
                xaxis_title='Month',
                showlegend=True
            )
            
            fig.update_yaxes(title_text="Active Users", secondary_y=False)
            fig.update_yaxes(title_text="Transaction Volume ($)", secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Monthly trend data not available")
    
    with tab5:
        # Performance matrix
        st.markdown("### 🏆 Top Performing Agents")
        
        if 'top_performing_agents' in metrics and metrics['top_performing_agents']:
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
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"aps_wallet_summary_{selected_year}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("📈 Download Monthly Data", use_container_width=True):
            monthly_df = analyzer.get_monthly_dataframe()
            if not monthly_df.empty:
                csv = monthly_df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv,
                    file_name=f"aps_wallet_monthly_{selected_year}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.warning("No monthly data to export")
    
    with col3:
        if st.button("💾 Export Raw Data", use_container_width=True):
            # Create Excel file with multiple sheets
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                if analyzer.onboarding_df is not None:
                    analyzer.onboarding_df.to_excel(writer, sheet_name='Onboarding', index=False)
                if analyzer.transaction_df is not None:
                    analyzer.transaction_df.to_excel(writer, sheet_name='Transactions', index=False)
                summary_df = analyzer.get_summary_dataframe()
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            output.seek(0)
            st.download_button(
                label="⬇️ Download Excel",
                data=output,
                file_name=f"aps_wallet_full_export_{selected_year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

# =========================
# Footer
# =========================
st.markdown("---")
st.markdown(
    f"""
    <div style="text-align: center; color: #6B7280; padding: 1rem;">
        <p>© {datetime.now().year} APS Wallet Performance Dashboard • Version 2.0</p>
        <p style="font-size: 0.8rem;">For internal use only</p>
    </div>
    """,
    unsafe_allow_html=True
)
