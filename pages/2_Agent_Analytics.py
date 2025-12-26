import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Agent Analytics", page_icon="👥")

st.title("👥 Agent Network Analytics")

if st.session_state.data_loaded:
    metrics = st.session_state.metrics
    analyzer = st.session_state.analyzer
    
    # Agent Distribution Analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # Agent status breakdown
        if analyzer.onboarding_df is not None:
            status_df = analyzer.onboarding_df['Status'].value_counts().reset_index()
            status_df.columns = ['Status', 'Count']
            
            fig = px.pie(
                status_df,
                values='Count',
                names='Status',
                title='Agent Status Distribution',
                hole=0.3
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Entity type distribution
        entity_counts = {
            'Agents': metrics['total_active_agents'],
            'Agent Tellers': metrics['total_active_tellers']
        }
        
        fig = px.bar(
            x=list(entity_counts.keys()),
            y=list(entity_counts.values()),
            title='Active Entity Distribution',
            labels={'x': 'Entity Type', 'y': 'Count'},
            color=list(entity_counts.values()),
            color_continuous_scale='tealrose'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Network Analysis
    st.markdown("### 🤝 Network Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Agent-Teller relationship
        rel_data = pd.DataFrame({
            'Category': ['With Tellers', 'Without Tellers'],
            'Count': [metrics['agents_with_tellers'], metrics['agents_without_tellers']]
        })
        
        fig = px.bar(
            rel_data,
            x='Category',
            y='Count',
            title='Agent-Teller Relationships',
            color='Count',
            text='Count'
        )
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Network efficiency
        efficiency_data = {
            'Metric': ['Agents per Teller', 'Avg Teller per Agent'],
            'Value': [
                metrics['total_active_agents'] / max(1, metrics['total_active_tellers']),
                metrics['total_active_tellers'] / max(1, metrics['agents_with_tellers'])
            ]
        }
        
        df_efficiency = pd.DataFrame(efficiency_data)
        
        fig = px.bar(
            df_efficiency,
            x='Metric',
            y='Value',
            title='Network Efficiency Metrics',
            text='Value'
        )
        fig.update_traces(
            texttemplate='%{y:.1f}',
            textposition='outside',
            marker_color=['#636EFA', '#EF553B']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Onboarding Trends
    st.markdown("### 📥 Onboarding Analysis")
    
    if analyzer.onboarding_df is not None and 'Registration Date' in analyzer.onboarding_df.columns:
        # Monthly onboarding trend
        onboarding_df = analyzer.onboarding_df.copy()
        onboarding_df['Registration Month'] = onboarding_df['Registration Date'].dt.to_period('M').astype(str)
        
        monthly_onboarding = onboarding_df.groupby('Registration Month').size().reset_index()
        monthly_onboarding.columns = ['Month', 'Count']
        
        fig = px.line(
            monthly_onboarding.tail(12),  # Last 12 months
            x='Month',
            y='Count',
            title='Monthly Onboarding Trend',
            markers=True,
            line_shape='spline'
        )
        fig.update_traces(line=dict(width=3))
        st.plotly_chart(fig, use_container_width=True)
    
    # Agent Performance Ranking
    st.markdown("### 🏆 Top Performing Agents")
    
    if metrics.get('top_performing_agents'):
        top_agents = pd.DataFrame(metrics['top_performing_agents'])
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            fig = px.bar(
                top_agents.head(10),
                x='User Identifier',
                y='Total_Amount',
                title='Top 10 Agents by Transaction Volume',
                color='Transaction_Count',
                labels={
                    'Total_Amount': 'Total Volume ($)',
                    'Transaction_Count': 'Number of Transactions'
                }
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(
                top_agents.head(5)[['User Identifier', 'Total_Amount', 'Transaction_Count']]
                .style.format({
                    'Total_Amount': '${:,.2f}',
                    'Transaction_Count': '{:,.0f}'
                }),
                use_container_width=True
            )
    
    # Geographic Distribution (Placeholder)
    st.markdown("### 🌍 Geographic Distribution")
    
    # Create sample geographic data
    regions = ['North', 'South', 'East', 'West', 'Central']
    agent_distribution = {
        'Region': regions * 2,
        'Entity Type': ['Agents'] * 5 + ['Tellers'] * 5,
        'Count': [
            metrics['total_active_agents'] * 0.3,
            metrics['total_active_agents'] * 0.25,
            metrics['total_active_agents'] * 0.2,
            metrics['total_active_agents'] * 0.15,
            metrics['total_active_agents'] * 0.1,
            metrics['total_active_tellers'] * 0.35,
            metrics['total_active_tellers'] * 0.25,
            metrics['total_active_tellers'] * 0.2,
            metrics['total_active_tellers'] * 0.15,
            metrics['total_active_tellers'] * 0.05
        ]
    }
    
    df_geo = pd.DataFrame(agent_distribution)
    
    fig = px.bar(
        df_geo,
        x='Region',
        y='Count',
        color='Entity Type',
        title='Regional Distribution of Agents & Tellers',
        barmode='group',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    st.plotly_chart(fig, use_container_width=True)
    
else:
    st.info("👈 Please upload data files in the main page to view agent analytics.")