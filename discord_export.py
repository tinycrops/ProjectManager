#!/usr/bin/env python3
import json
import os
import subprocess
import argparse
from dotenv import load_dotenv

def check_docker():
    """Check if Docker is installed and running."""
    try:
        subprocess.run(['docker', 'info'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Docker is not installed or not running.")
        return False

def export_discord_channel(channel_id, output_dir, discord_token, start_date=None, end_date=None):
    """Export Discord channel using DiscordChatExporter.
    
    Args:
        channel_id (str): Discord channel ID to export
        output_dir (str): Directory to save the exported files
        discord_token (str): Discord authentication token
        start_date (str, optional): Start date in ISO format (e.g., "2023-01-01")
        end_date (str, optional): End date in ISO format (e.g., "2023-12-31")
    """
    docker_cmd = [
        'docker', 'run', '--rm',
        '-v', f"{output_dir}:/out",
        '--env', f"DISCORD_TOKEN={discord_token}",
        'tyrrrz/discordchatexporter:stable', 'export',
        '-f', 'Json',
        '-c', channel_id,
        '-t', discord_token
    ]
    
    # Add time range arguments if provided
    if start_date:
        docker_cmd.extend(['--after', start_date])
    if end_date:
        docker_cmd.extend(['--before', end_date])
    
    try:
        subprocess.run(docker_cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        print("Error: Failed to export Discord channel.")
        return False

def compress_conversation(conversation):
    """Create a compressed summary of conversation messages."""
    summary_lines = []
    for msg in conversation.get("messages", []):
        content = msg.get("content", "").strip()
        if content:
            author = msg.get("author", {}).get("nickname", 
                    msg.get("author", {}).get("name", "Unknown"))
            timestamp = msg.get("timestamp", "")
            summary_lines.append(f"- {author} ({timestamp}): {content}")
    return "\n".join(summary_lines)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Export and compress Discord channel conversation')
    parser.add_argument('channel_id', help='Discord channel ID to export')
    parser.add_argument('-o', '--output', help='Output filename', default='team_chat.md')
    args = parser.parse_args()

    # Load environment variables from .env file
    load_dotenv()
    discord_token = os.getenv('DISCORD_TOKEN')
    
    if not discord_token:
        print("Error: DISCORD_TOKEN not found in .env file")
        return

    # Set up directories
    output_dir = os.path.join(os.getcwd(), "team_chat")
    os.makedirs(output_dir, exist_ok=True)

    # Check Docker and export channel
    if not check_docker():
        return

    if not export_discord_channel(args.channel_id, output_dir, discord_token):
        return

    # Find and process the exported JSON file for the specific channel
    import time
    time.sleep(2)  # Wait a bit for the file to be fully written
    
    # Look for a file containing the channel ID
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    matching_files = [f for f in json_files if args.channel_id in f]
    
    if not matching_files:
        print(f"Error: No JSON file found containing channel ID: {args.channel_id}")
        print("Files in directory:", json_files)
        return
        
    if len(matching_files) > 1:
        print(f"Warning: Multiple matching files found, using the first one: {matching_files}")
        
    json_path = os.path.join(output_dir, matching_files[0])
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            conversation = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON file: {json_path}")
        return
    except FileNotFoundError:
        print(f"Error: File not found: {json_path}")
        return

    # Create and save the summary
    summary = compress_conversation(conversation)
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("# Compressed Conversation Summary\n\n")
            f.write(summary)
        print(f"Compressed conversation written to {args.output}")
    except IOError as e:
        print(f"Error writing to output file: {e}")

if __name__ == "__main__":
    main()
