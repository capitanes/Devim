import pandas as pd
import streamlit as st
import io
from datetime import datetime, timedelta

def format_currency(amount):
    """
    Format a numeric value as currency.
    
    Args:
        amount: Numeric value to format
    
    Returns:
        Formatted currency string
    """
    return f"${amount:,.2f}"

def download_csv(df):
    """
    Prepare dataframe for CSV download.
    
    Args:
        df: DataFrame to download
    
    Returns:
        CSV data as string
    """
    # Create a copy of the dataframe
    download_df = df.copy()
    
    # Convert datetime columns to string
    for col in download_df.columns:
        if pd.api.types.is_datetime64_any_dtype(download_df[col]):
            download_df[col] = download_df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Convert to CSV
    csv = download_df.to_csv(index=False)
    
    return csv

def download_excel(df):
    """
    Prepare dataframe for Excel download.
    
    Args:
        df: DataFrame to download
    
    Returns:
        Excel data as bytes
    """
    # Create a copy of the dataframe
    download_df = df.copy()
    
    # Create an in-memory Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        download_df.to_excel(writer, sheet_name='Credit Loan Analysis', index=False)
        
        # Get the worksheet
        workbook = writer.book
        worksheet = writer.sheets['Credit Loan Analysis']
        
        # Add formatting
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D9D9D9',
            'border': 1
        })
        
        # Write the column headers with the defined format
        for col_num, value in enumerate(download_df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Adjust column widths
        for i, col in enumerate(download_df.columns):
            column_width = max(len(str(col)), download_df[col].map(lambda x: len(str(x))).max())
            worksheet.set_column(i, i, column_width + 2)
    
    # Reset the pointer to the beginning
    output.seek(0)
    
    return output.getvalue()

def create_date_filter(df, date_column, label):
    """
    Create a date range filter widget.
    
    Args:
        df: DataFrame containing date data
        date_column: Column name with date values
        label: Label for the filter widget
    
    Returns:
        Tuple of (start_date, end_date)
    """
    # Get min and max dates from the dataframe
    min_date = df[date_column].min().date()
    max_date = df[date_column].max().date()
    
    # Create a date range slider
    st.sidebar.subheader(label)
    
    # Default to last 6 months if range is large enough
    default_start = max(min_date, max_date - timedelta(days=180))
    
    start_date = st.sidebar.date_input(
        "Start Date",
        value=default_start,
        min_value=min_date,
        max_value=max_date
    )
    
    end_date = st.sidebar.date_input(
        "End Date",
        value=max_date,
        min_value=start_date,
        max_value=max_date
    )
    
    # Convert to datetime for filtering
    start_datetime = pd.Timestamp(start_date)
    end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    
    return start_datetime, end_datetime
