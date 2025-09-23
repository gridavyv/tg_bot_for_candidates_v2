#!/usr/bin/env python3
"""
Helper script to convert applicant_users.json to CSV format.
Creates a CSV file with columns: user_id, username, first_name, last_name, language_code
"""

import json
import csv
import os
from typing import List, Dict, Any


def read_json_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Read JSON file and return the data as a list of dictionaries.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        List[Dict[str, Any]]: List of user dictionaries
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{file_path}': {e}")
        return []
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return []


def convert_to_csv(data: List[Dict[str, Any]], output_file: str) -> bool:
    """
    Convert JSON data to CSV format.
    
    Args:
        data (List[Dict[str, Any]]): List of user dictionaries
        output_file (str): Path to the output CSV file
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not data:
        print("No data to convert.")
        return False
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            # Define the fieldnames in the specified order
            fieldnames = ['user_id', 'username', 'first_name', 'last_name', 'language_code']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write the header
            writer.writeheader()
            
            # Write the data rows
            for user in data:
                # Handle None values by converting them to empty strings
                row = {}
                for field in fieldnames:
                    value = user.get(field)
                    row[field] = '' if value is None else str(value)
                writer.writerow(row)
        
        print(f"Successfully converted {len(data)} records to '{output_file}'")
        return True
        
    except Exception as e:
        print(f"Error writing CSV file '{output_file}': {e}")
        return False


def main():
    """
    Main function to execute the JSON to CSV conversion.
    """
    # Define file paths
    json_file = "applicant_users.json"
    csv_file = "applicant_users.csv"
    
    # Check if JSON file exists
    if not os.path.exists(json_file):
        print(f"Error: JSON file '{json_file}' not found in current directory.")
        return
    
    # Read JSON data
    print(f"Reading data from '{json_file}'...")
    data = read_json_file(json_file)
    
    if not data:
        print("No data found or error reading file.")
        return
    
    # Convert to CSV
    print(f"Converting to CSV format...")
    success = convert_to_csv(data, csv_file)
    
    if success:
        print(f"Conversion completed successfully!")
        print(f"Output file: {csv_file}")
    else:
        print("Conversion failed.")


if __name__ == "__main__":
    main()
