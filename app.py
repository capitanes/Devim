import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime, timedelta

from data_processor import (
    process_orders_data, 
    process_plan_data, 
    process_payments_data, 
    merge_data,
    calculate_delinquency_metrics
)
from visualizations import (
    create_delinquency_trend_chart,
    create_payment_comparison_chart,
    create_payment_behavior_chart,
    create_delinquency_heatmap
)
from utils import (
    download_csv,
    download_excel,
    format_currency,
    create_date_filter
)

# Set page title and layout
st.set_page_config(
    page_title="Credit Loan Payment Analysis Dashboard",
    page_icon="💰",
    layout="wide"
)

# Application title
st.title("Credit Loan Payment Analysis Dashboard")
st.markdown("Analyze credit loan payment behaviors and delinquency patterns")

# Sidebar for data upload and filtering
st.sidebar.header("Data Upload")

# Default file paths
default_orders_file = "data/orders.csv"
default_plan_file = "data/plan.csv"
default_payments_file = "data/payments.csv"

# File uploaders with default files
orders_file = st.sidebar.file_uploader("Upload Orders CSV", type=["csv"]) or default_orders_file
plan_file = st.sidebar.file_uploader("Upload Payment Plan CSV", type=["csv"]) or default_plan_file
payments_file = st.sidebar.file_uploader("Upload Actual Payments CSV", type=["csv"]) or default_payments_file

# Initialize session state for storing dataframes
if 'orders_df' not in st.session_state:
    st.session_state.orders_df = None
if 'plan_df' not in st.session_state:
    st.session_state.plan_df = None
if 'payments_df' not in st.session_state:
    st.session_state.payments_df = None
if 'merged_df' not in st.session_state:
    st.session_state.merged_df = None
if 'delinquency_df' not in st.session_state:
    st.session_state.delinquency_df = None

# Process uploaded files
if orders_file is not None:
    try:
        st.session_state.orders_df = process_orders_data(orders_file)
        st.sidebar.success(f"Orders data loaded: {len(st.session_state.orders_df)} records")
    except Exception as e:
        st.sidebar.error(f"Error processing orders file: {e}")

if plan_file is not None:
    try:
        st.session_state.plan_df = process_plan_data(plan_file)
        st.sidebar.success(f"Payment plan data loaded: {len(st.session_state.plan_df)} records")
    except Exception as e:
        st.sidebar.error(f"Error processing payment plan file: {e}")

if payments_file is not None:
    try:
        st.session_state.payments_df = process_payments_data(payments_file)
        st.sidebar.success(f"Payments data loaded: {len(st.session_state.payments_df)} records")
    except Exception as e:
        st.sidebar.error(f"Error processing payments file: {e}")

# If all files are uploaded, merge data
if (st.session_state.orders_df is not None and 
    st.session_state.plan_df is not None and 
    st.session_state.payments_df is not None):
    
    try:
        st.session_state.merged_df = merge_data(
            st.session_state.orders_df,
            st.session_state.plan_df,
            st.session_state.payments_df
        )
        
        st.session_state.delinquency_df = calculate_delinquency_metrics(st.session_state.merged_df)
        
        # Display filters in sidebar after data is loaded
        st.sidebar.header("Filters")
        
        # Date range filter
        start_date, end_date = create_date_filter(
            st.session_state.merged_df,
            'plan_at',
            "Filter by Planned Payment Date"
        )
        
        # Loan amount filter
        min_loan, max_loan = st.sidebar.slider(
            "Loan Amount Range",
            min_value=float(st.session_state.merged_df['issued_sum'].min()),
            max_value=float(st.session_state.merged_df['issued_sum'].max()),
            value=(float(st.session_state.merged_df['issued_sum'].min()), 
                   float(st.session_state.merged_df['issued_sum'].max()))
        )
        
        # Apply filters
        filtered_df = st.session_state.delinquency_df[
            (st.session_state.delinquency_df['plan_at'] >= start_date) &
            (st.session_state.delinquency_df['plan_at'] <= end_date) &
            (st.session_state.delinquency_df['issued_sum'] >= min_loan) &
            (st.session_state.delinquency_df['issued_sum'] <= max_loan)
        ]
        
        # Main dashboard content
        if not filtered_df.empty:
            # Dashboard metrics
            metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
            
            with metrics_col1:
                total_loans = filtered_df['order_id'].nunique()
                st.metric("Total Loans", f"{total_loans:,}")
            
            with metrics_col2:
                total_loan_amount = filtered_df['issued_sum'].sum()
                st.metric("Total Loan Amount", f"${total_loan_amount:,.2f}")
            
            with metrics_col3:
                avg_delay = filtered_df['days_late'].mean()
                st.metric("Average Payment Delay", f"{avg_delay:.1f} days")
            
            with metrics_col4:
                delinquency_rate = (filtered_df[filtered_df['days_late'] > 0]['order_id'].nunique() / 
                                   total_loans * 100)
                st.metric("Delinquency Rate", f"{delinquency_rate:.1f}%")
            
            # Visualization tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "Delinquency Trends", 
                "Planned vs Actual Payments", 
                "Payment Behavior",
                "Summary & Export"
            ])
            
            with tab1:
                st.subheader("Delinquency Trends Analysis")
                
                # Delinquency trend over time
                st.plotly_chart(
                    create_delinquency_trend_chart(filtered_df),
                    use_container_width=True
                )
                
                # Delinquency heatmap
                st.plotly_chart(
                    create_delinquency_heatmap(filtered_df),
                    use_container_width=True
                )
                
                # Additional delinquency statistics
                st.subheader("Delinquency Statistics")
                
                stats_col1, stats_col2 = st.columns(2)
                
                with stats_col1:
                    # Distribution of days late
                    # Create a function to categorize days late
                    def categorize_days_late(days):
                        if days <= -1:
                            return 'Early'
                        elif days <= 0:
                            return 'On time'
                        elif days <= 7:
                            return '1-7 days'
                        elif days <= 14:
                            return '8-14 days'
                        elif days <= 30:
                            return '15-30 days'
                        elif days <= 60:
                            return '31-60 days'
                        else:
                            return '60+ days'
                    
                    # Apply the categorization function
                    filtered_df_copy = filtered_df.copy()
                    filtered_df_copy['days_late_category'] = filtered_df_copy['days_late'].apply(categorize_days_late)
                    
                    # Group by the category and count
                    late_counts = filtered_df_copy.groupby('days_late_category').size().reset_index(name='count')
                    
                    fig = px.pie(
                        late_counts, 
                        values='count', 
                        names='days_late_category',
                        title='Distribution of Payment Timing',
                        color_discrete_sequence=px.colors.sequential.Blues_r
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with stats_col2:
                    # Average days late by loan amount
                    # Create loan amount ranges manually
                    filtered_df_loan = filtered_df.copy()
                    
                    # Find min and max loan amounts for range creation
                    min_loan = filtered_df_loan['issued_sum'].min()
                    max_loan = filtered_df_loan['issued_sum'].max()
                    
                    # Create range bins (5 equal bins)
                    bin_size = (max_loan - min_loan) / 5
                    bins = [min_loan + i * bin_size for i in range(6)]
                    
                    # Create labels for the bins
                    labels = [f'${bins[i]:.0f}-${bins[i+1]:.0f}' for i in range(5)]
                    
                    # Create a function to assign each loan to a bin
                    def assign_loan_bin(loan_amount):
                        for i in range(5):
                            if bins[i] <= loan_amount < bins[i+1]:
                                return labels[i]
                        return labels[-1]  # For the maximum value
                    
                    # Apply the binning function
                    filtered_df_loan['loan_amount_range'] = filtered_df_loan['issued_sum'].apply(assign_loan_bin)
                    
                    # Group by the loan amount range and calculate average days late
                    avg_late_by_loan = filtered_df_loan.groupby('loan_amount_range')['days_late'].mean().reset_index()
                    
                    fig = px.bar(
                        avg_late_by_loan,
                        x='loan_amount_range',
                        y='days_late',
                        title='Average Days Late by Loan Amount',
                        labels={'loan_amount_range': 'Loan Amount Range', 'days_late': 'Average Days Late'},
                        color='days_late',
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                st.subheader("Planned vs Actual Payments")
                
                # Payment comparison chart
                st.plotly_chart(
                    create_payment_comparison_chart(filtered_df),
                    use_container_width=True
                )
                
                # Payment gap analysis
                st.subheader("Payment Gap Analysis")
                payment_col1, payment_col2 = st.columns(2)
                
                with payment_col1:
                    # Payment gap distribution
                    payment_gap_df = filtered_df.copy()
                    payment_gap_df['payment_gap'] = payment_gap_df['plan_sum_total'] - payment_gap_df['paid_sum']
                    payment_gap_df['gap_percentage'] = (payment_gap_df['payment_gap'] / 
                                                       payment_gap_df['plan_sum_total'] * 100)
                    
                    fig = px.histogram(
                        payment_gap_df,
                        x='gap_percentage',
                        title='Distribution of Payment Gaps (%)',
                        labels={'gap_percentage': 'Payment Gap (%)'},
                        color_discrete_sequence=['#E74C3C']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with payment_col2:
                    # Cumulative payments over time
                    payment_time_df = filtered_df.sort_values('plan_at')
                    payment_time_df['cumulative_planned'] = payment_time_df.groupby('order_id')['plan_sum_total'].cumsum()
                    payment_time_df['cumulative_actual'] = payment_time_df.groupby('order_id')['paid_sum'].cumsum()
                    
                    # Take a sample of orders for clarity
                    sample_orders = payment_time_df['order_id'].unique()[:5]
                    sample_df = payment_time_df[payment_time_df['order_id'].isin(sample_orders)]
                    
                    fig = go.Figure()
                    
                    for order_id in sample_orders:
                        order_data = sample_df[sample_df['order_id'] == order_id]
                        
                        fig.add_trace(go.Scatter(
                            x=order_data['plan_at'],
                            y=order_data['cumulative_planned'],
                            mode='lines',
                            name=f'Order {order_id} (Planned)',
                            line=dict(dash='solid')
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=order_data['paid_at'],
                            y=order_data['cumulative_actual'],
                            mode='lines',
                            name=f'Order {order_id} (Actual)',
                            line=dict(dash='dot')
                        ))
                    
                    fig.update_layout(
                        title='Cumulative Payments Over Time (Sample Orders)',
                        xaxis_title='Date',
                        yaxis_title='Cumulative Amount',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                st.subheader("Payment Behavior Analysis")
                
                # Payment behavior chart
                st.plotly_chart(
                    create_payment_behavior_chart(filtered_df),
                    use_container_width=True
                )
                
                # Additional payment behavior analytics
                behavior_col1, behavior_col2 = st.columns(2)
                
                with behavior_col1:
                    # Payment lateness over loan duration
                    loan_duration_df = filtered_df.copy()
                    
                    # Calculate loan age in days first
                    loan_duration_df['loan_age_days'] = (loan_duration_df['plan_at'] - loan_duration_df['put_at']).dt.days
                    
                    # Convert days to approximate months (using 30 days as a month for simplicity)
                    loan_duration_df['loan_age_months'] = (loan_duration_df['loan_age_days'] / 30).astype(int)
                    
                    avg_lateness_by_age = loan_duration_df.groupby('loan_age_months')['days_late'].mean().reset_index()
                    
                    fig = px.line(
                        avg_lateness_by_age,
                        x='loan_age_months',
                        y='days_late',
                        title='Average Payment Lateness by Loan Age',
                        labels={'loan_age_months': 'Loan Age (Months)', 'days_late': 'Average Days Late'},
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with behavior_col2:
                    # Seasonal patterns in payment behavior
                    seasonal_df = filtered_df.copy()
                    seasonal_df['month'] = seasonal_df['plan_at'].dt.month
                    seasonal_df['month_name'] = seasonal_df['plan_at'].dt.strftime('%B')
                    
                    monthly_delinquency = seasonal_df.groupby('month_name')['days_late'].mean().reset_index()
                    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                                  'July', 'August', 'September', 'October', 'November', 'December']
                    monthly_delinquency['month_name'] = pd.Categorical(
                        monthly_delinquency['month_name'], 
                        categories=month_order, 
                        ordered=True
                    )
                    monthly_delinquency = monthly_delinquency.sort_values('month_name')
                    
                    fig = px.bar(
                        monthly_delinquency,
                        x='month_name',
                        y='days_late',
                        title='Seasonal Patterns in Payment Delinquency',
                        labels={'month_name': 'Month', 'days_late': 'Average Days Late'},
                        color='days_late',
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab4:
                st.subheader("Summary & Data Export")
                
                # Summary statistics
                st.markdown("### Key Findings")
                
                # Calculate summary statistics
                total_payments = len(filtered_df)
                on_time_payments = len(filtered_df[filtered_df['days_late'] <= 0])
                late_payments = len(filtered_df[filtered_df['days_late'] > 0])
                on_time_percentage = on_time_payments / total_payments * 100
                
                total_planned = filtered_df['plan_sum_total'].sum()
                total_paid = filtered_df['paid_sum'].sum()
                payment_deficit = total_planned - total_paid
                payment_deficit_percentage = payment_deficit / total_planned * 100
                
                st.markdown(f"""
                **Payment Timeliness:**
                - Total payments analyzed: {total_payments:,}
                - On-time or early payments: {on_time_payments:,} ({on_time_percentage:.1f}%)
                - Late payments: {late_payments:,} ({100-on_time_percentage:.1f}%)
                
                **Payment Amounts:**
                - Total planned payment amount: ${total_planned:,.2f}
                - Total actual payment amount: ${total_paid:,.2f}
                - Payment deficit: ${payment_deficit:,.2f} ({payment_deficit_percentage:.1f}%)
                
                **Delinquency Patterns:**
                - Most common delinquency period: {filtered_df['days_late'].value_counts().idxmax()} days
                - Average delinquency duration: {filtered_df['days_late'].mean():.1f} days
                """)
                
                # Data inconsistencies
                st.markdown("### Data Inconsistencies")
                
                # Check for orders with no payments
                orders_without_payments = set(st.session_state.orders_df['order_id']) - set(st.session_state.payments_df['order_id'])
                
                # Check for payments without corresponding plan
                payments_without_plan = set(st.session_state.payments_df['order_id']) - set(st.session_state.plan_df['order_id'])
                
                # Check for plan entries without orders
                plan_without_orders = set(st.session_state.plan_df['order_id']) - set(st.session_state.orders_df['order_id'])
                
                st.markdown(f"""
                **Identified inconsistencies:**
                - Orders without any payment records: {len(orders_without_payments)}
                - Payments without a corresponding payment plan: {len(payments_without_plan)}
                - Payment plans without corresponding orders: {len(plan_without_orders)}
                """)
                
                # Export options
                st.markdown("### Export Data")
                
                export_col1, export_col2 = st.columns(2)
                
                with export_col1:
                    if st.button("Export Analysis as CSV"):
                        csv_data = download_csv(filtered_df)
                        st.download_button(
                            label="Download CSV",
                            data=csv_data,
                            file_name="credit_loan_analysis.csv",
                            mime="text/csv"
                        )
                
                with export_col2:
                    if st.button("Export Analysis as Excel"):
                        excel_data = download_excel(filtered_df)
                        st.download_button(
                            label="Download Excel",
                            data=excel_data,
                            file_name="credit_loan_analysis.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
        else:
            st.warning("No data matches the selected filters. Please adjust your filter criteria.")
    
    except Exception as e:
        st.error(f"Error processing data: {e}")
        st.exception(e)
else:
    # Display instructions if files are not uploaded
    st.info("Please upload the required CSV files to start analyzing credit loan payment data:")
    
    instructions_col1, instructions_col2 = st.columns(2)
    
    with instructions_col1:
        st.markdown("""
        **Required data files:**
        1. **Orders CSV** - Contains loan application details (order_id, created_at, put_at, closed_at, issued_sum)
        2. **Payment Plan CSV** - Contains planned payment schedules (order_id, plan_at, plan_sum_total)
        3. **Actual Payments CSV** - Contains actual payment records (order_id, paid_at, paid_sum)
        """)
    
    with instructions_col2:
        st.markdown("""
        **What you'll be able to analyze:**
        - Payment delinquency trends and patterns
        - Comparison between planned and actual payments
        - Statistical summaries of payment behaviors
        - Time-series analysis of payment patterns
        - Detailed delinquency metrics with interactive visualizations
        """)
