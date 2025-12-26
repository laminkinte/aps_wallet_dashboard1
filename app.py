"""
APS Wallet - Annual Performance Dashboard
Main Application File
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
from datetime import datetime
import io
import warnings
warnings.filterwarnings('ignore')

# =========================
# Page Configuration
# =========================
st.set_page_config(
    page_title="APS Wallet Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Custom CSS
# =========================
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
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F3F4F6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4F46E5;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# Analytics Engine
# =========================
class AnalyticsEngine:
    def __init__(self, year=2025):
        self.year = year
        self.onboarding_df = None
        self.transaction_df = None
        self.metrics = {}
    
    def load_data(self, onboarding_file, transaction_file):
        """Load and preprocess data"""
        try:
            # Load CSV files
            if hasattr(onboarding_file, 'read'):
                self.onboarding_df = pd.read_csv(onboarding_file)
            else:
                self.onboarding_df = pd.read_csv(onboarding_file)
            
            if hasattr(transaction_file, 'read'):
                self.transaction_df = pd.read_csv(transaction_file)
            else:
                self.transaction_df = pd.read_csv(transaction_file)
            
            # Clean column names
            self.onboarding_df.columns = self.onboarding_df.columns.str.strip().str.replace(' ', '_')
            self.transaction_df.columns = self.transaction_df.columns.str.strip().str.replace(' ', '_')
            
            # Convert date columns
            date_columns_onboarding = ['Registration_Date', 'RegistrationDate', 'Date']
            date_columns_transaction = ['Created_At', 'CreatedAt', 'Transaction_Date', 'Date']
            
            for col in date_columns_onboarding:
                if col in self.onboarding_df.columns:
                    self.onboarding_df[col] = pd.to_datetime(self.onboarding_df[col], errors='coerce')
                    break
            
            for col in date_columns_transaction:
                if col in self.transaction_df.columns:
                    self.transaction_df[col] = pd.to_datetime(self.transaction_df[col], errors='coerce')
                    break
            
            return True
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return False
    
    def calculate_metrics(self):
        """Calculate all key metrics"""
        try:
            # Initialize metrics
            metrics = {}
            
            # Onboarding metrics
            if self.onboarding_df is not None:
                # Total agents
                if 'Entity' in self.onboarding_df.columns:
                    metrics['total_agents'] = len(self.onboarding_df[
                        self.onboarding_df['Entity'] == 'AGENT'
                    ])
                    metrics['active_agents'] = len(self.onboarding_df[
                        (self.onboarding_df['Entity'] == 'AGENT') & 
                        (self.onboarding_df['Status'] == 'ACTIVE')
                    ])
                    metrics['active_tellers'] = len(self.onboarding_df[
                        (self.onboarding_df['Entity'].str.contains('TELLER', na=False)) &
                        (self.onboarding_df['Status'] == 'ACTIVE')
                    ])
                
                # Onboarding this year
                date_col = None
                for col in ['Registration_Date', 'RegistrationDate', 'Date']:
                    if col in self.onboarding_df.columns:
                        date_col = col
                        break
                
                if date_col:
                    self.onboarding_df['year'] = pd.to_datetime(self.onboarding_df[date_col]).dt.year
                    metrics['onboarded_this_year'] = len(self.onboarding_df[
                        self.onboarding_df['year'] == self.year
                    ])
                else:
                    metrics['onboarded_this_year'] = 0
            
            # Transaction metrics
            if self.transaction_df is not None:
                # Extract year
                date_col = None
                for col in ['Created_At', 'CreatedAt', 'Transaction_Date', 'Date']:
                    if col in self.transaction_df.columns:
                        date_col = col
                        break
                
                if date_col:
                    self.transaction_df['transaction_year'] = pd.to_datetime(self.transaction_df[date_col]).dt.year
                    self.transaction_df['transaction_month'] = pd.to_datetime(self.transaction_df[date_col]).dt.month_name()
                    
                    year_transactions = self.transaction_df[
                        self.transaction_df['transaction_year'] == self.year
                    ]
                    
                    # Basic transaction counts
                    metrics['total_transactions'] = len(year_transactions)
                    
                    # Transaction volume
                    if 'Amount' in year_transactions.columns:
                        metrics['transaction_volume'] = year_transactions['Amount'].sum()
                    else:
                        metrics['transaction_volume'] = 0
                    
                    # Success/failure
                    if 'Status' in year_transactions.columns:
                        metrics['successful_transactions'] = len(year_transactions[
                            year_transactions['Status'].str.contains('SUCCESS|COMPLETED', case=False, na=False)
                        ])
                        metrics['failed_transactions'] = len(year_transactions[
                            year_transactions['Status'].str.contains('FAIL|ERROR|REJECTED', case=False, na=False)
                        ])
                    else:
                        metrics['successful_transactions'] = 0
                        metrics['failed_transactions'] = 0
                    
                    # Monthly data
                    if 'transaction_month' in year_transactions.columns:
                        monthly_summary = year_transactions.groupby('transaction_month').agg({
                            'Amount': ['sum', 'count'] if 'Amount' in year_transactions.columns else pd.NamedAgg(column='transaction_year', aggfunc='count')
                        }).reset_index()
                        
                        # Flatten column names
                        if isinstance(monthly_summary.columns, pd.MultiIndex):
                            monthly_summary.columns = ['Month', 'Total_Amount', 'Transaction_Count']
                        else:
                            monthly_summary.columns = ['Month', 'Transaction_Count']
                            monthly_summary['Total_Amount'] = 0
                        
                        metrics['monthly_data'] = monthly_summary.to_dict('records')
                    
                    # Top performers
                    if 'User_Identifier' in year_transactions.columns or 'User' in year_transactions.columns:
                        user_col = 'User_Identifier' if 'User_Identifier' in year_transactions.columns else 'User'
                        if 'Amount' in year_transactions.columns:
                            top_performers = year_transactions.groupby(user_col).agg({
                                'Amount': ['sum', 'count']
                            }).reset_index()
                            top_performers.columns = [user_col, 'Total_Amount', 'Transaction_Count']
                            metrics['top_performing_agents'] = top_performers.sort_values('Total_Amount', ascending=False).head(10).to_dict('records')
            
            self.metrics = metrics
            return metrics
            
        except Exception as e:
            st.error(f"Error calculating metrics: {str(e)}")
            return None

# =========================
# Initialize Session State
# =========================
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'metrics' not in st.session_state:
    st.session_state.metrics = None
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.markdown("### 📊 APS Wallet Dashboard")
    st.markdown("---")
    
    # Year selection
    selected_year = st.selectbox(
        "Select Analysis Year",
        options=[2025, 2024, 2023],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 📁 Upload Data")
    
    # File uploaders
    onboarding_file = st.file_uploader(
        "Onboarding Data (CSV)",
        type=['csv'],
        key='onboarding_uploader'
    )
    
    transaction_file = st.file_uploader(
        "Transaction Data (CSV)",
        type=['csv'],
        key='transaction_uploader'
    )
    
    st.markdown("---")
    
    # Process button
    if st.button("🚀 Process Data", type="primary", use_container_width=True):
        if onboarding_file is not None and transaction_file is not None:
            with st.spinner("Processing data..."):
                try:
                    # Initialize analyzer
                    analyzer = AnalyticsEngine(year=selected_year)
                    
                    # Load data
                    if analyzer.load_data(onboarding_file, transaction_file):
                        # Calculate metrics
                        metrics = analyzer.calculate_metrics()
                        
                        if metrics:
                            # Store in session state
                            st.session_state.analyzer = analyzer
                            st.session_state.metrics = metrics
                            st.session_state.data_loaded = True
                            
                            st.success("✅ Data processed successfully!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Please upload both CSV files")
    
    # Demo mode
    st.markdown("---")
    demo_mode = st.checkbox("Enable Demo Mode", value=False)
    
    if demo_mode and st.button("📊 Load Demo Data", use_container_width=True):
        with st.spinner("Loading demo data..."):
            try:
                # Create demo data
                np.random.seed(42)
                
                # Demo onboarding data
                demo_onboarding = pd.DataFrame({
                    'User_Identifier': [f'AGENT_{i:04d}' for i in range(1, 101)],
                    'Entity': ['AGENT'] * 70 + ['TELLER'] * 30,
                    'Status': ['ACTIVE'] * 85 + ['INACTIVE'] * 15,
                    'Registration_Date': pd.date_range('2023-01-01', periods=100, freq='D')
                })
                
                # Demo transaction data
                demo_transactions = pd.DataFrame({
                    'User_Identifier': np.random.choice([f'AGENT_{i:04d}' for i in range(1, 101)], 1000),
                    'Amount': np.random.uniform(100, 10000, 1000),
                    'Service_Name': np.random.choice(['Deposit', 'Withdrawal', 'Transfer', 'Bill Payment'], 1000),
                    'Status': np.random.choice(['SUCCESS', 'FAILED'], 1000, p=[0.95, 0.05]),
                    'Created_At': pd.date_range('2024-01-01', periods=1000, freq='H')
                })
                
                # Convert to file-like objects
                onboarding_buffer = io.StringIO()
                transaction_buffer = io.StringIO()
                demo_onboarding.to_csv(onboarding_buffer, index=False)
                demo_transactions.to_csv(transaction_buffer, index=False)
                onboarding_buffer.seek(0)
                transaction_buffer.seek(0)
                
                # Initialize analyzer with demo data
                analyzer = AnalyticsEngine(year=selected_year)
                if analyzer.load_data(onboarding_buffer, transaction_buffer):
                    metrics = analyzer.calculate_metrics()
                    
                    if metrics:
                        st.session_state.analyzer = analyzer
                        st.session_state.metrics = metrics
                        st.session_state.data_loaded = True
                        
                        st.success("✅ Demo data loaded successfully!")
                        
            except Exception as e:
                st.error(f"❌ Error loading demo data: {str(e)}")
    
    st.markdown("---")
    st.caption(f"© {datetime.now().year} APS Wallet Analytics")

# =========================
# Main Content
# =========================
st.markdown("<h1 class='main-header'>💰 APS Wallet Annual Dashboard</h1>", unsafe_allow_html=True)

if not st.session_state.data_loaded:
    # Welcome screen
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h3>Welcome to APS Wallet Analytics</h3>
            <p>Upload your data files to analyze agent performance and transaction metrics.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📋 Data Requirements"):
            st.markdown("""
            **Required CSV Files:**
            
            **1. Onboarding Data** should include:
            - User Identifier
            - Entity (Agent/Teller)
            - Status (Active/Inactive)
            - Registration Date
            
            **2. Transaction Data** should include:
            - User Identifier
            - Amount
            - Service Name
            - Status
            - Transaction Date
            """)
        
        st.info("👈 Upload CSV files in the sidebar to begin analysis")
else:
    # Display metrics
    metrics = st.session_state.metrics
    
    # KPI Section
    st.markdown("<h2 class='sub-header'>📊 Performance Overview</h2>", unsafe_allow_html=True)
    
    # Row 1
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Active Agents",
            value=f"{metrics.get('active_agents', 0):,}"
        )
    
    with col2:
        st.metric(
            label="Active Tellers",
            value=f"{metrics.get('active_tellers', 0):,}"
        )
    
    with col3:
        st.metric(
            label=f"{selected_year} Onboarded",
            value=f"{metrics.get('onboarded_this_year', 0):,}"
        )
    
    with col4:
        volume = metrics.get('transaction_volume', 0)
        st.metric(
            label="Transaction Volume",
            value=f"${volume:,.0f}"
        )
    
    # Row 2
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Transactions",
            value=f"{metrics.get('total_transactions', 0):,}"
        )
    
    with col2:
        successful = metrics.get('successful_transactions', 0)
        failed = metrics.get('failed_transactions', 0)
        total = successful + failed
        success_rate = (successful / total * 100) if total > 0 else 0
        st.metric(
            label="Success Rate",
            value=f"{success_rate:.1f}%"
        )
    
    with col3:
        st.metric(
            label="Total Agents",
            value=f"{metrics.get('total_agents', 0):,}"
        )
    
    # Tabs for detailed views
    tab1, tab2, tab3 = st.tabs(["📈 Charts", "📊 Tables", "📥 Export"])
    
    with tab1:
        # Charts tab
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly transactions chart
            if 'monthly_data' in metrics and metrics['monthly_data']:
                monthly_df = pd.DataFrame(metrics['monthly_data'])
                if not monthly_df.empty and 'Total_Amount' in monthly_df.columns:
                    fig = px.bar(
                        monthly_df,
                        x='Month',
                        y='Total_Amount',
                        title='Monthly Transaction Volume',
                        color='Total_Amount',
                        color_continuous_scale='viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Success rate pie chart
            if successful > 0 or failed > 0:
                fig = px.pie(
                    values=[successful, failed],
                    names=['Successful', 'Failed'],
                    title='Transaction Success Rate',
                    hole=0.4,
                    color_discrete_sequence=['#00CC96', '#EF553B']
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Tables tab
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Monthly Summary")
            if 'monthly_data' in metrics and metrics['monthly_data']:
                monthly_df = pd.DataFrame(metrics['monthly_data'])
                st.dataframe(monthly_df, use_container_width=True)
        
        with col2:
            st.markdown("### Top Performers")
            if 'top_performing_agents' in metrics and metrics['top_performing_agents']:
                top_df = pd.DataFrame(metrics['top_performing_agents'])
                st.dataframe(top_df, use_container_width=True)
    
    with tab3:
        # Export tab
        st.markdown("### 📥 Data Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Summary export
            if st.button("Export Summary Report"):
                summary_data = []
                for key, value in metrics.items():
                    if key not in ['monthly_data', 'top_performing_agents']:
                        summary_data.append({'Metric': key, 'Value': value})
                
                summary_df = pd.DataFrame(summary_data)
                csv = summary_df.to_csv(index=False)
                
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"aps_summary_{selected_year}.csv",
                    mime="text/csv"
                )
        
        with col2:
            # Raw data export
            if st.button("Export Raw Data"):
                analyzer = st.session_state.analyzer
                
                if analyzer.onboarding_df is not None and analyzer.transaction_df is not None:
                    # Create Excel file
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        analyzer.onboarding_df.to_excel(writer, sheet_name='Onboarding', index=False)
                        analyzer.transaction_df.to_excel(writer, sheet_name='Transactions', index=False)
                    
                    output.seek(0)
                    
                    st.download_button(
                        label="Download Excel",
                        data=output,
                        file_name=f"aps_raw_data_{selected_year}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

# =========================
# Footer
# =========================
st.markdown("---")
st.markdown(
    f"""
    <div style="text-align: center; color: #6B7280; padding: 1rem;">
        <p>APS Wallet Analytics Dashboard • Version 1.0 • {datetime.now().strftime('%Y-%m-%d')}</p>
    </div>
    """,
    unsafe_allow_html=True
)
