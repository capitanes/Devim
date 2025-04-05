import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_delinquency_trend_chart(df):
    """
    Create a chart showing delinquency trends over time.
    
    Args:
        df: DataFrame containing delinquency metrics
    
    Returns:
        Plotly figure object
    """
    # Group by plan_at date and calculate average days late
    trend_df = df.groupby(df['plan_at'].dt.to_period('M').astype(str)).agg({
        'days_late': 'mean',
        'is_delinquent': 'mean',
        'order_id': 'count'
    }).reset_index()
    
    trend_df.rename(columns={
        'is_delinquent': 'delinquency_rate',
        'order_id': 'payment_count'
    }, inplace=True)
    
    trend_df['delinquency_rate'] = trend_df['delinquency_rate'] * 100
    
    # Create subplots with shared x-axis
    fig = make_subplots(
        rows=2, 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Average Days Late by Month", "Delinquency Rate by Month (%)")
    )
    
    # Add bar chart for average days late
    fig.add_trace(
        go.Bar(
            x=trend_df['plan_at'],
            y=trend_df['days_late'],
            name='Average Days Late',
            marker_color='#E74C3C'
        ),
        row=1, col=1
    )
    
    # Add line chart for delinquency rate
    fig.add_trace(
        go.Scatter(
            x=trend_df['plan_at'],
            y=trend_df['delinquency_rate'],
            name='Delinquency Rate (%)',
            mode='lines+markers',
            line=dict(color='#2C3E50', width=2),
            marker=dict(size=8)
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis2_title="Month",
        yaxis_title="Average Days Late",
        yaxis2_title="Delinquency Rate (%)"
    )
    
    return fig

def create_payment_comparison_chart(df):
    """
    Create a chart comparing planned vs actual payments.
    
    Args:
        df: DataFrame containing payment data
    
    Returns:
        Plotly figure object
    """
    # Group by plan_at date and aggregate payment amounts
    payment_comp_df = df.groupby(df['plan_at'].dt.to_period('M').astype(str)).agg({
        'plan_sum_total': 'sum',
        'paid_sum': 'sum'
    }).reset_index()
    
    # Calculate the percentage of planned payments that were actually paid
    payment_comp_df['payment_rate'] = payment_comp_df['paid_sum'] / payment_comp_df['plan_sum_total'] * 100
    
    # Create subplots
    fig = make_subplots(
        rows=2, 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Planned vs Actual Payment Amounts", "Payment Completion Rate (%)")
    )
    
    # Add bar chart for planned and actual payment amounts
    fig.add_trace(
        go.Bar(
            x=payment_comp_df['plan_at'],
            y=payment_comp_df['plan_sum_total'],
            name='Planned Payments',
            marker_color='#2C3E50'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=payment_comp_df['plan_at'],
            y=payment_comp_df['paid_sum'],
            name='Actual Payments',
            marker_color='#27AE60'
        ),
        row=1, col=1
    )
    
    # Add line chart for payment completion rate
    fig.add_trace(
        go.Scatter(
            x=payment_comp_df['plan_at'],
            y=payment_comp_df['payment_rate'],
            name='Payment Rate (%)',
            mode='lines+markers',
            line=dict(color='#E74C3C', width=2),
            marker=dict(size=8)
        ),
        row=2, col=1
    )
    
    # Add 100% reference line
    fig.add_trace(
        go.Scatter(
            x=payment_comp_df['plan_at'],
            y=[100] * len(payment_comp_df),
            name='100% Target',
            mode='lines',
            line=dict(color='rgba(0,0,0,0.3)', width=1, dash='dash')
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis2_title="Month",
        yaxis_title="Payment Amount",
        yaxis2_title="Payment Rate (%)",
        barmode='group'
    )
    
    return fig

def create_payment_behavior_chart(df):
    """
    Create a chart showing payment behavior patterns.
    
    Args:
        df: DataFrame containing payment data
    
    Returns:
        Plotly figure object
    """
    # Calculate payment status distribution by month
    behavior_df = df.copy()
    behavior_df['month'] = behavior_df['plan_at'].dt.to_period('M').astype(str)
    
    # Pivot the data to get payment status counts by month
    behavior_pivot = pd.pivot_table(
        behavior_df,
        values='order_id',
        index='month',
        columns='payment_status',
        aggfunc='count',
        fill_value=0,
        observed=True  # Add observed=True to resolve FutureWarning
    ).reset_index()
    
    # Calculate total payments per month for percentage calculation
    behavior_pivot['total'] = behavior_pivot.iloc[:, 1:].sum(axis=1)
    
    # Convert to percentages
    for col in behavior_pivot.columns:
        if col not in ['month', 'total']:
            behavior_pivot[f'{col}_pct'] = behavior_pivot[col] / behavior_pivot['total'] * 100
    
    # Create figure
    fig = make_subplots(
        rows=2, 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Payment Status Distribution (Count)", "Payment Status Distribution (%)")
    )
    
    # Define colors for payment statuses
    status_colors = {
        'Early': '#27AE60',
        'On Time': '#2C3E50',
        'Slightly Late (1-7 days)': '#F39C12',
        'Late (8-30 days)': '#E67E22',
        'Very Late (31-60 days)': '#D35400',
        'Extremely Late (60+ days)': '#E74C3C'
    }
    
    # Add stacked bar chart for counts
    for status in behavior_pivot.columns:
        if status not in ['month', 'total'] and not status.endswith('_pct'):
            fig.add_trace(
                go.Bar(
                    x=behavior_pivot['month'],
                    y=behavior_pivot[status],
                    name=status,
                    marker_color=status_colors.get(status, '#000000')
                ),
                row=1, col=1
            )
    
    # Add stacked bar chart for percentages
    for status in behavior_pivot.columns:
        if status.endswith('_pct'):
            status_name = status.replace('_pct', '')
            if status_name not in ['month', 'total']:
                fig.add_trace(
                    go.Bar(
                        x=behavior_pivot['month'],
                        y=behavior_pivot[status],
                        name=f"{status_name} (%)",
                        marker_color=status_colors.get(status_name, '#000000'),
                        showlegend=False
                    ),
                    row=2, col=1
                )
    
    # Update layout
    fig.update_layout(
        height=700,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis2_title="Month",
        yaxis_title="Number of Payments",
        yaxis2_title="Percentage (%)",
        barmode='stack'
    )
    
    return fig

def create_delinquency_heatmap(df):
    """
    Create a heatmap showing delinquency patterns.
    
    Args:
        df: DataFrame containing delinquency metrics
    
    Returns:
        Plotly figure object
    """
    # Create a copy of the dataframe
    heatmap_df = df.copy()
    
    # Extract month and year from plan_at
    heatmap_df['month'] = heatmap_df['plan_at'].dt.month
    heatmap_df['year'] = heatmap_df['plan_at'].dt.year
    
    # Group by month and loan amount range
    # Create loan amount ranges manually instead of using pd.cut
    # Define bin edges and labels
    bin_edges = [0, 1000, 2000, 5000, 10000, float('inf')]
    bin_labels = ['0-1K', '1K-2K', '2K-5K', '5K-10K', '10K+']
    
    # Function to assign each loan to a bin
    def get_loan_range(loan_amount):
        for i in range(len(bin_edges) - 1):
            if bin_edges[i] <= loan_amount < bin_edges[i + 1]:
                return bin_labels[i]
        return bin_labels[-1]  # For max value
    
    # Apply the function to create loan amount ranges
    heatmap_df['loan_amount_range'] = heatmap_df['issued_sum'].apply(get_loan_range)

    heatmap_df['loan_amount_range'] = pd.Categorical(
    heatmap_df['loan_amount_range'],
    categories=['0-1K', '1K-2K', '2K-5K', '5K-10K', '10K+'],
    ordered=True
    )
    
    # Create a pivot table for the heatmap
    heatmap_pivot = pd.pivot_table(
        heatmap_df,
        values='days_late',
        index='loan_amount_range',
        columns=['year', 'month'],
        aggfunc='mean',
        fill_value=0,
        observed=True  # Add observed=True to resolve FutureWarning
    )
    
    # Flatten multi-index columns
    heatmap_pivot.columns = [f"{year}-{month:02d}" for year, month in heatmap_pivot.columns]
    
    # Reset index to prepare for plotting
    heatmap_pivot = heatmap_pivot.reset_index()
    
    # Melt the dataframe for heatmap plotting
    heatmap_melted = pd.melt(
        heatmap_pivot,
        id_vars='loan_amount_range',
        var_name='period',
        value_name='avg_days_late'
    )
    
    # Create heatmap
    fig = px.density_heatmap(
        heatmap_melted,
        x='period',
        y='loan_amount_range',
        z='avg_days_late',
        title='Average Days Late by Loan Amount and Month',
        labels={
            'period': 'Month',
            'loan_amount_range': 'Loan Amount Range',
            'avg_days_late': 'Average Days Late'
        },
        color_continuous_scale=px.colors.sequential.Reds
    )
    
    # Update layout
    fig.update_layout(
        height=500,
        xaxis_title="Period (Year-Month)",
        yaxis_title="Loan Amount Range",
        coloraxis_colorbar=dict(title="Avg Days Late")
    )
    
    return fig
