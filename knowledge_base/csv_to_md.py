import pandas as pd
import argparse
from pathlib import Path
import re
import csv

def clean_text(text):
    """Clean and format text for markdown."""
    if pd.isna(text):
        return ""
    # Convert to string if not already
    text = str(text)
    # Remove surrounding quotes if present
    text = text.strip('"')
    # Replace double quotes with single quotes
    text = text.replace('""', '"')
    # Escape markdown special characters
    special_chars = ['*', '#', '_', '`', '>', '|', '[', ']', '(', ')', '+', '-', '.', '!']
    for char in special_chars:
        text = text.replace(char, '\\' + char)
    return text

def read_problematic_csv(file_path, expected_columns):
    """
    Read CSV file with custom handling for problematic rows.
    
    Args:
        file_path (str): Path to the CSV file
        expected_columns (int): Expected number of columns
    
    Returns:
        pd.DataFrame: DataFrame with the CSV content
    """
    # First try to read with specific parameters
    try:
        return pd.read_csv(file_path, 
                         sep=',',
                         quoting=csv.QUOTE_ALL,
                         doublequote=True,
                         quotechar='"')
    except pd.errors.ParserError:
        # If normal reading fails, use manual parsing
        rows = []
        problem_rows = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # Get header and properly handle quotes
            header_line = f.readline().strip()
            # Correctly divide header line
            header = header_line.split(',"')
            header[0] = header[0].strip('"')  # Handle with first column
            header = [col.strip('"') for col in header]  # Handle with other columns
            
            # Read remaining lines
            for line_num, line in enumerate(f, start=2):
                try:
                    # 使用相同的分割邏輯處理每一行
                    fields = line.strip().split(',"')
                    fields[0] = fields[0].strip('"')
                    fields = [field.strip('"') for field in fields]
                    
                    if len(fields) == len(header):
                        rows.append(fields)
                    else:
                        problem_rows.append(line_num)
                        # Make sure the number of columns is correct
                        if len(fields) > len(header):
                            fields = fields[:len(header)]
                        else:
                            fields.extend([''] * (len(header) - len(fields)))
                        rows.append(fields)
                except Exception as e:
                    problem_rows.append(line_num)
                    print(f"Warning: Error parsing line {line_num}: {str(e)}")
                    continue
        
        if problem_rows:
            print(f"Warning: Found and fixed problematic rows at lines: {problem_rows}")
        
        # Create DataFrame with clean column names
        df = pd.DataFrame(rows, columns=header)
        print("Available columns:", df.columns.tolist())
        return df

def csv_to_markdown(input_file, output_file, selected_fields=None, chunk_size=None):
    """
    Convert CSV file to Markdown format with selected fields.
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output Markdown file
        selected_fields (list): List of field names to include in output
        chunk_size (int): Optional size for chunking the output into multiple files
    """
    # Read CSV file with custom handler
    df = read_problematic_csv(input_file, 23)
    
    # Print available fields for debugging
    print("Available fields in DataFrame:", df.columns.tolist())
    
    # If no fields specified, use all fields
    if not selected_fields:
        selected_fields = df.columns.tolist()
    else:
        # Verify all selected fields exist
        missing_fields = [field for field in selected_fields if field not in df.columns]
        if missing_fields:
            raise ValueError(f"Fields not found in CSV file: {missing_fields}")
    
    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def write_chunk(chunk_df, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            for _, row in chunk_df.iterrows():
                try:
                    # Write title as header
                    f.write(f"# {clean_text(row['title'])}\n\n")
                    
                    # Write each selected field
                    for field in selected_fields:
                        if field != 'title':  # Skip title as it's already used as header
                            value = row[field]
                            if pd.notna(value) and str(value).strip():  # Check if value exists and is not empty
                                f.write(f"## {field}\n")
                                f.write(f"{clean_text(value)}\n\n")
                    
                    f.write("---\n\n")  # Add separator between entries
                except Exception as e:
                    print(f"Warning: Error processing row with title '{row.get('title', 'Unknown')}': {str(e)}")
                    continue
    
    if chunk_size:
        # Split into multiple files
        for i, chunk_start in enumerate(range(0, len(df), chunk_size)):
            chunk_df = df[chunk_start:chunk_start + chunk_size]
            chunk_path = output_path.parent / f"{output_path.stem}_{i + 1}{output_path.suffix}"
            write_chunk(chunk_df, chunk_path)
    else:
        # Write to single file
        write_chunk(df, output_path)

def main():
    parser = argparse.ArgumentParser(description='Convert CSV to Markdown format')
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('output_file', help='Output Markdown file path')
    parser.add_argument('--fields', nargs='+', help='Fields to include in output (space-separated)')
    parser.add_argument('--chunk-size', type=int, help='Number of entries per output file')
    
    args = parser.parse_args()
    
    try:
        csv_to_markdown(args.input_file, args.output_file, args.fields, args.chunk_size)
        print(f"Successfully converted {args.input_file} to Markdown format")
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == '__main__':
    main()
