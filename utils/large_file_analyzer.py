import pandas as pd
import numpy as np
from datetime import datetime
import warnings
from typing import Dict, List, Optional, Callable
import time
import os
import psutil
import gc
from pathlib import Path
warnings.filterwarnings('ignore')

class AnalysisConfig:
    """Configuration for large file analyzer"""
    def __init__(self, year: int = 2025, min_deposits_for_active: int = 20):
        self.year = year
        self.min_deposits_for_active = min_deposits_for_active
        self.deposit_keywords = ['DEPOSIT', 'FUNDING', 'LOAD', 'CREDIT']

class LargeFileAnalyzer:
    """Analyzer optimized for large files (up to 5GB+)"""
    
    def __init__(self, 
                 onboarding_path: str = None,
                 transaction_path: str = None,
                 config: AnalysisConfig = None,
                 use_chunked: bool = True,
                 use_parallel: bool = False,
                 chunk_size: int = 1000000):
        
        self.onboarding_path = onboarding_path
        self.transaction_path = transaction_path
        self.config = config or AnalysisConfig()
        self.use_chunked = use_chunked
        self.use_parallel = use_parallel
        self.chunk_size = chunk_size
        
        # Data storage
        self.onboarding_df = None
        self.transaction_chunks = []
        self.deposit_chunks = []
        
        # Statistics
        self.processing_stats = {
            'start_time': None,
            'end_time': None,
            'memory_peak': 0,
            'chunks_processed': 0,
            'total_rows': 0
        }
        
        # Cache for results
        self._results_cache = None
    
    def _update_memory_stats(self):
        """Update memory usage statistics"""
        memory_gb = psutil.Process().memory_info().rss / (1024 ** 3)
        self.processing_stats['memory_peak'] = max(
            self.processing_stats['memory_peak'], memory_gb
        )
        return memory_gb
    
    def _read_file_chunks(self, file_path: str, dtype_dict: dict = None, 
                         usecols: list = None, progress_callback: Callable = None):
        """Read large file in chunks with memory optimization"""
        chunks = []
        total_chunks = 0
        
        # Estimate total chunks
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            # Rough estimate: 100 bytes per row
            estimated_rows = file_size / 100
            total_chunks = int(np.ceil(estimated_rows / self.chunk_size))
        
        # Read in chunks
        chunk_iterator = pd.read_csv(
            file_path,
            chunksize=self.chunk_size,
            dtype=dtype_dict,
            usecols=usecols,
            low_memory=False
        ) if file_path.endswith('.csv') else pd.read_parquet(
            file_path,
            chunksize=self.chunk_size
        )
        
        for i, chunk in enumerate(chunk_iterator):
            # Update progress
            if progress_callback:
                progress = (i + 1) / max(total_chunks, 1)
                progress_callback(progress, f"Processing chunk {i+1}...")
            
            # Clean memory
            self._update_memory_stats()
            if i % 10 == 0:
                gc.collect()
            
            chunks.append(chunk)
            self.processing_stats['chunks_processed'] += 1
            self.processing_stats['total_rows'] += len(chunk)
        
        return chunks
    
    def preprocess_onboarding_data(self, progress_callback: Callable = None):
        """Preprocess onboarding data"""
        if progress_callback:
            progress_callback(0.1, "Loading onboarding data...")
        
        # Define columns needed
        usecols = ['Account ID', 'Entity', 'Status', 'Registration Date']
        dtype_dict = {
            'Account ID': 'string',
            'Entity': 'string',
            'Status': 'string',
            'Registration Date': 'string'
        }
        
        if self.use_chunked and os.path.getsize(self.onboarding_path) > 100 * 1024 * 1024:  # >100MB
            # Read in chunks
            chunks = self._read_file_chunks(
                self.onboarding_path, 
                dtype_dict=dtype_dict,
                usecols=usecols,
                progress_callback=lambda p, m: progress_callback(0.1 + p * 0.3, m) if progress_callback else None
            )
            
            # Combine chunks
            self.onboarding_df = pd.concat(chunks, ignore_index=True)
        else:
            # Read entire file
            if self.onboarding_path.endswith('.csv'):
                self.onboarding_df = pd.read_csv(
                    self.onboarding_path,
                    usecols=usecols,
                    dtype=dtype_dict,
                    low_memory=False
                )
            else:
                self.onboarding_df = pd.read_parquet(self.onboarding_path)
        
        # Clean data
        if progress_callback:
            progress_callback(0.5, "Cleaning onboarding data...")
        
        self.onboarding_df['Entity'] = self.onboarding_df['Entity'].str.upper().str.strip()
        self.onboarding_df['Status'] = self.onboarding_df['Status'].str.upper().str.strip()
        self.onboarding_df['Account ID'] = self.onboarding_df['Account ID'].str.strip()
        
        # Parse dates
        self.onboarding_df['Registration Date'] = pd.to_datetime(
            self.onboarding_df['Registration Date'],
            errors='coerce'
        )
        
        if progress_callback:
            progress_callback(0.6, "Onboarding data processed")
    
    def preprocess_transaction_data(self, progress_callback: Callable = None):
        """Preprocess transaction data with chunked processing"""
        if progress_callback:
            progress_callback(0.6, "Loading transaction data...")
        
        # Define columns needed
        needed_cols = [
            'User Identifier', 'Parent User Identifier', 'Entity Name',
            'Service Name', 'Transaction Type', 'Product Name',
            'Created At', 'Transaction Amount', 'Transaction Status'
        ]
        
        # Read in chunks for large files
        if self.use_chunked:
            chunk_num = 0
            transaction_chunks = []
            deposit_chunks = []
            
            # Estimate total file size for progress
            file_size_mb = os.path.getsize(self.transaction_path) / (1024 ** 2)
            estimated_chunks = max(1, int(file_size_mb / 100))  # 100MB per chunk
            
            # Read file in chunks
            chunk_iterator = pd.read_csv(
                self.transaction_path,
                chunksize=self.chunk_size,
                usecols=needed_cols,
                low_memory=False
            ) if self.transaction_path.endswith('.csv') else pd.read_parquet(
                self.transaction_path,
                chunksize=self.chunk_size
            )
            
            for chunk in chunk_iterator:
                chunk_num += 1
                
                # Update progress
                if progress_callback:
                    progress = 0.6 + (chunk_num / estimated_chunks) * 0.3
                    progress_callback(progress, f"Processing transaction chunk {chunk_num}...")
                
                # Clean and process chunk
                processed_chunk = self._process_transaction_chunk(chunk)
                if processed_chunk is not None:
                    transaction_chunks.append(processed_chunk)
                
                # Identify deposits
                deposit_chunk = self._extract_deposits_from_chunk(chunk)
                if deposit_chunk is not None:
                    deposit_chunks.append(deposit_chunk)
                
                # Clean memory
                self._update_memory_stats()
                if chunk_num % 5 == 0:
                    gc.collect()
            
            # Combine chunks
            if transaction_chunks:
                self.transaction_chunks = transaction_chunks
            
            if deposit_chunks:
                self.deposit_chunks = deposit_chunks
        
        else:
            # Read entire file (for smaller files)
            if self.transaction_path.endswith('.csv'):
                df = pd.read_csv(
                    self.transaction_path,
                    usecols=needed_cols,
                    low_memory=False
                )
            else:
                df = pd.read_parquet(self.transaction_path)
            
            # Process and store
            processed_df = self._process_transaction_chunk(df)
            if processed_df is not None:
                self.transaction_chunks = [processed_df]
            
            deposit_df = self._extract_deposits_from_chunk(df)
            if deposit_df is not None:
                self.deposit_chunks = [deposit_df]
        
        if progress_callback:
            progress_callback(0.9, "Transaction data processed")
    
    def _process_transaction_chunk(self, chunk: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Process a single transaction chunk"""
        try:
            # Clean text columns
            text_cols = ['Entity Name', 'Service Name', 'Transaction Type', 'Product Name']
            for col in text_cols:
                if col in chunk.columns:
                    chunk[col] = chunk[col].str.upper().str.strip()
            
            # Parse dates
            if 'Created At' in chunk.columns:
                chunk['Created At'] = pd.to_datetime(chunk['Created At'], errors='coerce')
                chunk['Year'] = chunk['Created At'].dt.year
                chunk['Month'] = chunk['Created At'].dt.month
            
            # Filter for current year
            if 'Year' in chunk.columns:
                chunk = chunk[chunk['Year'] == self.config.year].copy()
            
            return chunk if not chunk.empty else None
            
        except Exception as e:
            print(f"Error processing chunk: {e}")
            return None
    
    def _extract_deposits_from_chunk(self, chunk: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Extract deposit transactions from a chunk"""
        try:
            deposit_mask = pd.Series(False, index=chunk.index)
            
            for keyword in self.config.deposit_keywords:
                for col in ['Service Name', 'Transaction Type', 'Product Name']:
                    if col in chunk.columns:
                        mask = chunk[col].str.contains(keyword, na=False, case=False)
                        deposit_mask = deposit_mask | mask
            
            if deposit_mask.any():
                deposit_chunk = chunk[deposit_mask].copy()
                
                # Add month column if not present
                if 'Created At' in deposit_chunk.columns and 'Month' not in deposit_chunk.columns:
                    deposit_chunk['Month'] = deposit_chunk['Created At'].dt.month
                
                return deposit_chunk
            
            return None
            
        except Exception as e:
            print(f"Error extracting deposits: {e}")
            return None
    
    def calculate_all_metrics(self, progress_callback: Callable = None) -> Dict:
        """Calculate all metrics with memory optimization"""
        self.processing_stats['start_time'] = time.time()
        
        if progress_callback:
            progress_callback(0, "Starting analysis...")
        
        # Preprocess data
        self.preprocess_onboarding_data(
            lambda p, m: progress_callback(p * 0.3, m) if progress_callback else None
        )
        
        self.preprocess_transaction_data(
            lambda p, m: progress_callback(0.3 + p * 0.4, m) if progress_callback else None
        )
        
        # Calculate metrics
        if progress_callback:
            progress_callback(0.7, "Calculating metrics...")
        
        results = self._calculate_metrics()
        
        # Finalize
        self.processing_stats['end_time'] = time.time()
        self.processing_stats['processing_time'] = (
            self.processing_stats['end_time'] - self.processing_stats['start_time']
        )
        
        if progress_callback:
            progress_callback(1.0, "Analysis complete!")
        
        return results
    
    def _calculate_metrics(self) -> Dict:
        """Calculate metrics from processed data"""
        results = {
            'year': self.config.year,
            'total_active_agents': 0,
            'total_active_tellers': 0,
            'agents_with_tellers': 0,
            'agents_without_tellers': 0,
            'onboarded_total': 0,
            'onboarded_agents': 0,
            'onboarded_tellers': 0,
            'active_users_overall': 0,
            'inactive_users_overall': 0,
            'monthly_active_users': {m: 0 for m in range(1, 13)},
            'monthly_deposits': {m: 0 for m in range(1, 13)},
            'transaction_volume': 0.0,
            'successful_transactions': 0,
            'failed_transactions': 0,
            'top_performing_agents': []
        }
        
        # Calculate from onboarding data
        if self.onboarding_df is not None:
            terminated_status = {'TERMINATED', 'BLOCKED', 'SUSPENDED', 'INACTIVE'}
            active_mask = ~self.onboarding_df['Status'].isin(terminated_status)
            df_active = self.onboarding_df[active_mask]
            
            # Entity counts
            if 'Entity' in df_active.columns:
                entity_counts = df_active['Entity'].value_counts()
                results['total_active_agents'] = entity_counts.get('AGENT', 0)
                results['total_active_tellers'] = entity_counts.get('AGENT TELLER', 0)
            
            # Onboarding in current year
            if 'Registration Date' in self.onboarding_df.columns:
                mask_year = (
                    self.onboarding_df['Registration Date'].dt.year == self.config.year
                ) & active_mask
                df_onboarded = self.onboarding_df[mask_year]
                results['onboarded_total'] = len(df_onboarded)
                
                if 'Entity' in df_onboarded.columns:
                    onboarded_counts = df_onboarded['Entity'].value_counts()
                    results['onboarded_agents'] = onboarded_counts.get('AGENT', 0)
                    results['onboarded_tellers'] = onboarded_counts.get('AGENT TELLER', 0)
        
        # Calculate from transaction chunks
        if self.transaction_chunks:
            # Aggregate across chunks
            total_volume = 0
            successful = 0
            failed = 0
            
            for chunk in self.transaction_chunks:
                # Transaction volume
                if 'Transaction Amount' in chunk.columns:
                    try:
                        chunk['Transaction Amount'] = pd.to_numeric(
                            chunk['Transaction Amount'], errors='coerce'
                        )
                        total_volume += chunk['Transaction Amount'].sum()
                    except:
                        pass
                
                # Transaction status
                if 'Transaction Status' in chunk.columns:
                    status_counts = chunk['Transaction Status'].value_counts()
                    successful += status_counts.get('SUCCESS', 0) + status_counts.get('COMPLETED', 0)
                    failed += status_counts.get('FAILED', 0) + status_counts.get('REJECTED', 0)
            
            results['transaction_volume'] = total_volume
            results['successful_transactions'] = successful
            results['failed_transactions'] = failed
        
        # Calculate from deposit chunks
        if self.deposit_chunks:
            # Combine deposit chunks for analysis
            all_deposits = pd.concat(self.deposit_chunks, ignore_index=True) if len(self.deposit_chunks) > 1 else self.deposit_chunks[0]
            
            # Agent with tellers
            if 'Parent User Identifier' in all_deposits.columns:
                parent_ids = all_deposits['Parent User Identifier'].dropna().astype(str).unique()
                results['agents_with_tellers'] = len(set(parent_ids))
                
                # Calculate agents without tellers
                results['agents_without_tellers'] = max(
                    0, results['total_active_agents'] - results['agents_with_tellers']
                )
            
            # Active users
            if 'User Identifier' in all_deposits.columns:
                deposit_counts = all_deposits['User Identifier'].value_counts()
                results['active_users_overall'] = len(deposit_counts[
                    deposit_counts >= self.config.min_deposits_for_active
                ])
                results['inactive_users_overall'] = len(deposit_counts[
                    deposit_counts < self.config.min_deposits_for_active
                ])
            
            # Monthly deposits
            if 'Month' in all_deposits.columns:
                for month in range(1, 13):
                    month_mask = all_deposits['Month'] == month
                    results['monthly_deposits'][month] = len(all_deposits[month_mask])
            
            # Monthly active users
            if 'Month' in all_deposits.columns and 'User Identifier' in all_deposits.columns:
                for month in range(1, 13):
                    month_mask = all_deposits['Month'] == month
                    month_deposits = all_deposits[month_mask]
                    if not month_deposits.empty:
                        month_counts = month_deposits['User Identifier'].value_counts()
                        results['monthly_active_users'][month] = len(month_counts[
                            month_counts >= self.config.min_deposits_for_active
                        ])
            
            # Top performing agents
            if 'Transaction Amount' in all_deposits.columns and 'User Identifier' in all_deposits.columns:
                try:
                    all_deposits['Transaction Amount'] = pd.to_numeric(
                        all_deposits['Transaction Amount'], errors='coerce'
                    )
                    
                    agent_deposits = all_deposits.groupby('User Identifier').agg({
                        'Transaction Amount': ['sum', 'count']
                    }).round(2)
                    
                    agent_deposits.columns = ['Total_Amount', 'Transaction_Count']
                    agent_deposits = agent_deposits.sort_values('Total_Amount', ascending=False)
                    results['top_performing_agents'] = agent_deposits.head(10).reset_index().to_dict('records')
                    
                except Exception as e:
                    print(f"Error calculating top agents: {e}")
        
        return results
    
    def get_agent_stats(self):
        """Get agent statistics"""
        if self.onboarding_df is not None and 'Status' in self.onboarding_df.columns:
            status_counts = self.onboarding_df['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            return status_counts
        return None
    
    def get_daily_volume(self, days: int = 30):
        """Get daily transaction volume for the last N days"""
        if not self.transaction_chunks:
            return None
        
        # Combine recent chunks
        all_transactions = pd.concat(self.transaction_chunks, ignore_index=True)
        
        if 'Created At' not in all_transactions.columns or 'Transaction Amount' not in all_transactions.columns:
            return None
        
        # Filter for recent dates
        recent_date = datetime.now() - timedelta(days=days)
        recent_transactions = all_transactions[all_transactions['Created At'] >= recent_date]
        
        if recent_transactions.empty:
            return None
        
        # Group by date
        recent_transactions['Date'] = recent_transactions['Created At'].dt.date
        daily_volume = recent_transactions.groupby('Date')['Transaction Amount'].sum().reset_index()
        
        return daily_volume
    
    def get_sample_data(self, sample_size: int = 100000):
        """Get sample data for export"""
        if not self.transaction_chunks:
            return pd.DataFrame()
        
        # Combine chunks and take sample
        all_data = pd.concat(self.transaction_chunks, ignore_index=True)
        
        if len(all_data) > sample_size:
            return all_data.sample(n=sample_size, random_state=42)
        else:
            return all_data
    
    def cleanup(self):
        """Clean up memory and temporary files"""
        self.onboarding_df = None
        self.transaction_chunks = []
        self.deposit_chunks = []
        self._results_cache = None
        gc.collect()
