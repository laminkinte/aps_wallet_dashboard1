import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Overview", page_icon="📊")

st.title("📊 Executive Overview")

if st.session_state.data_loaded:
    metrics = st.session_state.metrics
    analyzer = st.session_state.analyzer
    
    # Executive Summary
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Key Insights
        
        This dashboard provides a comprehensive overview of APS Wallet's 
        agent network performance for the selected year. Key metrics include:
        
        - **Agent Network Growth**: Track onboarding and active status
        - **Transaction Performance**: Monitor success rates and volumes
        - **Agent Productivity**: Analyze teller relationships and activity
        - **Trend Analysis**: Identify monthly patterns and growth opportunities
        """)
    
    with col2:
        st.metric("Year Analyzed", metrics['year'])
        st.metric("Data Processed", "✓ Complete")
        st.metric("Last Updated", st.session_state.get('last_update', 'Now'))
    
    # Performance Scorecard
    st.markdown("### 🎯 Performance Scorecard")
    
    # Calculate scores (0-100)
    scores = {
        'Agent Growth': min(100, (metrics['onboarded_total'] / 1000) * 100),
        'Network Coverage': min(100, (metrics['agents_with_tellers'] / metrics['total_active_agents'] * 100) 
                               if metrics['total_active_agents'] > 0 else 0),
        'Transaction Success': min(100, (metrics['successful_transactions'] / 
                                        (metrics['successful_transactions'] + metrics['failed_transactions']) * 100) 
                                 if (metrics['successful_transactions'] + metrics['failed_transactions']) > 0 else 0),
        'User Activity': min(100, (metrics['active_users_overall'] / 
                                  (metrics['active_users_overall'] + metrics['inactive_users_overall']) * 100) 
                           if (metrics['active_users_overall'] + metrics['inactive_users_overall']) > 0 else 0)
    }
    
    # Display scorecards
    cols = st.columns(4)
    score_items = list(scores.items())
    
    for idx, (name, score) in enumerate(score_items):
        with cols[idx]:
            # Determine color based on score
            if score >= 80:
                color = "#10B981"
            elif score >= 60:
                color = "#F59E0B"
            else:
                color = "#EF4444"
            
            # Create gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': name},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': color},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig.update_layout(height=200, margin=dict(t=50, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
    
    # Year-over-Year Comparison Placeholder
    st.markdown("### 📈 Year-over-Year Comparison")
    
    # Create placeholder data for demonstration
    years = [2023, 2024, 2025]
    comparison_data = {
        'Active Agents': [500, 750, metrics['total_active_agents']],
        'Transaction Volume': [1000000, 1500000, metrics['transaction_volume']],
        'Onboarding': [300, 450, metrics['onboarded_total']]
    }
    
    fig = go.Figure()
    
    for metric_name, values in comparison_data.items():
        fig.add_trace(go.Scatter(
            x=years,
            y=values,
            name=metric_name,
            mode='lines+markers',
            line=dict(width=3)
        ))
    
    fig.update_layout(
        title="Three-Year Performance Trend",
        xaxis_title="Year",
        yaxis_title="Count / Volume",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations Section
    st.markdown("### 💡 Strategic Recommendations")
    
    recommendations = []
    
    if scores['Network Coverage'] < 50:
        recommendations.append(
            "**Increase Agent-Teller Network**: Only {:.1f}% of agents have tellers. "
            "Consider incentive programs to expand the network.".format(scores['Network Coverage'])
        )
    
    if metrics['failed_transactions'] > metrics['successful_transactions'] * 0.1:
        recommendations.append(
            "**Improve Transaction Success**: {:.1f}% failure rate detected. "
            "Review system stability and user training.".format(
                (metrics['failed_transactions'] / metrics['successful_transactions'] * 100) 
                if metrics['successful_transactions'] > 0 else 0
            )
        )
    
    if metrics['inactive_users_overall'] > metrics['active_users_overall']:
        recommendations.append(
            "**Boost User Activity**: {} inactive users detected. "
            "Implement re-engagement campaigns.".format(metrics['inactive_users_overall'])
        )
    
    if not recommendations:
        recommendations.append("**Excellent Performance**: All metrics are within optimal ranges. "
                             "Focus on maintaining current strategies.")
    
    for i, rec in enumerate(recommendations, 1):
        st.info(f"{i}. {rec}")
        
else:
    st.info("👈 Please upload data files in the main page to view the overview.")