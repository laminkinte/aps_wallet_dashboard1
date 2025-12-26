import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Performance Metrics", page_icon="📈")

st.title("📈 Performance Metrics")

if st.session_state.data_loaded:
    metrics = st.session_state.metrics
    analyzer = st.session_state.analyzer
    
    # Transaction Performance
    st.markdown("### 💰 Transaction Performance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        success_rate = (metrics['successful_transactions'] / 
                       (metrics['successful_transactions'] + metrics['failed_transactions']) * 100 
                       if (metrics['successful_transactions'] + metrics['failed_transactions']) > 0 else 0)
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=success_rate,
            title={'text': "Success Rate"},
            gauge={
                'axis': {'range': [None, 100]},
                'steps': [
                    {'range': [0, 70], 'color': "lightgray"},
                    {'range': [70, 90], 'color': "gray"},
                    {'range': [90, 100], 'color': "darkgray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 95
                }
            }
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        avg_transaction = metrics['transaction_volume'] / max(1, metrics['successful_transactions'])
        
        fig = go.Figure(go.Indicator(
            mode="number",
            value=avg_transaction,
            title={'text': "Avg Transaction Value"},
            number={'prefix': "$", 'valueformat': ",.0f"}
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        transactions_per_agent = metrics['successful_transactions'] / max(1, metrics['total_active_agents'])
        
        fig = go.Figure(go.Indicator(
            mode="number",
            value=transactions_per_agent,
            title={'text': "Transactions per Agent"},
            number={'valueformat': ",.0f"}
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    # Transaction Volume Trend
    st.markdown("### 📊 Volume Analysis")
    
    if hasattr(analyzer, 'deposit_df') and not analyzer.deposit_df.empty:
        if 'Created At' in analyzer.deposit_df.columns and 'Transaction Amount' in analyzer.deposit_df.columns:
            deposit_df = analyzer.deposit_df.copy()
            
            # Convert Transaction Amount to numeric
            deposit_df['Transaction Amount'] = pd.to_numeric(
                deposit_df['Transaction Amount'], errors='coerce'
            )
            
            # Daily volume
            deposit_df['Date'] = deposit_df['Created At'].dt.date
            daily_volume = deposit_df.groupby('Date')['Transaction Amount'].sum().reset_index()
            
            fig = px.line(
                daily_volume.tail(30),  # Last 30 days
                x='Date',
                y='Transaction Amount',
                title='Daily Transaction Volume (Last 30 Days)',
                markers=True
            )
            fig.update_layout(
                yaxis_title="Volume ($)",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Performance Benchmarks
    st.markdown("### 🎯 Performance Benchmarks")
    
    # Create benchmark data
    benchmarks = {
        'Metric': [
            'Transaction Success Rate',
            'Agent Activation Rate',
            'Teller Utilization',
            'Volume Growth'
        ],
        'Current': [
            success_rate,
            (metrics['active_users_overall'] / (metrics['active_users_overall'] + metrics['inactive_users_overall']) * 100 
             if (metrics['active_users_overall'] + metrics['inactive_users_overall']) > 0 else 0),
            (metrics['agents_with_tellers'] / metrics['total_active_agents'] * 100 
             if metrics['total_active_agents'] > 0 else 0),
            min(100, (metrics['onboarded_total'] / 500) * 100)  # Assuming 500 as target
        ],
        'Target': [95, 80, 70, 100]
    }
    
    df_benchmarks = pd.DataFrame(benchmarks)
    df_benchmarks['Gap'] = df_benchmarks['Target'] - df_benchmarks['Current']
    df_benchmarks['Achievement'] = (df_benchmarks['Current'] / df_benchmarks['Target']) * 100
    
    # Display benchmarks
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Current',
        x=df_benchmarks['Metric'],
        y=df_benchmarks['Current'],
        marker_color='#636EFA'
    ))
    
    fig.add_trace(go.Bar(
        name='Target',
        x=df_benchmarks['Metric'],
        y=df_benchmarks['Target'],
        marker_color='lightgray',
        opacity=0.5
    ))
    
    fig.update_layout(
        title='Performance vs Targets',
        barmode='overlay',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance Matrix
    st.markdown("### 📈 Performance Matrix")
    
    # Create performance matrix data
    performance_data = []
    if metrics.get('top_performing_agents'):
        for agent in metrics['top_performing_agents'][:20]:
            performance_data.append({
                'Agent': agent['User Identifier'],
                'Volume': agent.get('Total_Amount', 0),
                'Transactions': agent.get('Transaction_Count', 0),
                'Avg per Transaction': agent.get('Total_Amount', 0) / max(1, agent.get('Transaction_Count', 0))
            })
    
    if performance_data:
        df_perf = pd.DataFrame(performance_data)
        
        fig = px.scatter(
            df_perf,
            x='Transactions',
            y='Volume',
            size='Avg per Transaction',
            color='Avg per Transaction',
            hover_name='Agent',
            title='Agent Performance Matrix',
            labels={
                'Transactions': 'Number of Transactions',
                'Volume': 'Total Volume ($)',
                'Avg per Transaction': 'Average Value ($)'
            },
            size_max=40
        )
        
        # Add quadrant lines
        median_transactions = df_perf['Transactions'].median()
        median_volume = df_perf['Volume'].median()
        
        fig.add_hline(y=median_volume, line_dash="dash", line_color="gray")
        fig.add_vline(x=median_transactions, line_dash="dash", line_color="gray")
        
        # Add quadrant labels
        fig.add_annotation(
            x=median_transactions/2,
            y=median_volume*1.5,
            text="High Value, Low Frequency",
            showarrow=False,
            font=dict(size=10)
        )
        
        fig.add_annotation(
            x=median_transactions*1.5,
            y=median_volume*1.5,
            text="High Performers",
            showarrow=False,
            font=dict(size=10)
        )
        
        fig.add_annotation(
            x=median_transactions/2,
            y=median_volume/2,
            text="Low Performers",
            showarrow=False,
            font=dict(size=10)
        )
        
        fig.add_annotation(
            x=median_transactions*1.5,
            y=median_volume/2,
            text="High Frequency, Low Value",
            showarrow=False,
            font=dict(size=10)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
else:
    st.info("👈 Please upload data files in the main page to view performance metrics.")