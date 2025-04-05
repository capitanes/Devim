import pandas as pd
import numpy as np
from io import StringIO
import datetime

def process_orders_data(file):
    """
    Process the orders CSV file containing loan application details.
    
    Args:
        file: Uploaded CSV file object
    
    Returns:
        pandas DataFrame with processed orders data
    """
    # Read the file content
    content = file.read().decode('utf-8')
    
    # Parse CSV data
    df = pd.read_csv(StringIO(content))
    
    # Ensure required columns exist
    required_columns = ['order_id', 'created_at', 'put_at', 'closed_at', 'issued_sum']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns in orders file: {', '.join(missing_columns)}")
    
    # Convert date columns to datetime
    date_columns = ['created_at', 'put_at', 'closed_at']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Convert numeric columns
    if 'issued_sum' in df.columns:
        df['issued_sum'] = pd.to_numeric(df['issued_sum'], errors='coerce')
    
    # Drop rows with missing order_id
    df = df.dropna(subset=['order_id'])
    
    # Convert order_id to string to ensure consistent joining
    df['order_id'] = df['order_id'].astype(str)
    
    return df

def process_plan_data(file):
    """
    Process the payment plan CSV file containing planned payment schedules.
    
    Args:
        file: Uploaded CSV file object
    
    Returns:
        pandas DataFrame with processed payment plan data
    """
    # Read the file content
    content = file.read().decode('utf-8')
    
    # Parse CSV data
    df = pd.read_csv(StringIO(content))
    
    # Ensure required columns exist
    required_columns = ['order_id', 'plan_at', 'plan_sum_total']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns in payment plan file: {', '.join(missing_columns)}")
    
    # Convert date columns to datetime
    if 'plan_at' in df.columns:
        df['plan_at'] = pd.to_datetime(df['plan_at'], errors='coerce')
    
    # Convert numeric columns
    if 'plan_sum_total' in df.columns:
        df['plan_sum_total'] = pd.to_numeric(df['plan_sum_total'], errors='coerce')
    
    # Drop rows with missing order_id or plan_at
    df = df.dropna(subset=['order_id', 'plan_at'])
    
    # Convert order_id to string to ensure consistent joining
    df['order_id'] = df['order_id'].astype(str)
    
    return df

def process_payments_data(file):
    """
    Process the actual payments CSV file containing payment records.
    
    Args:
        file: Uploaded CSV file object
    
    Returns:
        pandas DataFrame with processed payment data
    """
    # Read the file content
    content = file.read().decode('utf-8')
    
    # Parse CSV data
    df = pd.read_csv(StringIO(content))
    
    # Ensure required columns exist
    required_columns = ['order_id', 'paid_at', 'paid_sum']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns in payments file: {', '.join(missing_columns)}")
    
    # Convert date columns to datetime
    if 'paid_at' in df.columns:
        df['paid_at'] = pd.to_datetime(df['paid_at'], errors='coerce')
    
    # Convert numeric columns
    if 'paid_sum' in df.columns:
        df['paid_sum'] = pd.to_numeric(df['paid_sum'], errors='coerce')
    
    # Drop rows with missing order_id or paid_at
    df = df.dropna(subset=['order_id', 'paid_at'])
    
    # Convert order_id to string to ensure consistent joining
    df['order_id'] = df['order_id'].astype(str)
    
    return df

def merge_data(orders_df, plan_df, payments_df):
    """
    Merge the three datasets into a single dataframe for analysis.
    
    Args:
        orders_df: Processed orders DataFrame
        plan_df: Processed payment plan DataFrame
        payments_df: Processed actual payments DataFrame
    
    Returns:
        Merged DataFrame with all relevant information
    """
    # First merge orders with payment plan
    merged_df = pd.merge(
        orders_df,
        plan_df,
        on='order_id',
        how='inner'
    )
    
    # Then merge with actual payments
    # We use outer join here to include planned payments that might not have actual payments
    merged_df = pd.merge(
        merged_df,
        payments_df,
        on='order_id',
        how='left',
        suffixes=('', '_payment')
    )
    
    # Clean up the merged dataframe
    # If payment data is missing, set paid values to 0
    if 'paid_sum' in merged_df.columns:
        merged_df['paid_sum'] = merged_df['paid_sum'].fillna(0)
    
    # Handle the case where payment date is missing but amount exists
    if 'paid_at' in merged_df.columns:
        # For rows with paid_sum > 0 but no paid_at, use the plan_at date
        # This assumption can be adjusted based on business logic
        mask = (merged_df['paid_sum'] > 0) & (merged_df['paid_at'].isna())
        merged_df.loc[mask, 'paid_at'] = merged_df.loc[mask, 'plan_at']
    
    return merged_df

def calculate_delinquency_metrics(merged_df):
    """
    Calculate delinquency metrics based on the merged data.
    
    Args:
        merged_df: Merged DataFrame with orders, plan, and payments data
    
    Returns:
        DataFrame with additional delinquency metrics
    """
    # Make a copy to avoid modifying the original
    df = merged_df.copy()
    
    # Calculate days between planned and actual payment dates
    if 'plan_at' in df.columns and 'paid_at' in df.columns:
        # For payments that have been made
        mask = df['paid_at'].notna()
        df.loc[mask, 'days_late'] = (df.loc[mask, 'paid_at'] - df.loc[mask, 'plan_at']).dt.days
        
        # For payments that haven't been made, use today's date to calculate lateness
        mask = df['paid_at'].isna()
        today = pd.Timestamp.now().normalize()
        df.loc[mask, 'days_late'] = (today - df.loc[mask, 'plan_at']).dt.days
    else:
        df['days_late'] = 0
    
    # Calculate payment gap (difference between planned and actual payment amounts)
    if 'plan_sum_total' in df.columns and 'paid_sum' in df.columns:
        df['payment_gap'] = df['plan_sum_total'] - df['paid_sum']
    else:
        df['payment_gap'] = 0
    
    # Calculate delinquency flag (1 if payment is late, 0 otherwise)
    df['is_delinquent'] = (df['days_late'] > 0).astype(int)
    
    # Calculate loan age at payment time (in days)
    if 'put_at' in df.columns and 'plan_at' in df.columns:
        df['loan_age_days'] = (df['plan_at'] - df['put_at']).dt.days
    else:
        df['loan_age_days'] = 0
    
    # Calculate payment category based on days late
    df['payment_status'] = pd.cut(
        df['days_late'],
        bins=[-float('inf'), -1, 0, 7, 30, 60, float('inf')],
        labels=['Early', 'On Time', 'Slightly Late (1-7 days)', 
                'Late (8-30 days)', 'Very Late (31-60 days)', 'Extremely Late (60+ days)']
    )
    
    return df
