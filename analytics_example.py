"""
Example analytics script to demonstrate how to use the action tracking data
"""
from action_tracker import get_user_actions, get_user_action_summary
import json
from pathlib import Path


def analyze_user_engagement():
    """Analyze user engagement patterns"""
    actions_file = Path("user_actions.json")
    
    if not actions_file.exists():
        print("No action data found. Run the bot first to collect data.")
        return
    
    # Load all actions
    with open(actions_file, 'r', encoding='utf-8') as f:
        all_actions = json.load(f)
    
    if not all_actions:
        print("No actions recorded yet.")
        return
    
    # Get unique users
    user_ids = set(action.get("user_id") for action in all_actions if action.get("user_id"))
    
    print(f"📊 Analytics Report - {len(user_ids)} unique users")
    print("=" * 50)
    
    # Overall statistics
    action_counts = {}
    for action in all_actions:
        action_type = action.get("action_type", "unknown")
        action_counts[action_type] = action_counts.get(action_type, 0) + 1
    
    print("\n📈 Action Frequency:")
    for action_type, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {action_type}: {count}")
    
    # User journey analysis
    print(f"\n👥 User Journey Analysis:")
    print("-" * 30)
    
    for user_id in sorted(user_ids):
        summary = get_user_action_summary(user_id)
        print(f"\nUser {user_id}:")
        print(f"  Total actions: {summary['total_actions']}")
        print(f"  First action: {summary['first_action']}")
        print(f"  Last action: {summary['last_action']}")
        
        # Check completion status
        actions = summary['actions']
        action_types = [action.get('action_type') for action in actions]
        
        completion_status = "❌ Incomplete"
        if "sent_video" in action_types and "answered_confirm_sending" in action_types:
            if any(action.get('action_type') == 'answered_confirm_sending' and 
                   action.get('answer') == 'confirm_yes' for action in actions):
                completion_status = "✅ Completed"
        
        print(f"  Status: {completion_status}")
        
        # Show key milestones
        milestones = []
        if "start" in action_types:
            milestones.append("🚀 Started")
        if "got_video" in action_types:
            milestones.append("📹 Got video")
        if "answered_about_watched_video" in action_types:
            milestones.append("👀 Watched video")
        if "answered_to_shoot_video" in action_types:
            shoot_answer = next((action.get('answer') for action in actions 
                               if action.get('action_type') == 'answered_to_shoot_video'), None)
            if shoot_answer == "yes":
                milestones.append("✅ Wants to shoot")
            elif shoot_answer in ["maybe", "no"]:
                milestones.append("🤔 Hesitant/Rejected")
        if "got_instructions" in action_types:
            milestones.append("📋 Got instructions")
        if "sent_video" in action_types:
            milestones.append("📤 Sent video")
        if "answered_confirm_sending" in action_types:
            confirm_answer = next((action.get('answer') for action in actions 
                                 if action.get('action_type') == 'answered_confirm_sending'), None)
            if confirm_answer == "confirm_yes":
                milestones.append("✅ Confirmed sending")
            else:
                milestones.append("❌ Rejected sending")
        
        print(f"  Journey: {' → '.join(milestones)}")


def analyze_drop_off_points():
    """Analyze where users drop off in the funnel"""
    actions_file = Path("user_actions.json")
    
    if not actions_file.exists():
        print("No action data found.")
        return
    
    with open(actions_file, 'r', encoding='utf-8') as f:
        all_actions = json.load(f)
    
    # Group actions by user
    user_actions = {}
    for action in all_actions:
        user_id = action.get("user_id")
        if user_id:
            if user_id not in user_actions:
                user_actions[user_id] = []
            user_actions[user_id].append(action)
    
    # Define the expected funnel
    funnel_steps = [
        "start",
        "got_video", 
        "answered_about_watched_video",
        "answered_to_shoot_video",
        "got_instructions",
        "sent_video",
        "answered_confirm_sending"
    ]
    
    print("\n📉 Funnel Analysis:")
    print("-" * 20)
    
    step_counts = {}
    for step in funnel_steps:
        count = 0
        for user_id, actions in user_actions.items():
            action_types = [action.get('action_type') for action in actions]
            if step in action_types:
                count += 1
        step_counts[step] = count
        print(f"{step}: {count} users")
    
    # Calculate drop-off rates
    print("\n📊 Drop-off Analysis:")
    print("-" * 25)
    
    total_users = len(user_actions)
    print(f"Total users: {total_users}")
    
    for i, step in enumerate(funnel_steps):
        if i == 0:
            continue
        
        prev_step = funnel_steps[i-1]
        current_count = step_counts[step]
        prev_count = step_counts[prev_step]
        
        if prev_count > 0:
            drop_off_rate = ((prev_count - current_count) / prev_count) * 100
            print(f"{prev_step} → {step}: {drop_off_rate:.1f}% drop-off")


if __name__ == "__main__":
    print("🤖 Telegram Bot Analytics")
    print("=" * 30)
    
    analyze_user_engagement()
    analyze_drop_off_points()
    
    print("\n💡 Tips:")
    print("- Run this script after users interact with your bot")
    print("- Check user_actions.json for raw data")
    print("- Use this data to optimize your bot's user experience")
