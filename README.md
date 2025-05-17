# Discord Chat Analyzer

A user-friendly GUI for exporting and analyzing Discord conversations, built with Streamlit and powered by the DiscordChatExporter tool and Google's Gemini AI.

## Features

- **Export Discord Conversations**: Export chat history from any Discord channel with various format options
- **Incremental Exports**: Update conversation exports by only fetching new messages
- **View Exported Files**: Browse and preview exported conversation files
- **AI Analysis**: Ask questions about the conversation and get AI-powered insights
- **User-Friendly Interface**: No command line knowledge required

## Prerequisites

- **Docker**: Required for running DiscordChatExporter
- **Discord Token**: Your Discord authentication token
- **Gemini API Key**: Google Gemini API key for conversation analysis

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/discord-chat-analyzer.git
   cd discord-chat-analyzer
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

   This will install the required packages including `google-genai`, the official Python SDK for the Gemini API.

3. Verify Docker is installed and running:
   ```
   docker --version
   ```

## Usage

1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Open your web browser to the provided URL (typically http://localhost:8501)

3. In the Settings panel:
   - Enter your Discord Token
   - Enter your Gemini API Key
   - Click "Save API Keys"

4. Use the Export tab to export Discord conversations:
   - Enter the Channel ID you want to export
   - Choose export options (format, date range, etc.)
   - Click "Export Conversation"

5. Use the View Conversations tab to browse exported files

6. Use the Analysis tab to analyze conversations with AI:
   - Select an exported conversation file
   - Ask questions about the conversation
   - Get AI-generated insights and summaries

## Getting Discord Token and Channel IDs

For instructions on how to obtain your Discord Token and Channel IDs, please refer to the [DiscordChatExporter documentation](https://github.com/Tyrrrz/DiscordChatExporter/blob/master/.docs/Token-and-IDs.md).

## Privacy and Security

Your Discord Token and Gemini API key are stored locally in a `.env` file. Be careful not to share this file or expose these credentials.

## Credits

- [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter) by Tyrrrz
- Google Gemini API (using gemini-2.0-flash model) for conversation analysis
- Streamlit for the user interface

## License

This project is licensed under the MIT License - see the LICENSE file for details.