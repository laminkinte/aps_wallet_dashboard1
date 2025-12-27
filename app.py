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
import os
import warnings
import tempfile
import shutil
from pathlib import Path
import psutil
import sys
warnings.filterwarnings('ignore')

# Try to import optional performance packages
try:
    import dask.dataframe as dd
    DASK_AVAILABLE = True
except ImportError:
    DASK_AVAILABLE = False
    st.warning("Dask not available. Using pandas for large files.")

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Import our analyzer
try:
    from utils.large_file_analyzer import LargeFileAnalyzer, AnalysisConfig
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    from utils.analyzer import AgentPerformanceAnalyzer, AnalysisConfig
    st.warning("Large file analyzer not available. Using standard analyzer.")

# Page configuration
st.set_page_config(
    page_title="APS Wallet - Large Data Dashboard",
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
        # Fallback CSS
        st.markdown("""
        <style>
        .main-header { font-size: 2.5rem; color: #1E3A8A; text-align: center; }
        .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      padding: 1.5rem; border-radius: 10px; color: white; }
        .metric-value { font-size: 2rem; font-weight: 700; }
        .metric-label { font-size: 0.9rem; opacity: 0.9; }
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
if 'file_paths' not in st.session_state:
    st.session_state.file_paths = {}
if 'processing_progress' not in st.session_state:
    st.session_state.processing_progress = 0
if 'memory_usage' not in st.session_state:
    st.session_state.memory_usage = 0

# Helper functions for large file handling
def get_system_memory():
    """Get available system memory in GB"""
    return psutil.virtual_memory().available / (1024 ** 3)

def estimate_chunk_size(file_size_mb, available_memory_gb):
    """Estimate optimal chunk size based on available memory"""
    # Use 25% of available memory for safety
    max_memory_for_chunk = available_memory_gb * 0.25 * 1024  # Convert to MB
    # Don't exceed 500MB per chunk for stability
    return min(500, max(100, int(max_memory_for_chunk / 2)))

def save_uploaded_file(uploaded_file, temp_dir="temp_uploads"):
    """Save uploaded file to disk and return path"""
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, uploaded_file.name)
    
    with st.spinner(f"Saving {uploaded_file.name}... This may take a while for large files."):
        with open(file_path, "wb") as f:
            # Use chunked writing for large files
            chunk_size = 10 * 1024 * 1024  # 10MB chunks
            progress_bar = st.progress(0)
            bytes_written = 0
            total_size = uploaded_file.size
            
            while True:
                chunk = uploaded_file.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                bytes_written += len(chunk)
                progress = bytes_written / total_size
                progress_bar.progress(progress)
            
            progress_bar.empty()
    
    return file_path

def convert_to_parquet(csv_path, parquet_path=None):
    """Convert CSV to Parquet for faster loading"""
    if parquet_path is None:
        parquet_path = csv_path.replace('.csv', '.parquet')
    
    if not PARQUET_AVAILABLE:
        return csv_path
    
    if os.path.exists(parquet_path):
        return parquet_path
    
    with st.spinner("Converting to Parquet format for faster processing..."):
        # Read CSV in chunks and write to Parquet
        chunk_size = 1000000  # 1 million rows per chunk
        first_chunk = True
        
        for chunk in pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False):
            if first_chunk:
                chunk.to_parquet(parquet_path, engine='pyarrow')
                first_chunk = False
            else:
                chunk.to_parquet(parquet_path, engine='pyarrow', append=True)
    
    return parquet_path

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/6676/6676796.png", width=100)
    st.title("APS Wallet Dashboard")
    st.markdown("---")
    
    # System info
    st.subheader("System Information")
    memory_info = psutil.virtual_memory()
    st.write(f"**Available Memory:** {memory_info.available / (1024**3):.1f} GB")
    st.write(f"**Total Memory:** {memory_info.total / (1024**3):.1f} GB")
    
    st.markdown("---")
    
    # Year selection
    selected_year = st.selectbox(
        "Select Year",
        options=[2025, 2024, 2023],
        index=0
    )
    
    # File upload with large file support
    st.subheader("Upload Data Files (Supports up to 5GB)")
    
    # File type selection
    file_format = st.radio(
        "File Format",
        ["CSV", "Parquet", "Excel"],
        horizontal=True
    )
    
    # Chunk processing options
    st.subheader("Processing Options")
    use_chunked_processing = st.checkbox("Use Chunked Processing", value=True)
    use_parallel_processing = st.checkbox("Use Parallel Processing", value=DASK_AVAILABLE)
    convert_to_optimized_format = st.checkbox("Convert to Optimized Format", value=PARQUET_AVAILABLE)
    
    if use_chunked_processing:
        chunk_size = st.slider(
            "Chunk Size (rows)",
            min_value=100000,
            max_value=5000000,
            value=1000000,
            step=100000,
            help="Number of rows to process at a time"
        )
    
    # File uploaders
    onboarding_file = st.file_uploader(
        f"Onboarding Data ({file_format})",
        type=['csv', 'parquet', 'xlsx', 'xls'],
        help="Upload Onboarding file (up to 5GB)"
    )
    
    transaction_file = st.file_uploader(
        f"Transaction Data ({file_format})",
        type=['csv', 'parquet', 'xlsx', 'xls'],
        help="Upload Transaction file (up to 5GB)"
    )
    
    # Analysis parameters
    st.subheader("Analysis Parameters")
    min_deposits = st.slider(
        "Minimum deposits for 'Active' status",
        min_value=1,
        max_value=100,
        value=20
    )
    
    # Process button
    process_button = st.button("🚀 Process Large Files", type="primary", use_container_width=True)
    
    if process_button:
        if onboarding_file and transaction_file:
            with st.spinner("Processing large files. This may take several minutes..."):
                try:
                    # Create progress containers
                    progress_container = st.container()
                    memory_container = st.container()
                    status_container = st.container()
                    
                    # Step 1: Save files to disk
                    with status_container:
                        st.info("Step 1/4: Saving uploaded files to disk...")
                    
                    onboarding_path = save_uploaded_file(onboarding_file)
                    transaction_path = save_uploaded_file(transaction_file)
                    
                    # Step 2: Convert to optimized format if requested
                    if convert_to_optimized_format and file_format == "CSV":
                        with status_container:
                            st.info("Step 2/4: Converting to optimized format...")
                        
                        onboarding_path = convert_to_parquet(onboarding_path)
                        transaction_path = convert_to_parquet(transaction_path)
                    
                    # Store file paths
                    st.session_state.file_paths = {
                        'onboarding': onboarding_path,
                        'transaction': transaction_path
                    }
                    
                    # Step 3: Initialize analyzer with large file support
                    with status_container:
                        st.info("Step 3/4: Initializing analyzer...")
                    
                    config = AnalysisConfig(
                        year=selected_year,
                        min_deposits_for_active=min_deposits
                    )
                    
                    # Choose analyzer based on available packages
                    if ANALYZER_AVAILABLE and 'LargeFileAnalyzer' in globals():
                        analyzer = LargeFileAnalyzer(
                            onboarding_path=onboarding_path,
                            transaction_path=transaction_path,
                            config=config,
                            use_chunked=use_chunked_processing,
                            use_parallel=use_parallel_processing,
                            chunk_size=chunk_size if use_chunked_processing else None
                        )
                    else:
                        # Fallback to standard analyzer with disk-based processing
                        from utils.analyzer import AgentPerformanceAnalyzer
                        analyzer = AgentPerformanceAnalyzer(config=config)
                        analyzer.load_large_files(
                            onboarding_path=onboarding_path,
                            transaction_path=transaction_path,
                            chunk_size=chunk_size if use_chunked_processing else 1000000
                        )
                    
                    st.session_state.analyzer = analyzer
                    
                    # Step 4: Calculate metrics
                    with status_container:
                        st.info("Step 4/4: Calculating metrics...")
                    
                    # Create progress callback for the analyzer
                    def update_progress(progress, message):
                        st.session_state.processing_progress = progress
                        with progress_container:
                            st.progress(progress)
                            st.write(message)
                    
                    # Calculate metrics with progress tracking
                    metrics = analyzer.calculate_all_metrics(progress_callback=update_progress)
                    
                    st.session_state.metrics = metrics
                    st.session_state.data_loaded = True
                    
                    # Clean up
                    with status_container:
                        st.info("Cleaning up temporary files...")
                    
                    # Optional: Keep files for future sessions
                    keep_files = st.checkbox("Keep uploaded files for faster reload", value=False)
                    if not keep_files:
                        try:
                            os.remove(onboarding_path)
                            os.remove(transaction_path)
                        except:
                            pass
                    
                    st.success("✅ Large files processed successfully!")
                    
                except Exception as e:
                    st.error(f"Error processing large files: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
        else:
            st.warning("Please upload both files to proceed")
    
    st.markdown("---")
    st.caption(f"© {datetime.now().year} APS Wallet. All rights reserved.")

# Main content
st.markdown("<h1 class='main-header'>APS WALLET - LARGE DATA ANALYTICS DASHBOARD</h1>", unsafe_allow_html=True)

if not st.session_state.data_loaded:
    # Welcome screen for large files
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=200)
        st.markdown("""
        ### Large File Analytics Platform
        
        **Features for 5GB+ files:**
        
        ✅ **Chunked Processing** - Process data in manageable chunks
        ✅ **Memory Efficient** - Optimized for large datasets
        ✅ **Parallel Processing** - Faster analysis with multiple cores
        ✅ **Optimized Formats** - Convert to Parquet for speed
        ✅ **Progress Tracking** - Real-time processing updates
        
        **To get started:**
        1. Upload your large files (up to 5GB each)
        2. Configure processing options
        3. Click 'Process Large Files'
        
        **Recommended for large files:**
        - Use Chunked Processing
        - Convert to Parquet format
        - Enable Parallel Processing if available
        """)
        
        # Show system requirements
        with st.expander("System Requirements"):
            st.write("""
            **Minimum Requirements:**
            - 8GB RAM (16GB recommended for 5GB files)
            - Multi-core processor
            - SSD storage recommended
            
            **Estimated Processing Times:**
            - 1GB file: 2-5 minutes
            - 5GB file: 10-30 minutes
            - Depends on system specifications
            """)
        
else:
    # Display metrics
    metrics = st.session_state.metrics
    analyzer = st.session_state.analyzer
    
    # Performance stats
    with st.expander("Processing Statistics"):
        col1, col2, col3, col4 = st.columns(4)
        
        if hasattr(analyzer, 'processing_stats'):
            stats = analyzer.processing_stats
            with col1:
                st.metric("Total Rows", f"{stats.get('total_rows', 0):,}")
            with col2:
                st.metric("Processing Time", f"{stats.get('processing_time', 0):.1f}s")
            with col3:
                st.metric("Memory Peak", f"{stats.get('memory_peak', 0):.1f} GB")
            with col4:
                st.metric("Chunks Processed", stats.get('chunks_processed', 1))
    
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
    
    # More metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        success_rate = (metrics['successful_transactions'] / 
                       (metrics['successful_transactions'] + metrics['failed_transactions']) * 100 
                       if (metrics['successful_transactions'] + metrics['failed_transactions']) > 0 else 0)
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
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Transactions</div>
            <div class="metric-value">{metrics['successful_transactions'] + metrics['failed_transactions']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_transaction = metrics.get('transaction_volume', 0) / max(1, metrics['successful_transactions'])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg Transaction</div>
            <div class="metric-value">${avg_transaction:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", 
        "👥 Agent Network", 
        "💰 Transactions", 
        "📊 Performance",
        "📥 Data Export"
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
            if hasattr(analyzer, 'get_agent_stats'):
                agent_stats = analyzer.get_agent_stats()
                if agent_stats is not None:
                    fig = px.bar(
                        agent_stats,
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
            # Transaction volume over time (if available)
            if hasattr(analyzer, 'get_daily_volume'):
                daily_volume = analyzer.get_daily_volume()
                if daily_volume is not None:
                    fig = px.line(
                        daily_volume.tail(30),
                        x='Date',
                        y='Transaction Amount',
                        title='Daily Transaction Volume (Last 30 Days)',
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        # Performance matrix
        if metrics.get('top_performing_agents'):
            top_agents = pd.DataFrame(metrics['top_performing_agents'])
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                fig = px.scatter(
                    top_agents.head(20),
                    x='Transaction_Count',
                    y='Total_Amount',
                    size='Total_Amount',
                    color='Total_Amount',
                    hover_name='User Identifier',
                    title='Agent Performance Matrix',
                    labels={
                        'Transaction_Count': 'Number of Transactions',
                        'Total_Amount': 'Total Volume ($)'
                    },
                    color_continuous_scale='sunset'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.dataframe(
                    top_agents.head(10)[['User Identifier', 'Total_Amount', 'Transaction_Count']]
                    .style.format({
                        'Total_Amount': '${:,.2f}',
                        'Transaction_Count': '{:,.0f}'
                    }),
                    use_container_width=True,
                    height=400
                )
    
    with tab5:
        # Large data export options
        st.markdown("### Export Options for Large Datasets")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            export_format = st.selectbox(
                "Export Format",
                ["Parquet (Recommended)", "CSV Chunked", "CSV Single", "Excel"]
            )
        
        with col2:
            sample_size = st.number_input(
                "Sample Size (rows)",
                min_value=1000,
                max_value=10000000,
                value=100000,
                step=10000,
                help="For large files, export a sample first"
            )
        
        with col3:
            compression = st.selectbox(
                "Compression",
                ["None", "gzip", "snappy", "brotli"]
            )
        
        # Export buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export Summary Data", use_container_width=True):
                summary_data = pd.DataFrame([
                    ('Total Active Agents', metrics['total_active_agents']),
                    ('Total Active Tellers', metrics['total_active_tellers']),
                    ('Agents with Tellers', metrics['agents_with_tellers']),
                    ('Agents without Tellers', metrics['agents_without_tellers']),
                    (f'{metrics["year"]} Onboarded Total', metrics['onboarded_total']),
                    (f'{metrics["year"]} Agents Onboarded', metrics['onboarded_agents']),
                    (f'{metrics["year"]} Tellers Onboarded', metrics['onboarded_tellers']),
                    ('Active Users', metrics['active_users_overall']),
                    ('Inactive Users', metrics['inactive_users_overall']),
                    ('Transaction Volume', metrics.get('transaction_volume', 0)),
                    ('Successful Transactions', metrics['successful_transactions']),
                    ('Failed Transactions', metrics['failed_transactions'])
                ], columns=['Metric', 'Value'])
                
                csv = summary_data.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"aps_wallet_summary_{selected_year}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col2:
            if st.button("Export Monthly Data", use_container_width=True):
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
        
        with col3:
            if st.button("Export Sample Data", use_container_width=True):
                if hasattr(analyzer, 'get_sample_data'):
                    sample_data = analyzer.get_sample_data(sample_size)
                    if export_format == "Parquet (Recommended)" and PARQUET_AVAILABLE:
                        # Export as Parquet
                        buffer = io.BytesIO()
                        sample_data.to_parquet(buffer, compression=compression if compression != "None" else None)
                        buffer.seek(0)
                        st.download_button(
                            label="Download Parquet",
                            data=buffer,
                            file_name=f"sample_data_{selected_year}.parquet",
                            mime="application/octet-stream",
                            use_container_width=True
                        )
                    else:
                        # Export as CSV
                        csv = sample_data.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"sample_data_{selected_year}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
        
        # Advanced export options
        with st.expander("Advanced Export Options"):
            st.write("For exporting full datasets (>1GB):")
            
            if st.button("Generate Export Job", use_container_width=True):
                st.info("Large export job started. You will be notified when ready.")
                # In a real implementation, this would queue a background job
                st.write("Export would be saved to: `/exports/large_export_{timestamp}/`")
