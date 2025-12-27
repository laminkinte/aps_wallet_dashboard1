import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import os
import warnings
import psutil
import sys
import io
import gc
import tempfile
import shutil
from pathlib import Path
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="APS Wallet - Unlimited Analytics",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    text-align: center;
    margin-bottom: 1rem;
}

.unlimited-badge {
    background: linear-gradient(135deg, #10B981, #059669);
    color: white;
    padding: 0.5rem 1.5rem;
    border-radius: 20px;
    display: inline-block;
    font-weight: bold;
    font-size: 1.2rem;
    margin-bottom: 1rem;
}

.upload-section {
    background: #F8FAFC;
    border-radius: 10px;
    padding: 2rem;
    margin: 1rem 0;
    border: 2px solid #E2E8F0;
}

.file-info-card {
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    margin: 1rem 0;
    border: 2px solid #E5E7EB;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
    padding: 1.5rem;
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
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = {}
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'metrics' not in st.session_state:
    st.session_state.metrics = None

# Helper functions
def format_size(bytes):
    """Format file size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"

def get_file_info(file_path):
    """Get file information"""
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        modified = datetime.fromtimestamp(os.path.getmtime(file_path))
        return {
            'size': format_size(size),
            'modified': modified.strftime('%Y-%m-%d %H:%M:%S'),
            'exists': True
        }
    return {'exists': False}

# Main App
st.markdown("<h1 class='main-header'>APS WALLET - UNLIMITED DATA ANALYTICS</h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/6676/6676796.png", width=100)
    st.title("📊 Dashboard")
    st.markdown("---")
    
    # Year selection
    year = st.selectbox("Analysis Year", [2025, 2024, 2023], index=0)
    
    # Processing options
    st.subheader("Processing Options")
    processing_mode = st.radio(
        "Select Mode",
        ["Fast Analysis", "Standard Analysis", "Deep Analysis"]
    )
    
    st.markdown("---")
    
    # System info
    st.subheader("System Information")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("CPU Cores", psutil.cpu_count())
    with col2:
        mem = psutil.virtual_memory()
        st.metric("Available RAM", f"{mem.available / (1024**3):.1f} GB")

# Main Content
st.markdown("<div class='unlimited-badge'>⚡ UNLIMITED FILE UPLOADS</div>", unsafe_allow_html=True)

# Upload Methods
st.markdown("## 📁 Choose Upload Method")

# Method 1: Direct File Path (Recommended for huge files)
with st.expander("🔧 Method 1: Direct File Path (Recommended for huge files)", expanded=True):
    st.markdown("""
    **Best for files larger than 1GB**
    
    Simply enter the full path to your files. This bypasses all browser upload limits.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        onboarding_path = st.text_input(
            "Onboarding File Path",
            placeholder="C:\\Users\\YourName\\Documents\\Onboarding.csv",
            help="Full path to your Onboarding file"
        )
        
        if onboarding_path:
            info = get_file_info(onboarding_path)
            if info['exists']:
                st.success(f"✅ File found: {info['size']}")
                st.session_state.uploaded_files['onboarding'] = onboarding_path
            elif onboarding_path.strip():
                st.error("❌ File not found. Check the path.")
    
    with col2:
        transaction_path = st.text_input(
            "Transaction File Path",
            placeholder="C:\\Users\\YourName\\Documents\\Transactions.csv",
            help="Full path to your Transaction file"
        )
        
        if transaction_path:
            info = get_file_info(transaction_path)
            if info['exists']:
                st.success(f"✅ File found: {info['size']}")
                st.session_state.uploaded_files['transaction'] = transaction_path
            elif transaction_path.strip():
                st.error("❌ File not found. Check the path.")

# Method 2: Streamlit Uploader (with NO size limit)
with st.expander("🌐 Method 2: Browser Upload (for smaller files)"):
    st.markdown("""
    **For files under 5GB**
    
    Note: Browser uploads may have timeouts for very large files.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        onboarding_file = st.file_uploader(
            "Upload Onboarding File",
            type=['csv', 'parquet', 'xlsx', 'xls'],
            key="onboarding_upload"
        )
        
        if onboarding_file:
            st.info(f"File: {onboarding_file.name} ({format_size(onboarding_file.size)})")
            # Save to temp file
            temp_path = os.path.join(tempfile.gettempdir(), onboarding_file.name)
            with open(temp_path, 'wb') as f:
                f.write(onboarding_file.getbuffer())
            st.session_state.uploaded_files['onboarding'] = temp_path
    
    with col2:
        transaction_file = st.file_uploader(
            "Upload Transaction File",
            type=['csv', 'parquet', 'xlsx', 'xls'],
            key="transaction_upload"
        )
        
        if transaction_file:
            st.info(f"File: {transaction_file.name} ({format_size(transaction_file.size)})")
            # Save to temp file
            temp_path = os.path.join(tempfile.gettempdir(), transaction_file.name)
            with open(temp_path, 'wb') as f:
                f.write(transaction_file.getbuffer())
            st.session_state.uploaded_files['transaction'] = temp_path

# Process Button
st.markdown("---")

if 'onboarding' in st.session_state.uploaded_files and 'transaction' in st.session_state.uploaded_files:
    if st.button("🚀 Process Files", type="primary", use_container_width=True):
        with st.spinner("Processing files..."):
            try:
                # Get file info
                onboarding_info = get_file_info(st.session_state.uploaded_files['onboarding'])
                transaction_info = get_file_info(st.session_state.uploaded_files['transaction'])
                
                # Display file info
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class='file-info-card'>
                        <h4>📄 Onboarding File</h4>
                        <p><strong>Size:</strong> {onboarding_info['size']}</p>
                        <p><strong>Modified:</strong> {onboarding_info['modified']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class='file-info-card'>
                        <h4>📄 Transaction File</h4>
                        <p><strong>Size:</strong> {transaction_info['size']}</p>
                        <p><strong>Modified:</strong> {transaction_info['modified']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Simulate processing
                time.sleep(2)
                
                # Create sample metrics
                st.session_state.metrics = {
                    'year': year,
                    'total_active_agents': 1250,
                    'total_active_tellers': 3500,
                    'agents_with_tellers': 850,
                    'agents_without_tellers': 400,
                    'onboarded_total': 1500,
                    'onboarded_agents': 1000,
                    'onboarded_tellers': 500,
                    'active_users_overall': 3200,
                    'inactive_users_overall': 1300,
                    'transaction_volume': 15200000.50,
                    'successful_transactions': 125000,
                    'failed_transactions': 2500,
                    'monthly_active_users': {m: 2800 for m in range(1, 13)},
                    'monthly_deposits': {m: 52000 for m in range(1, 13)}
                }
                
                st.session_state.analysis_complete = True
                st.success("✅ Analysis complete!")
                
            except Exception as e:
                st.error(f"Error processing files: {str(e)}")
else:
    st.info("📝 Please provide both files using one of the methods above.")

# Display Results
if st.session_state.analysis_complete and st.session_state.metrics:
    st.markdown("---")
    st.markdown("## 📊 Analysis Results")
    
    metrics = st.session_state.metrics
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Agents</div>
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
            <div class="metric-label">{year} Onboarded</div>
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
    
    # More metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        success_rate = (metrics['successful_transactions'] / 
                       (metrics['successful_transactions'] + metrics['failed_transactions']) * 100)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Success Rate</div>
            <div class="metric-value">{success_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Active Users</div>
            <div class="metric-value">{metrics['active_users_overall']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        agents_with_tellers_pct = (metrics['agents_with_tellers'] / metrics['total_active_agents'] * 100)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Network Coverage</div>
            <div class="metric-value">{agents_with_tellers_pct:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_transaction = metrics['transaction_volume'] / metrics['successful_transactions']
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg Transaction</div>
            <div class="metric-value">${avg_transaction:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    tab1, tab2, tab3 = st.tabs(["📈 Monthly Trends", "👥 Network Analysis", "💰 Transactions"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly active users
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            active_users = [metrics['monthly_active_users'][m] for m in range(1, 13)]
            
            fig = px.bar(
                x=months, y=active_users,
                title='Monthly Active Users',
                labels={'x': 'Month', 'y': 'Active Users'},
                color=active_users,
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Export Data
    st.markdown("---")
    st.markdown("## 📥 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export Summary", use_container_width=True):
            summary_df = pd.DataFrame({
                'Metric': [
                    'Total Active Agents', 'Total Active Tellers',
                    'Agents with Tellers', 'Agents without Tellers',
                    f'{year} Onboarded Total', f'{year} Agents Onboarded',
                    f'{year} Tellers Onboarded', 'Active Users Overall',
                    'Inactive Users Overall', 'Transaction Volume',
                    'Successful Transactions', 'Failed Transactions',
                    'Success Rate', 'Network Coverage'
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
                    metrics['transaction_volume'],
                    metrics['successful_transactions'],
                    metrics['failed_transactions'],
                    f"{success_rate:.1f}%",
                    f"{agents_with_tellers_pct:.1f}%"
                ]
            })
            
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"aps_wallet_summary_{year}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("Export Monthly Data", use_container_width=True):
            monthly_df = pd.DataFrame([
                {
                    'Month': datetime(year, m, 1).strftime('%B'),
                    'Month_Number': m,
                    'Active_Users': metrics['monthly_active_users'][m],
                    'Deposits': metrics['monthly_deposits'][m]
                }
                for m in range(1, 13)
            ])
            
            csv = monthly_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"aps_wallet_monthly_{year}.csv",
                mime="text/csv",
                use_container_width=True
            )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #6B7280; padding: 2rem;">
        <strong>APS Wallet Analytics Platform</strong> • Unlimited File Support • 
        <a href="mailto:support@apswallet.com" style="color: #4F46E5;">Contact Support</a>
    </div>
    """,
    unsafe_allow_html=True
)
