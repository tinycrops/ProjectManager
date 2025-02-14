#!/usr/bin/env python3
import json
import os
import subprocess
import argparse
from dotenv import load_dotenv
import google.generativeai as genai

# Import the export functions from discord-export.py
from discord_export import check_docker, export_discord_channel, compress_conversation

def setup_gemini_model():
    """Configure and return Gemini model instance."""
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
        system_instruction="You are an AI assistant that analyzes Discord conversation data. Provide insights, summaries, and answer questions about the conversations."
    )

    return model.start_chat(history=[])

def analyze_conversation(chat_session, conversation_summary):
    """Interactive conversation analysis with Gemini."""
    # Initial context setting
    context_prompt = f"""Here's a Discord conversation summary to analyze. I'll be asking questions about it:

{conversation_summary}

Please keep your responses focused on the content of this conversation."""

    chat_session.send_message(context_prompt)
    
    print("\nConversation loaded! You can now ask questions about it.")
    print("Type 'quit' or 'exit' to end the session.\n")

    while True:
        question = input("\nWhat would you like to know about the conversation? > ")
        
        if question.lower() in ['quit', 'exit']:
            break
            
        try:
            response = chat_session.send_message(question)
            print("\nAnalysis:", response.text)
        except Exception as e:
            print(f"\nError getting response: {e}")

def main():
    parser = argparse.ArgumentParser(description='Export Discord chat and analyze with Gemini')
    parser.add_argument('channel_id', help='Discord channel ID to export')
    parser.add_argument('-o', '--output', help='Output filename', default='analysis_report.md')
    parser.add_argument('--start-date', help='Start date in ISO format (e.g., "2023-01-01")')
    parser.add_argument('--end-date', help='End date in ISO format (e.g., "2023-12-31")')
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()
    discord_token = os.getenv('DISCORD_TOKEN')
    
    if not discord_token:
        print("Error: DISCORD_TOKEN not found in .env file")
        return

    # Set up directories
    output_dir = os.path.join(os.getcwd(), "team_chat")
    os.makedirs(output_dir, exist_ok=True)

    # Export Discord chat
    if not check_docker():
        return

    if not export_discord_channel(args.channel_id, output_dir, discord_token, 
                                args.start_date, args.end_date):
        return

    # Process exported JSON
    print("Waiting for export to complete...")
    import time
    time.sleep(5)  # Increased delay to 5 seconds
    
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    matching_files = [f for f in json_files if args.channel_id in f]
    
    if not matching_files:
        print(f"Error: No JSON file found containing channel ID: {args.channel_id}")
        return
        
    json_path = os.path.join(output_dir, matching_files[0])
    print(f"Processing exported conversation from: {json_path}")
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            conversation = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error processing JSON file: {e}")
        return

    # Compress conversation and analyze with Gemini
    print("Compressing conversation...")
    summary = compress_conversation(conversation)
    
    print("Initializing Gemini model...")
    chat_session = setup_gemini_model()
    
    print("Starting interactive analysis...")
    try:
        analyze_conversation(chat_session, summary)
    except Exception as e:
        print(f"Error during interactive session: {e}")
        return

    # Add final delay to ensure Gemini completes
    time.sleep(2)

if __name__ == "__main__":
    main()