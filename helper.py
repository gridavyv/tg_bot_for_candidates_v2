#!/usr/bin/env python3
"""
Helper script to process user_actions.json and organize data by user_id.
Sorts actions by timestamp and includes answers/reasons if available.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


def read_user_actions(file_path: str) -> List[Dict[str, Any]]:
    """
    Read user_actions.json file and return the data as a list of dictionaries.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        List[Dict[str, Any]]: List of action dictionaries
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


def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse timestamp string to datetime object for sorting.
    
    Args:
        timestamp_str (str): ISO format timestamp string
        
    Returns:
        datetime: Parsed datetime object
    """
    try:
        # Handle ISO format with timezone
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError:
        # Fallback for different timestamp formats
        try:
            return datetime.fromisoformat(timestamp_str)
        except ValueError:
            print(f"Warning: Could not parse timestamp: {timestamp_str}")
            return datetime.min


def organize_actions_by_user(actions: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """
    Organize actions by user_id and sort by timestamp.
    
    Args:
        actions (List[Dict[str, Any]]): List of action dictionaries
        
    Returns:
        Dict[int, List[Dict[str, Any]]]: Dictionary with user_id as key and sorted actions as values
    """
    user_actions = {}
    
    for action in actions:
        user_id = action.get('user_id')
        if user_id is None:
            continue
            
        # Create action entry with all relevant fields
        action_entry = {
            'action_type': action.get('action_type', ''),
            'timestamp': action.get('timestamp', ''),
            'answer': action.get('answer'),
            'reason': action.get('reason')
        }
        
        # Remove None values to keep the dictionary clean
        action_entry = {k: v for k, v in action_entry.items() if v is not None}
        
        # Add to user's actions
        if user_id not in user_actions:
            user_actions[user_id] = []
        user_actions[user_id].append(action_entry)
    
    # Sort actions by timestamp for each user
    for user_id in user_actions:
        user_actions[user_id].sort(
            key=lambda x: parse_timestamp(x.get('timestamp', ''))
        )
    
    return user_actions


def save_organized_data(data: Dict[int, List[Dict[str, Any]]], output_file: str) -> bool:
    """
    Save organized data to a JSON file.
    
    Args:
        data (Dict[int, List[Dict[str, Any]]]): Organized user actions data
        output_file (str): Path to the output JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving data to '{output_file}': {e}")
        return False


def print_summary(data: Dict[int, List[Dict[str, Any]]]) -> None:
    """
    Print a summary of the organized data.
    
    Args:
        data (Dict[int, List[Dict[str, Any]]]): Organized user actions data
    """
    print(f"\nSummary:")
    print(f"Total users: {len(data)}")
    
    total_actions = sum(len(actions) for actions in data.values())
    print(f"Total actions: {total_actions}")
    
    print(f"\nActions per user:")
    for user_id, actions in data.items():
        print(f"  User {user_id}: {len(actions)} actions")
        
        # Show first few action types for each user
        action_types = [action['action_type'] for action in actions[:3]]
        if len(actions) > 3:
            action_types.append("...")
        print(f"    Sample actions: {', '.join(action_types)}")


def main():
    """
    Main function to execute the user actions organization.
    """
    # Define file paths
    input_file = "user_actions.json"
    output_file = "organized_user_actions.json"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found in current directory.")
        return
    
    # Read user actions data
    print(f"Reading data from '{input_file}'...")
    actions = read_user_actions(input_file)
    
    if not actions:
        print("No data found or error reading file.")
        return
    
    print(f"Found {len(actions)} actions")
    
    # Organize actions by user
    print("Organizing actions by user_id and sorting by timestamp...")
    organized_data = organize_actions_by_user(actions)
    
    # Save organized data
    print(f"Saving organized data to '{output_file}'...")
    success = save_organized_data(organized_data, output_file)
    
    if success:
        print("Data organization completed successfully!")
        print_summary(organized_data)
        print(f"\nOutput file: {output_file}")
        
        # Show sample of organized data
        if organized_data:
            sample_user = list(organized_data.keys())[0]
            print(f"\nSample data for user {sample_user}:")
            sample_actions = organized_data[sample_user][:3]  # Show first 3 actions
            for i, action in enumerate(sample_actions, 1):
                print(f"  {i}. {action['action_type']} at {action['timestamp']}")
                if 'answer' in action:
                    print(f"     Answer: {action['answer']}")
                if 'reason' in action:
                    print(f"     Reason: {action['reason']}")
    else:
        print("Data organization failed.")


if __name__ == "__main__":
    main()
