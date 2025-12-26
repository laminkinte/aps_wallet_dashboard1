import pandas as pd
import numpy as np
from datetime import datetime
import warnings
from typing import Dict, List, Set, Tuple, Optional
import time
import streamlit as st
from dataclasses import dataclass
import json

warnings.filterwarnings('ignore')

@dataclass
class AnalysisConfig:
    """Configuration for the analyzer"""
    year: int = 2025
    min_deposits_for_active: int = 20
    deposit_keywords: List[str] = None
    
    def __post_init__(self):
        if self.deposit_keywords is None:
            self.deposit_keywords = ['DEPOSIT', 'FUNDING', 'LOAD', 'CREDIT']

class AgentPerformanceAnalyzerUltraFast:
    def __init__(self, onboarding_df: pd.DataFrame = None, transaction_df: pd.DataFrame = None, config: AnalysisConfig = None):
        """
        Initialize the analyzer with dataframes
        """
        self.onboarding_df = onboarding_df
        self.transaction_df = transaction_df
        self.config = config or AnalysisConfig()
        self.start_time = time.time()
        self._processed_data = {}
        
    def set_data(self, onboarding_df: pd.DataFrame, transaction_df: pd.DataFrame):
        """Set data after initialization"""
        self.onboarding_df = onboarding_df
        self.transaction_df = transaction_df
        
    def load_and_preprocess_data(self, onboarding_file: str = None, transaction_file: str = None) -> None:
        """
        Load and preprocess data with optimization
        """
        if onboarding_file:
            self.onboarding_df = self._load_onboarding_data(onboarding_file)
        
        if transaction_file:
            self.transaction_df, self.deposit_df = self._load_transaction_data(transaction_file)
            
    def _load_onboarding_data(self, file_path: str) -> pd.DataFrame:
        """Load onboarding data efficiently"""
        try:
            df = pd.read_csv(
                file_path,
                usecols=['Account ID', 'Entity', 'Status', 'Registration Date'],
                dtype={
                    'Account ID': 'string',
                    'Entity': 'string',
                    'Status': 'string',
                    'Registration Date': 'string'
                },
                engine='c'
            )
        except:
            df = pd.read_csv(file_path, dtype=str)
            required_cols = ['Account ID', 'Entity', 'Status', 'Registration Date']
            for col in required_cols:
                if col not in df.columns:
                    st.error(f"Missing column: {col}")
                    return pd.DataFrame()
            
        # Clean data
        df['Entity'] = df['Entity'].str.upper().str.strip()
        df['Status'] = df['Status'].str.upper().str.strip()
        df['Account ID'] = df['Account ID'].str.strip()
        df['Registration Date'] = pd.to_datetime(
            df['Registration Date'],
            format='%d/%m/%Y %H:%M',
            errors='coerce'
        )
        
        return df
    
    def _load_transaction_data(self, file_path: str, sample_size: int = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load transaction data efficiently"""
        needed_cols = [
            'User Identifier', 'Parent User Identifier', 'Entity Name',
            'Service Name', 'Transaction Type', 'Product Name',
            'Created At', 'Transaction Amount', 'Transaction Status'
        ]
        
        # Read only needed columns
        try:
            dtype_dict = {col: 'string' for col in needed_cols}
            if sample_size:
                df = pd.read_csv(file_path, usecols=needed_cols, dtype=dtype_dict, nrows=sample_size)
            else:
                df = pd.read_csv(file_path, usecols=needed_cols, dtype=dtype_dict)
        except:
            df = pd.read_csv(file_path, dtype=str)
            # Filter to needed columns
            available_cols = [col for col in needed_cols if col in df.columns]
            df = df[available_cols]
        
        # Parse dates
        if 'Created At' in df.columns:
            df['Created At'] = pd.to_datetime(df['Created At'], errors='coerce')
            df['Year'] = df['Created At'].dt.year
            df['Month'] = df['Created At'].dt.month
            df['Day'] = df['Created At'].dt.day
            df['Hour'] = df['Created At'].dt.hour
        
        # Clean text columns
        text_cols = ['Entity Name', 'Service Name', 'Transaction Type', 'Product Name']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].str.upper().str.strip()
        
        # Identify deposits
        deposit_df = pd.DataFrame()
        if not df.empty:
            deposit_mask = pd.Series(False, index=df.index)
            for keyword in self.config.deposit_keywords:
                for col in ['Service Name', 'Transaction Type', 'Product Name']:
                    if col in df.columns:
                        mask = df[col].str.contains(keyword, na=False, case=False)
                        deposit_mask = deposit_mask | mask
            
            if deposit_mask.any():
                deposit_df = df[deposit_mask].copy()
        
        # Filter for current year
        current_year_df = df[df['Year'] == self.config.year].copy() if 'Year' in df.columns else pd.DataFrame()
        
        return current_year_df, deposit_df
    
    def calculate_all_metrics(self) -> Dict:
        """
        Calculate all metrics with caching
        """
        cache_key = f"metrics_{hash(str(self.onboarding_df) + str(self.transaction_df))}"
        
        if cache_key in self._processed_data:
            return self._processed_data[cache_key]
        
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
            'avg_transaction_time_minutes': 0.0,
            'transaction_volume': 0.0,
            'successful_transactions': 0,
            'failed_transactions': 0,
            'agent_hierarchy': {},
            'top_performing_agents': [],
            'performance_metrics': {}
        }
        
        if self.onboarding_df is None or self.transaction_df is None:
            return results
        
        # Calculate metrics
        results.update(self._calculate_agent_metrics())
        results.update(self._calculate_transaction_metrics())
        results.update(self._calculate_performance_metrics())
        
        self._processed_data[cache_key] = results
        return results
    
    def _calculate_agent_metrics(self) -> Dict:
        """Calculate agent-related metrics"""
        metrics = {}
        
        terminated_status = {'TERMINATED', 'BLOCKED', 'SUSPENDED', 'INACTIVE'}
        active_mask = ~self.onboarding_df['Status'].isin(terminated_status)
        df_active = self.onboarding_df[active_mask]
        
        # Entity counts
        entity_counts = df_active['Entity'].value_counts()
        metrics['total_active_agents'] = entity_counts.get('AGENT', 0)
        metrics['total_active_tellers'] = entity_counts.get('AGENT TELLER', 0)
        
        # Onboarding in current year
        mask_2025 = (
            self.onboarding_df['Registration Date'].dt.year == self.config.year
        ) & active_mask
        df_onboarded = self.onboarding_df[mask_2025]
        metrics['onboarded_total'] = len(df_onboarded)
        
        onboarded_counts = df_onboarded['Entity'].value_counts()
        metrics['onboarded_agents'] = onboarded_counts.get('AGENT', 0)
        metrics['onboarded_tellers'] = onboarded_counts.get('AGENT TELLER', 0)
        
        return metrics
    
    def _calculate_transaction_metrics(self) -> Dict:
        """Calculate transaction-related metrics"""
        metrics = {
            'transaction_volume': 0,
            'successful_transactions': 0,
            'failed_transactions': 0,
            'monthly_deposits': {m: 0 for m in range(1, 13)}
        }
        
        if self.transaction_df is None or self.transaction_df.empty:
            return metrics
        
        # Transaction volume
        if 'Transaction Amount' in self.transaction_df.columns:
            try:
                self.transaction_df['Transaction Amount'] = pd.to_numeric(
                    self.transaction_df['Transaction Amount'], errors='coerce'
                )
                metrics['transaction_volume'] = self.transaction_df['Transaction Amount'].sum()
            except:
                pass
        
        # Transaction status
        if 'Transaction Status' in self.transaction_df.columns:
            status_counts = self.transaction_df['Transaction Status'].value_counts()
            metrics['successful_transactions'] = status_counts.get('SUCCESS', 0) + status_counts.get('COMPLETED', 0)
            metrics['failed_transactions'] = status_counts.get('FAILED', 0) + status_counts.get('REJECTED', 0)
        
        # Monthly deposits
        if hasattr(self, 'deposit_df') and not self.deposit_df.empty:
            for month in range(1, 13):
                month_mask = self.deposit_df['Month'] == month
                metrics['monthly_deposits'][month] = len(self.deposit_df[month_mask])
        
        return metrics
    
    def _calculate_performance_metrics(self) -> Dict:
        """Calculate performance metrics"""
        metrics = {
            'performance_metrics': {},
            'top_performing_agents': [],
            'agent_hierarchy': {}
        }
        
        # Calculate agent-teller relationships
        if hasattr(self, 'deposit_df') and not self.deposit_df.empty:
            # Agent with tellers
            parent_ids = self.deposit_df['Parent User Identifier'].dropna().astype(str).unique()
            metrics['agents_with_tellers'] = len(set(parent_ids))
            
            # Get active agents from onboarding
            active_agents = set(self.onboarding_df[
                (self.onboarding_df['Entity'] == 'AGENT') & 
                (~self.onboarding_df['Status'].isin({'TERMINATED', 'BLOCKED', 'SUSPENDED', 'INACTIVE'}))
            ]['Account ID'].astype(str))
            
            metrics['agents_without_tellers'] = max(0, len(active_agents) - metrics['agents_with_tellers'])
            
            # Active users based on deposits
            deposit_counts = self.deposit_df['User Identifier'].value_counts()
            metrics['active_users_overall'] = len(deposit_counts[deposit_counts >= self.config.min_deposits_for_active])
            metrics['inactive_users_overall'] = len(deposit_counts[deposit_counts < self.config.min_deposits_for_active])
            
            # Monthly active users
            for month in range(1, 13):
                month_mask = self.deposit_df['Month'] == month
                month_deposits = self.deposit_df[month_mask]
                if not month_deposits.empty:
                    month_counts = month_deposits['User Identifier'].value_counts()
                    metrics['monthly_active_users'][month] = len(month_counts[
                        month_counts >= self.config.min_deposits_for_active
                    ])
            
            # Top performing agents
            if 'Transaction Amount' in self.deposit_df.columns:
                agent_deposits = self.deposit_df.groupby('User Identifier').agg({
                    'Transaction Amount': ['sum', 'count']
                }).round(2)
                agent_deposits.columns = ['Total_Amount', 'Transaction_Count']
                agent_deposits = agent_deposits.sort_values('Total_Amount', ascending=False)
                metrics['top_performing_agents'] = agent_deposits.head(10).reset_index().to_dict('records')
        
        return metrics
    
    def get_monthly_dataframe(self) -> pd.DataFrame:
        """Get monthly data as DataFrame"""
        metrics = self.calculate_all_metrics()
        
        months = []
        for m in range(1, 13):
            months.append({
                'Month': datetime(self.config.year, m, 1).strftime('%B'),
                'Month_Number': m,
                'Active_Users': metrics['monthly_active_users'].get(m, 0),
                'Deposit_Count': metrics['monthly_deposits'].get(m, 0)
            })
        
        return pd.DataFrame(months)
    
    def get_summary_dataframe(self) -> pd.DataFrame:
        """Get summary as DataFrame"""
        metrics = self.calculate_all_metrics()
        
        summary_data = [
            ('Total Active Agents', metrics['total_active_agents'], '👥'),
            ('Total Active Tellers', metrics['total_active_tellers'], '👥'),
            ('Agents with Tellers', metrics['agents_with_tellers'], '🤝'),
            ('Agents without Tellers', metrics['agents_without_tellers'], '❌'),
            ('Total Onboarded', metrics['onboarded_total'], '📥'),
            ('Agents Onboarded', metrics['onboarded_agents'], '👤'),
            ('Tellers Onboarded', metrics['onboarded_tellers'], '👥'),
            ('Active Users (≥20 deposits)', metrics['active_users_overall'], '✅'),
            ('Inactive Users (<20 deposits)', metrics['inactive_users_overall'], '❌'),
            ('Transaction Volume', f"${metrics['transaction_volume']:,.2f}", '💰'),
            ('Successful Transactions', metrics['successful_transactions'], '✅'),
            ('Failed Transactions', metrics['failed_transactions'], '❌'),
            ('Avg Transaction Time', f"{metrics.get('avg_transaction_time_minutes', 0):.2f} min", '⏱️')
        ]
        
        return pd.DataFrame(summary_data, columns=['Metric', 'Value', 'Icon'])
    
    def get_raw_data_for_export(self) -> Dict[str, pd.DataFrame]:
        """Get all raw data for export"""
        return {
            'onboarding_data': self.onboarding_df,
            'transaction_data': self.transaction_df,
            'deposit_data': getattr(self, 'deposit_df', pd.DataFrame()),
            'monthly_summary': self.get_monthly_dataframe(),
            'agent_summary': self.get_summary_dataframe()
        }