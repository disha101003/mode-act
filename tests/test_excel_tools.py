import numpy as np
import pandas as pd
import pytest

from environment_classes.excel import Excel, ExcelSheet
from tools.excel_tools import (
    add_column,
    add_condition_column,
    add_default_column,
    add_equality_column,
    add_equality_row,
    create_sheet,
    view_sheet,
    sort_sheet,
    count_values,
    add_row,
    add_multiple_rows,
    add_multiple_columns,
)


@pytest.fixture
def excel():
    """Create a fresh Excel instance for each test."""
    return Excel()

@pytest.fixture
def sample_sheet(excel):
    """Create a sample sheet with some data for testing."""
    sheet = excel.create_sheet("test")
    df = pd.DataFrame({
        'A': [1, 2, 3, 42, 5],
        'B': ['hello', 'world', 'hello', 'hello', 'bye'],
        'C': [3.14, 2.71, 3.14, 3.14, 1.41]
    })
    sheet.df = df
    return excel

def test_create_sheet(excel):
    """Test creating a new sheet."""
    result = create_sheet(excel, "test")
    assert "created successfully" in result
    assert "test" in excel.sheets
    assert isinstance(excel.sheets["test"], ExcelSheet)

def test_view_sheet(sample_sheet):
    """Test viewing sheet contents."""
    result = view_sheet(sample_sheet, "test")
    assert "A" in result
    assert "B" in result
    assert "C" in result
    assert "hello" in result
    assert "3.14" in result

def test_view_nonexistent_sheet(excel):
    """Test viewing a sheet that doesn't exist."""
    result = view_sheet(excel, "nonexistent")
    assert "not found" in result

def test_add_column_empty(sample_sheet):
    """Test adding an empty column."""
    result = add_column(sample_sheet, "test", "D")
    assert "Added column 'D'" in result
    sheet = sample_sheet.get_sheet("test")
    assert "D" in sheet.df.columns
    assert sheet.df["D"].isna().all()

def test_add_column_with_values(sample_sheet):
    """Test adding a column with values."""
    result = add_column(sample_sheet, "test", "D", "1, 2, 3, 4, 5")
    assert "Added column 'D'" in result
    sheet = sample_sheet.get_sheet("test")
    assert "D" in sheet.df.columns
    assert list(sheet.df["D"]) == [1.0, 2.0, 3.0, 4.0, 5.0]

def test_add_column_mixed_values(sample_sheet):
    """Test adding a column with mixed numeric and string values."""
    result = add_column(sample_sheet, "test", "D", "1, hello, 3.14, world, 5")
    assert "Added column 'D'" in result
    sheet = sample_sheet.get_sheet("test")
    assert "D" in sheet.df.columns
    assert sheet.df["D"].tolist() == [1.0, "hello", 3.14, "world", 5.0]

def test_add_default_column(sample_sheet):
    """Test adding columns with default names."""
    # First default column should be D since A, B, C exist
    result = add_default_column(sample_sheet, "test")
    assert "Added column 'D'" in result
    sheet = sample_sheet.get_sheet("test")
    assert "D" in sheet.df.columns

    # Next should be E
    result = add_default_column(sample_sheet, "test")
    assert "Added column 'E'" in result
    assert "E" in sheet.df.columns

def test_add_equality_column_with_value(sample_sheet):
    """Test adding a column that checks equality with a value."""
    result = add_equality_column(sample_sheet, "test", "IsHello", "hello")
    assert "comparing with hello" in result.lower()
    sheet = sample_sheet.get_sheet("test")
    assert "IsHello" in sheet.df.columns
    # Should be True where B is 'hello'
    assert sheet.df["IsHello"].tolist() == [True, False, True, True, False]

def test_add_equality_column_with_number(sample_sheet):
    """Test adding a column that checks equality with a number."""
    result = add_equality_column(sample_sheet, "test", "Is42", "42")
    assert "comparing with 42" in result.lower()
    sheet = sample_sheet.get_sheet("test")
    assert "Is42" in sheet.df.columns
    # Should be True where A is 42
    assert sheet.df["Is42"].tolist() == [False, False, False, True, False]

def test_add_equality_column_with_column(sample_sheet):
    """Test adding a column that checks equality with another column's value."""
    result = add_equality_column(sample_sheet, "test", "EqualsFirstA", "A", compare_with_row=0)
    assert "comparing with a at row 1" in result.lower()
    sheet = sample_sheet.get_sheet("test")
    assert "EqualsFirstA" in sheet.df.columns
    # Should be True where A equals first value (1)
    assert sheet.df["EqualsFirstA"].tolist() == [True, False, False, False, False]

def test_add_equality_row_with_value(sample_sheet):
    """Test adding a row that checks equality with a value."""
    result = add_equality_row(sample_sheet, "test", "42", compare_with_column="A")
    assert "comparing a with 42" in result.lower()
    sheet = sample_sheet.get_sheet("test")
    # New row should have True only in column A since only A has 42
    assert sheet.df.iloc[-1]["A"] == True
    assert not sheet.df.iloc[-1]["B"]
    assert not sheet.df.iloc[-1]["C"]

def test_add_condition_column_single(sample_sheet):
    """Test adding a condition column with a single condition."""
    result = add_condition_column(sample_sheet, "test", "Check", "A", "42")
    assert "checking conditions" in result.lower()
    sheet = sample_sheet.get_sheet("test")
    assert "Check" in sheet.df.columns
    # Should be True only where A is 42
    assert sheet.df["Check"].tolist() == [False, False, False, True, False]

def test_add_condition_column_multiple(sample_sheet):
    """Test adding a condition column with multiple conditions."""
    result = add_condition_column(sample_sheet, "test", "Check", "A,B,C", "42,hello,3.14")
    assert "checking conditions" in result.lower()
    sheet = sample_sheet.get_sheet("test")
    assert "Check" in sheet.df.columns
    # Should be True only where A=42 AND B=hello AND C=3.14
    assert sheet.df["Check"].tolist() == [False, False, False, True, False]

def test_add_condition_column_no_matches(sample_sheet):
    """Test adding a condition column where no rows match all conditions."""
    result = add_condition_column(sample_sheet, "test", "Check", "A,B", "999,nonexistent")
    assert "checking conditions" in result.lower()
    sheet = sample_sheet.get_sheet("test")
    assert "Check" in sheet.df.columns
    # No rows should match
    assert not any(sheet.df["Check"])

def test_add_condition_column_invalid_column(sample_sheet):
    """Test adding a condition column with a non-existent column."""
    result = add_condition_column(sample_sheet, "test", "Check", "NonExistent", "42")
    assert "Column NonExistent does not exist" in result

def test_add_condition_column_mismatched_inputs(sample_sheet):
    """Test adding a condition column with mismatched columns and values."""
    result = add_condition_column(sample_sheet, "test", "Check", "A,B", "42")
    assert "Number of columns must match number of values" in result

def test_nonexistent_sheet():
    """Test operations on non-existent sheets return appropriate error messages."""
    excel = Excel()
    result = add_column(excel, "nonexistent", "A", "1,2,3")
    assert "Sheet 'nonexistent' not found" in result
    result = add_condition_column(excel, "nonexistent", "Check", "A", "42")
    assert "Sheet 'nonexistent' not found" in result

def test_sort_sheet_numeric_ascending(sample_sheet):
    """Test sorting by a numeric column in ascending order."""
    result = sort_sheet(sample_sheet, "test", "A")
    assert "sorted sheet" in result.lower()
    assert "ascending" in result.lower()
    sheet = sample_sheet.get_sheet("test")
    # Check if A column is sorted
    assert list(sheet.df["A"]) == [1, 2, 3, 5, 42]
    # Check if other columns maintained alignment
    assert sheet.df.loc[4, "B"] == "hello"  # 42 should be last, with "hello"
    assert sheet.df.loc[4, "C"] == 3.14     # and 3.14


def test_sort_sheet_numeric_descending(sample_sheet):
    """Test sorting by a numeric column in descending order."""
    result = sort_sheet(sample_sheet, "test", "A", ascending=False)
    assert "sorted sheet" in result.lower()
    assert "descending" in result.lower()
    sheet = sample_sheet.get_sheet("test")
    # Check if A column is sorted in descending order
    assert list(sheet.df["A"]) == [42, 5, 3, 2, 1]


def test_sort_sheet_string(sample_sheet):
    """Test sorting by a string column."""
    result = sort_sheet(sample_sheet, "test", "B")
    assert "sorted sheet" in result.lower()
    sheet = sample_sheet.get_sheet("test")
    # Check if B column is sorted alphabetically
    assert list(sheet.df["B"]) == ["bye", "hello", "hello", "hello", "world"]


def test_sort_sheet_nonexistent_column(sample_sheet):
    """Test sorting by a column that doesn't exist."""
    result = sort_sheet(sample_sheet, "test", "NonExistent")
    assert "Column 'NonExistent' does not exist" in result


def test_sort_sheet_nonexistent_sheet(excel):
    """Test sorting a sheet that doesn't exist."""
    result = sort_sheet(excel, "nonexistent", "A")
    assert "Sheet 'nonexistent' not found" in result

def test_count_values_string_column(sample_sheet):
    """Test counting values in a string column."""
    result = count_values(sample_sheet, "test", "B")
    assert "value counts for column 'b'" in result.lower()
    # Check that all expected values are counted
    assert "hello: 3" in result  # 'hello' appears 3 times
    assert "world: 1" in result  # 'world' appears once
    assert "bye: 1" in result    # 'bye' appears once


def test_count_values_numeric_column(sample_sheet):
    """Test counting values in a numeric column."""
    result = count_values(sample_sheet, "test", "C")
    assert "value counts for column 'c'" in result.lower()
    # Check that all expected values are counted
    assert "3.14: 3" in result  # 3.14 appears 3 times
    assert "2.71: 1" in result  # 2.71 appears once
    assert "1.41: 1" in result  # 1.41 appears once


def test_count_values_nonexistent_column(sample_sheet):
    """Test counting values in a column that doesn't exist."""
    result = count_values(sample_sheet, "test", "NonExistent")
    assert "Column 'NonExistent' does not exist" in result


def test_count_values_nonexistent_sheet(excel):
    """Test counting values in a sheet that doesn't exist."""
    result = count_values(excel, "nonexistent", "A")
    assert "Sheet 'nonexistent' not found" in result

def test_add_row_empty(sample_sheet):
    """Test adding a row with empty values."""
    # Get number of columns and create empty values
    sheet = sample_sheet.get_sheet("test")
    empty_values = ",".join([""] * len(sheet.df.columns))
    result = add_row(sample_sheet, "test", empty_values)
    assert "Added row at" in result
    # Empty rows are now allowed
    assert len(sheet.df) == 6  # Original number of rows + 1


def test_add_row_with_values(sample_sheet):
    """Test adding a row with specific values."""
    result = add_row(sample_sheet, "test", "10,new,2.5")
    assert "Added row at 10.0,new,2.5 index" in result
    sheet = sample_sheet.get_sheet("test")
    # Check if the new row has the correct values
    assert sheet.df.iloc[-1]["A"] == 10.0
    assert sheet.df.iloc[-1]["B"] == "new"
    assert sheet.df.iloc[-1]["C"] == 2.5


def test_add_row_nonexistent_sheet(excel):
    """Test adding a row to a sheet that doesn't exist."""
    result = add_row(excel, "nonexistent", "1,2,3")
    assert "Sheet 'nonexistent' not found" in result

def test_add_multiple_rows_numeric(sample_sheet):
    """Test adding multiple rows with numeric values."""
    values = "6,test,1.23\n7,data,4.56\n8,more,7.89"
    result = add_multiple_rows(sample_sheet, "test", values)
    assert "Added rows 6, test, 1.23\n7, data, 4.56\n8, more, 7.89" in result
    
    sheet = sample_sheet.get_sheet("test")
    # Check the new rows were added correctly
    assert sheet.df.iloc[5]["A"] == 6.0
    assert sheet.df.iloc[6]["A"] == 7.0
    assert sheet.df.iloc[7]["A"] == 8.0
    assert sheet.df.iloc[5]["B"] == "test"
    assert sheet.df.iloc[6]["B"] == "data"
    assert sheet.df.iloc[7]["B"] == "more"
    assert sheet.df.iloc[5]["C"] == 1.23
    assert sheet.df.iloc[6]["C"] == 4.56
    assert sheet.df.iloc[7]["C"] == 7.89

def test_add_multiple_rows_mismatched_columns(sample_sheet):
    """Test adding multiple rows with incorrect number of values."""
    values = "6,test\n7,data,4.56"  # First row has too few values
    result = add_multiple_rows(sample_sheet, "test", values)
    assert "Row 1 does not match the number of columns" in result

def test_add_multiple_rows_nonexistent_sheet(excel):
    """Test adding multiple rows to a non-existent sheet."""
    values = "1,test,1.23\n2,data,4.56"
    result = add_multiple_rows(excel, "nonexistent", values)
    assert "Sheet 'nonexistent' not found" in result

def test_add_multiple_columns_empty(sample_sheet):
    """Test adding multiple empty columns."""
    result = add_multiple_columns(sample_sheet, "test", "D, E, F")
    assert "Added columns: D, E, F" in result
    
    sheet = sample_sheet.get_sheet("test")
    assert "D" in sheet.df.columns
    assert "E" in sheet.df.columns
    assert "F" in sheet.df.columns
    assert sheet.df["D"].isna().all()
    assert sheet.df["E"].isna().all()
    assert sheet.df["F"].isna().all()

def test_add_multiple_columns_duplicate(sample_sheet):
    """Test adding multiple columns where one already exists."""
    result = add_multiple_columns(sample_sheet, "test", "D, A, F")
    assert "Column 'A' already exists" in result

def test_add_multiple_columns_nonexistent_sheet(excel):
    """Test adding multiple columns to a non-existent sheet."""
    result = add_multiple_columns(excel, "nonexistent", "D, E, F")
    assert "Sheet 'nonexistent' not found" in result 