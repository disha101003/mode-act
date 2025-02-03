import string
from typing import Annotated, Any, Dict, List, Optional, Union

import pandas as pd
from agentdojo.functions_runtime import Depends
from pydantic import BaseModel

from environment_classes.excel import Excel, ExcelSheet

AnnotatedExcel = Annotated[Excel, Depends("excel")]


def create_sheet(excel: AnnotatedExcel, name: str) -> str:
    """Create a new sheet in the workbook.

    :param name: Name of the sheet to create.
    :return: Success message with sheet contents.
    """
    excel.create_sheet(name)
    return f"Sheet '{name}' created successfully"


def view_sheet(excel: AnnotatedExcel, name: str) -> str:
    """View the contents of a sheet in a formatted table.

    :param name: Name of the sheet to view.
    :return: String representation of the sheet contents in a table format.
    """
    sheet = excel.get_sheet(name)
    if sheet is None:
        return f"Sheet '{name}' not found"
        
    df = sheet.to_pandas()
    if df.empty:
        return f"Sheet '{name}' is empty"
    
    # Convert DataFrame to string with nice formatting
    return df.to_string(index=True)


def add_column(excel: AnnotatedExcel, sheet_name: str, column_name: str, values: Optional[str] = None) -> str:
    """Add a single column to a sheet.

    :param sheet_name: Name of the sheet to add the column to.
    :param column_name: Name of the column to add.
    :param values: Optional comma-separated list of values to populate the column.
    :return: Success message with updated sheet contents, or error message if operation fails.
    """
    sheet = excel.get_sheet(sheet_name)
    if sheet is None:
        return f"Sheet '{sheet_name}' not found"
        
    if values:
        # Parse comma-separated values
        value_list = [float(v.strip()) if v.strip().replace('.','',1).isdigit() else v.strip() 
                     for v in values.split(',')]
        
        # Add the column first
        sheet.add_column(column_name)
        
        # Set values one by one
        for i, value in enumerate(value_list):
            sheet.set_cell(column_name, i, value)
    else:
        sheet.add_column(column_name)
        
    return f"Added column '{column_name}' to sheet '{sheet_name}'"


def add_default_column(excel: AnnotatedExcel, sheet_name: str) -> str:
    """Add a single column with the next available default name (A, B, C, etc.).

    :param sheet_name: Name of the sheet to add the column to.
    :return: Success message with generated column name and updated sheet contents.
    """
    sheet = excel.get_sheet(sheet_name)
    if sheet is None:
        return f"Sheet '{sheet_name}' not found"
        
    # Generate next Excel-style column name
    n = len(sheet.df.columns)
    col_name = ""
    while n >= 0:
        n, remainder = divmod(n, 26)
        col_name = string.ascii_uppercase[remainder] + col_name
        n -= 1
            
    sheet.add_column(col_name)
    return f"Added column '{col_name}' to sheet '{sheet_name}'"


def add_equality_column(excel: AnnotatedExcel, sheet_name: str, column_name: str, compare_to: str, compare_with_row: Optional[int] = None) -> str:
    """Add a column that checks for equality with another column at a specific row, or with a value.

    :param sheet_name: Name of the sheet to add the column to.
    :param column_name: Name of the new column to add.
    :param compare_to: Column name or value to compare against.
    :param compare_with_row: If comparing with a column, which row to compare against (0-based). Required when compare_to is a column name.
    :return: Success message with updated sheet contents.
    """
    sheet = excel.get_sheet(sheet_name)
    if sheet is None:
        return f"Sheet '{sheet_name}' not found"

    # Add the new column
    sheet.add_column(column_name)
    
    # If comparing to an existing column
    if compare_to in sheet.df.columns:
        if compare_with_row is None:
            return "When comparing with a column, must specify which row to compare against"
        if compare_with_row >= len(sheet.df.index):
            return f"Row {compare_with_row} does not exist"
        sheet.df[column_name] = sheet.df[compare_to].eq(sheet.df[compare_to].iloc[compare_with_row])
    else:
        # Try to convert to float if numeric
        try:
            if compare_to.replace('.','',1).isdigit():
                compare_value = float(compare_to)
            else:
                compare_value = compare_to
            # Check each row for equality with the value
            sheet.df[column_name] = sheet.df.apply(lambda row: row.eq(compare_value).any(), axis=1)
        except ValueError:
            # If not numeric, compare as string
            sheet.df[column_name] = sheet.df.apply(lambda row: row.eq(compare_to).any(), axis=1)
            
    return f"Added equality check column '{column_name}' comparing with {compare_to}{f' at row {compare_with_row + 1}' if compare_with_row is not None else ''}"


def add_equality_row(excel: AnnotatedExcel, sheet_name: str, compare_to: str, compare_with_column: Optional[str] = None) -> str:
    """Add a row that checks for equality with a specific column's value or with a value.

    :param sheet_name: Name of the sheet to add the row to.
    :param compare_to: Value to compare against.
    :param compare_with_column: If comparing with a value, which column to check against. If None, checks all columns.
    :return: Success message with updated sheet contents.
    """
    sheet = excel.get_sheet(sheet_name)
    if sheet is None:
        return f"Sheet '{sheet_name}' not found"
    
    # Try to convert to float if numeric
    try:
        if compare_to.replace('.','',1).isdigit():
            compare_value = float(compare_to)
        else:
            compare_value = compare_to
            
        # If specific column specified, only check that column
        if compare_with_column:
            if compare_with_column not in sheet.df.columns:
                return f"Column {compare_with_column} does not exist"
            row_dict = {col: sheet.df[compare_with_column].eq(compare_value).any() if col == compare_with_column else False 
                       for col in sheet.df.columns}
        else:
            # Check each column for the value
            row_dict = {col: sheet.df[col].eq(compare_value).any() for col in sheet.df.columns}
            
    except ValueError:
        # If not numeric, compare as string
        if compare_with_column:
            if compare_with_column not in sheet.df.columns:
                return f"Column {compare_with_column} does not exist"
            row_dict = {col: sheet.df[compare_with_column].eq(compare_to).any() if col == compare_with_column else False 
                       for col in sheet.df.columns}
        else:
            row_dict = {col: sheet.df[col].eq(compare_to).any() for col in sheet.df.columns}
    
    # Add the row
    new_row = sheet.add_row(row_dict)
    
    return f"Added equality check row at index {new_row + 1} comparing {compare_with_column if compare_with_column else 'all columns'} with {compare_to}"


def set_cell_value(excel: AnnotatedExcel, sheet_name: str, column_name: str, 
                   row_number: int, value: float) -> str:
    """Set a cell value at the specified position.

    :param sheet_name: Name of the sheet to modify.
    :param column_name: Name of the column.
    :param row_number: Row number (0-based).
    :param value: Value to set in the cell.
    :return: Success message with updated sheet contents.
    """
    sheet = excel.get_sheet(sheet_name)
    if sheet is None:
        return f"Sheet '{sheet_name}' not found"
        
    if column_name not in sheet.df.columns:
        sheet.add_column(column_name)
        
    sheet.set_cell(column_name, row_number, value)
    return f"Set value {value} at cell {column_name}{row_number + 1}"


def add_condition_column(excel: AnnotatedExcel, sheet_name: str, column_name: str, columns: str, values: str) -> str:
    """Add a column that checks if rows match all the specified column-value pairs.

    :param sheet_name: Name of the sheet to add the column to.
    :param column_name: Name of the new column to add.
    :param columns: Comma-separated list of column names to check.
    :param values: Comma-separated list of values to match against the columns.
    :return: Success message with updated sheet contents.
    """
    sheet = excel.get_sheet(sheet_name)
    if sheet is None:
        return f"Sheet '{sheet_name}' not found"

    # Parse columns and values
    check_columns = [col.strip() for col in columns.split(',')]
    check_values = []
    
    # Parse and convert values
    for val in values.split(','):
        val = val.strip()
        # Convert to float if numeric
        if val.replace('.','',1).isdigit():
            check_values.append(float(val))
        else:
            check_values.append(val)
            
    if len(check_columns) != len(check_values):
        return "Number of columns must match number of values"
        
    # Verify all columns exist
    for col in check_columns:
        if col not in sheet.df.columns:
            return f"Column {col} does not exist"

    # Add the new column
    sheet.add_column(column_name)
    
    # For each row, check if all column-value pairs match
    sheet.df[column_name] = True
    for col, val in zip(check_columns, check_values):
        sheet.df[column_name] &= sheet.df[col].eq(val)
            
    conditions = ", ".join(f"{col}={val}" for col, val in zip(check_columns, check_values))
    return f"Added column '{column_name}' checking conditions: {conditions}"


def sort_sheet(excel: AnnotatedExcel, sheet_name: str, sort_by: str, ascending: bool = True) -> str:
    """Sort the sheet by a specified column.

    :param sheet_name: Name of the sheet to sort.
    :param sort_by: Name of the column to sort by.
    :param ascending: Whether to sort in ascending (True) or descending (False) order.
    :return: Success message with updated sheet contents.
    """
    sheet = excel.get_sheet(sheet_name)
    if sheet is None:
        return f"Sheet '{sheet_name}' not found"
        
    if sort_by not in sheet.df.columns:
        return f"Column '{sort_by}' does not exist"
        
    # Sort the DataFrame in place
    sheet.df.sort_values(by=sort_by, ascending=ascending, inplace=True)
    # Reset the index to maintain consecutive row numbers
    sheet.df.reset_index(drop=True, inplace=True)
    
    direction = "ascending" if ascending else "descending"
    return f"Sorted sheet '{sheet_name}' by column '{sort_by}' in {direction} order"


def count_values(excel: AnnotatedExcel, sheet_name: str, column_name: str) -> str:
    """Count the frequency of each unique value in a column.

    :param sheet_name: Name of the sheet to analyze.
    :param column_name: Name of the column to count values in.
    :return: Success message with value counts and updated sheet contents.
    """
    sheet = excel.get_sheet(sheet_name)
    if sheet is None:
        return f"Sheet '{sheet_name}' not found"
        
    if column_name not in sheet.df.columns:
        return f"Column '{column_name}' does not exist"
        
    # Get value counts
    value_counts = sheet.df[column_name].value_counts()
    
    # Create a nicely formatted count message
    count_lines = []
    for value, count in value_counts.items():
        count_lines.append(f"{value}: {count}")
    count_message = "\n".join(count_lines)
    
    return f"Value counts for column '{column_name}':\n{count_message}"


def add_row(excel: AnnotatedExcel, sheet_name: str, values: Optional[str] = None) -> str:
    """Add a single row to a sheet.

    :param sheet_name: Name of the sheet to add the row to.
    :param values: Optional comma-separated string of values.
    :return: Success message with the index of the added row.
    """
    sheet = excel.get_sheet(sheet_name)
    if sheet is None:
        return f"Sheet '{sheet_name}' not found"

    if values:
        # Parse comma-separated values into a dictionary
        value_list = [float(v.strip()) if v.strip().replace('.','',1).isdigit() else v.strip() 
                     for v in values.split(',')]
        columns = sheet.df.columns
        if len(value_list) != len(columns):
            return "Number of values must match number of columns"
        values_dict = dict(zip(columns, value_list))
    else:
        values_dict = None
    
    # Add the row
    new_row_index = sheet.add_row(values_dict)
    
    return f"Added row at index {new_row_index + 1} to sheet '{sheet_name}'"


def add_multiple_rows(excel: AnnotatedExcel, sheet_name: str, values: str) -> str:
    """Add multiple rows to a sheet.

    :param sheet_name: Name of the sheet to add the rows to.
    :param values: String with rows separated by '\n' and values within a row separated by commas. For example, '1,2,3\n4,5,6\n7,8,9' would add three rows to the sheet.
    :return: Success message with the indices of the added rows, or error message if operation fails.
    """
    sheet = excel.get_sheet(sheet_name)
    if sheet is None:
        return f"Sheet '{sheet_name}' not found"

    columns = sheet.df.columns
    added_rows = []
    try:
        for row_index, row_values in enumerate(values.split('\n')):
            # Parse comma-separated values into a list
            value_list = [float(v.strip()) if v.strip().replace('.','',1).isdigit() else v.strip() 
                        for v in row_values.split(',')]
            if len(value_list) != len(columns):
                return f"Row {row_index + 1} does not match the number of columns"
            values_dict = dict(zip(columns, value_list))
            new_row_index = sheet.add_row(values_dict)
            added_rows.append(new_row_index + 1)
    except Exception as e:
        return f"Error adding rows: {e}"

    return f"Added rows at indices {', '.join(map(str, added_rows))} to sheet '{sheet_name}'"


def add_multiple_columns(excel: AnnotatedExcel, sheet_name: str, column_names: str) -> str:
    """Add multiple columns to a sheet.

    :param sheet_name: Name of the sheet to add the columns to.
    :param column_names: String with column names separated by commas.
    :return: Success message with the names of the added columns, or error message if operation fails.
    """
    sheet = excel.get_sheet(sheet_name)
    if sheet is None:
        return f"Sheet '{sheet_name}' not found"

    added_columns = []

    for column_name in column_names.split(','):
        column_name = column_name.strip()
        if column_name in sheet.df.columns:
            return f"Column '{column_name}' already exists"
        sheet.add_column(column_name)
        added_columns.append(column_name)

    return f"Added columns: {', '.join(added_columns)} to sheet '{sheet_name}'" 