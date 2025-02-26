import streamlit as st
import os
import json
import time
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Import functions from existing scripts
from discord_export import (
    check_docker, export_discord_channel, compress_conversation,
    load_last_timestamp, save_last_timestamp, get_most_recent_timestamp
)

# Set page config
st.set_page_config(
    page_title="Discord Chat Analyzer",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to save API keys to .env file
def save_keys_to_env(discord_token, gemini_api_key):
    with open(".env", "w") as f:
        f.write(f"DISCORD_TOKEN={discord_token}\n")
        f.write(f"GEMINI_API_KEY={gemini_api_key}\n")
    load_dotenv(override=True)

# Function to setup Gemini model
def setup_gemini_model():
    """Configure and return Gemini model instance."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Gemini API key not found. Please provide it in the settings.")
        return None
    
    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
        system_instruction="You are an AI assistant that analyzes Discord conversation data. Provide insights, summaries, and answer questions about the conversations.",
    )

    return model.start_chat(history=[])

# Sidebar for settings
with st.sidebar:
    st.title("⚙️ Settings")
    
    # API Keys section
    st.subheader("API Keys")
    discord_token = st.text_input("Discord Token", value=os.getenv("DISCORD_TOKEN", ""), type="password", 
                                 help="Your Discord authentication token. Learn how to get it in the Token-and-IDs guide.")
    
    gemini_api_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password",
                                  help="Your Google Gemini API key.")
    
    if st.button("Save API Keys"):
        save_keys_to_env(discord_token, gemini_api_key)
        st.success("API keys saved successfully!")
    
    # Docker Status
    st.subheader("Docker Status")
    docker_status = check_docker()
    if docker_status:
        st.success("Docker is running")
    else:
        st.error("Docker is not running or not installed")
        st.info("This tool requires Docker to be installed and running. Please check the Docker installation guide.")

# Main content
st.title("Discord Chat Analyzer")
st.markdown("Export and analyze your Discord conversations with AI assistance.")

# Tabs for different functions
tab1, tab2, tab3 = st.tabs(["Export", "View Conversations", "Analyze"])

# Export tab
with tab1:
    st.header("Export Discord Conversations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        channel_id = st.text_input("Channel ID", help="The ID of the Discord channel you want to export.")
        
        # Date range selection
        date_options = st.radio("Export Range", ["Full History", "Date Range", "Incremental (since last export)"])
        
        if date_options == "Date Range":
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
        else:
            start_date = None
            end_date = None
    
    with col2:
        st.subheader("Export Options")
        export_format = st.selectbox("Export Format", ["Json", "HtmlDark", "HtmlLight", "Csv", "PlainText"], index=0)
        download_media = st.checkbox("Download Media (images, avatars, etc.)", value=False)
        include_threads = st.selectbox("Include Threads", ["none", "active", "all"], index=0)
        
    export_button = st.button("Export Conversation", use_container_width=True, type="primary")
    
    if export_button:
        if not channel_id:
            st.error("Please provide a Channel ID")
        elif not os.getenv("DISCORD_TOKEN"):
            st.error("Please provide a Discord Token in the settings")
        elif not docker_status:
            st.error("Docker is required but not available")
        else:
            # Set up progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Create output directory
            output_dir = os.path.join(os.getcwd(), "team_chat")
            os.makedirs(output_dir, exist_ok=True)
            
            # Determine start date for incremental export
            if date_options == "Incremental (since last export)":
                last_timestamp = load_last_timestamp(channel_id)
                if last_timestamp:
                    start_date_str = last_timestamp
                    status_text.info(f"Performing incremental export from {start_date_str}")
                else:
                    status_text.info("No previous export found. Performing full export.")
                    start_date_str = None
            elif date_options == "Date Range":
                start_date_str = start_date.isoformat()
                end_date_str = end_date.isoformat()
            else:
                start_date_str = None
                end_date_str = None
            
            progress_bar.progress(25, text="Starting export...")
            
            # Prepare export command
            docker_cmd = [
                'docker', 'run', '--rm',
                '-v', f"{output_dir}:/out",
                'tyrrrz/discordchatexporter:stable', 'export',
                '-f', export_format,
                '-c', channel_id,
                '-t', os.getenv("DISCORD_TOKEN")
            ]
            
            # Add date range if specified
            if start_date_str:
                docker_cmd.extend(['--after', start_date_str])
            if date_options == "Date Range" and end_date_str:
                docker_cmd.extend(['--before', end_date_str])
                
            # Add media download option if selected
            if download_media:
                docker_cmd.append('--media')
                
            # Add threads option if not none
            if include_threads != "none":
                docker_cmd.extend(['--include-threads', include_threads])
            
            # Execute export
            try:
                status_text.info("Exporting conversation... (this may take a while for large channels)")
                subprocess.run(docker_cmd, check=True)
                progress_bar.progress(75, text="Processing export...")
                
                # Wait for file to be fully written
                time.sleep(2)
                
                # Find the exported file
                if export_format == "Json":
                    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json') and channel_id in f]
                    if json_files:
                        json_path = os.path.join(output_dir, json_files[0])
                        
                        # Update timestamp for incremental exports
                        try:
                            with open(json_path, "r", encoding="utf-8") as f:
                                conversation = json.load(f)
                                
                            latest_timestamp = get_most_recent_timestamp(conversation)
                            if latest_timestamp:
                                save_last_timestamp(channel_id, latest_timestamp)
                        except Exception as e:
                            status_text.error(f"Error processing JSON: {str(e)}")
                
                progress_bar.progress(100, text="Export completed!")
                st.success(f"Conversation exported successfully to: {output_dir}")
                
            except subprocess.CalledProcessError as e:
                progress_bar.empty()
                st.error(f"Export failed: {str(e)}")
            except Exception as e:
                progress_bar.empty()
                st.error(f"An error occurred: {str(e)}")

# View Conversations tab
with tab2:
    st.header("View Exported Conversations")
    
    output_dir = os.path.join(os.getcwd(), "team_chat")
    os.makedirs(output_dir, exist_ok=True)
    
    # List all exported files
    exported_files = []
    for f in os.listdir(output_dir):
        file_path = os.path.join(output_dir, f)
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            exported_files.append({
                "name": f,
                "path": file_path,
                "size": f"{file_size:.2f} MB",
                "modified": modified_time.strftime("%Y-%m-%d %H:%M:%S")
            })
    
    # Display files in a table
    if exported_files:
        st.dataframe(exported_files, 
                     column_config={
                         "name": "Filename",
                         "size": "Size",
                         "modified": "Last Modified",
                         "path": st.column_config.Column(
                             "File Path",
                             disabled=True
                         )
                     },
                     use_container_width=True)
        
        # View file contents
        selected_file = st.selectbox("Select a file to view:", 
                                   [f["name"] for f in exported_files],
                                   index=None)
        
        if selected_file:
            file_path = os.path.join(output_dir, selected_file)
            try:
                if selected_file.endswith('.json'):
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # Show conversation summary
                    st.subheader("Conversation Summary")
                    
                    # Basic info
                    if "guild" in data:
                        st.info(f"Server: {data.get('guild', {}).get('name', 'Unknown')}")
                    
                    st.info(f"Channel: {data.get('channel', {}).get('name', 'Unknown')}")
                    st.info(f"Message Count: {len(data.get('messages', []))}")
                    
                    # Show messages
                    st.subheader("Messages")
                    
                    with st.expander("View Messages", expanded=False):
                        for msg in data.get("messages", [])[:100]:  # Limit to first 100 messages
                            author = msg.get("author", {}).get("nickname") or msg.get("author", {}).get("name", "Unknown")
                            timestamp = msg.get("timestamp", "")
                            content = msg.get("content", "").strip()
                            
                            if content:
                                st.markdown(f"**{author}** ({timestamp}):")
                                st.markdown(content)
                                st.divider()
                        
                        if len(data.get("messages", [])) > 100:
                            st.info("Only showing the first 100 messages. The full conversation is available for analysis.")
                
                elif selected_file.endswith('.html'):
                    st.warning("HTML files can't be previewed here. Please open the file in a web browser.")
                    
                elif selected_file.endswith('.txt') or selected_file.endswith('.csv'):
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    st.text(content[:10000] + ("..." if len(content) > 10000 else ""))
                
                else:
                    st.warning(f"Preview not available for this file type: {selected_file}")
                
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    else:
        st.info("No exported files found. Use the Export tab to export conversations first.")
        
# Analyze tab
with tab3:
    st.header("AI Analysis")
    
    output_dir = os.path.join(os.getcwd(), "team_chat")
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    
    if not json_files:
        st.info("No conversation files found. Please export a conversation first.")
    else:
        # Select file to analyze
        selected_file = st.selectbox("Select conversation to analyze:", 
                                   json_files,
                                   index=None)
        
        if selected_file:
            if not os.getenv("GEMINI_API_KEY"):
                st.error("Please add your Gemini API key in Settings to use AI analysis.")
            else:
                try:
                    json_path = os.path.join(output_dir, selected_file)
                    with open(json_path, "r", encoding="utf-8") as f:
                        conversation = json.load(f)
                    
                    # Compress conversation for analysis
                    st.info("Preparing conversation for analysis...")
                    summary = compress_conversation(conversation)
                    
                    # Initialize the Gemini model for chat
                    chat_session = setup_gemini_model()
                    if chat_session:
                        # Send initial context message
                        with st.spinner("Initializing AI analysis..."):
                            context_prompt = f"""Here's a Discord conversation summary to analyze:

{summary[:50000]}  # Limiting to 50K chars to avoid token limits

Please keep your responses focused on the content of this conversation."""
                            
                            response = chat_session.send_message(context_prompt)
                        
                        st.success("AI analysis ready! Ask questions about the conversation.")
                        
                        # Create chat interface
                        query = st.text_input("Ask a question about this conversation:")
                        if query:
                            with st.spinner("Analyzing..."):
                                try:
                                    response = chat_session.send_message(query)
                                    st.markdown(response.text)
                                except Exception as e:
                                    st.error(f"Error getting AI response: {str(e)}")
                        
                        # Suggested questions
                        st.markdown("### Suggested questions:")
                        suggested_questions = [
                            "What are the main topics discussed in this conversation?",
                            "Summarize the key points from this conversation.",
                            "Who are the most active participants?",
                            "Are there any decisions or action items in this conversation?",
                            "What's the overall sentiment of this conversation?"
                        ]
                        
                        for q in suggested_questions:
                            if st.button(q):
                                with st.spinner("Analyzing..."):
                                    try:
                                        response = chat_session.send_message(q)
                                        st.markdown(response.text)
                                    except Exception as e:
                                        st.error(f"Error getting AI response: {str(e)}")
                except Exception as e:
                    st.error(f"Error processing conversation: {str(e)}")

# Footer
st.divider()
st.markdown("""
### Help & Resources

- This tool uses [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter) with Docker to export Discord conversations.
- To get your Discord Token and Channel IDs, check the [Token-and-IDs guide](https://github.com/Tyrrrz/DiscordChatExporter/blob/master/.docs/Token-and-IDs.md).
- Analysis is powered by Google's Gemini AI. You'll need a Gemini API key from [Google AI Studio](https://makersuite.google.com/).
- Docker is required for this application to function properly.
""")