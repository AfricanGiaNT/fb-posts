# AI Facebook Content Generator

Transform your Markdown project documentation into engaging Facebook posts using AI, delivered through a Telegram bot interface.

## 🎯 Overview

This system helps you convert technical documentation about your automation projects into story-driven, engaging Facebook posts. It uses OpenAI's GPT-4o to analyze your markdown content and generate posts using 5 different brand tone styles.

## 🚀 Features

- **Telegram Bot Interface**: Simple, interactive workflow via Telegram
- **5 Brand Tone Styles**: Consistent voice across all posts
- **AI-Powered Generation**: Uses GPT-4o for high-quality content
- **Interactive Review**: Approve, regenerate, or change tone
- **Airtable Integration**: Track and manage all generated content
- **Markdown Support**: Works with any `.md` file format

## 🎙️ Brand Tone Styles

1. **🧩 Behind-the-Build** - "Built this with Cursor AI..."
2. **💡 What Broke** - "I broke something I built. And I loved it."
3. **🚀 Finished & Proud** - "Just shipped this automation..."
4. **🎯 Problem → Solution → Result** - Clear pain point resolution
5. **📓 Mini Lesson** - Philosophical automation insights

## 📋 Quick Setup

### 1. Install Dependencies

```bash
# Clone or download the project
git clone <your-repo-url>
cd fb-posts

# Run setup script
python setup.py
```

### 2. Configure Environment Variables

Edit the `.env` file with your API keys:

```env
# Telegram Bot Token (get from @BotFather)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Airtable Configuration
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_airtable_base_id
AIRTABLE_TABLE_NAME=Content Tracker
```

### 3. Set Up Airtable

Create a new base with a table named "Content Tracker" and these fields:

| Field Name | Field Type | Options |
|------------|------------|---------|
| Post Title | Single line text | |
| Generated Draft | Long text | |
| Tone Used | Single select | Behind-the-Build, What Broke, Finished & Proud, Problem → Solution → Result, Mini Lesson |
| Review Status | Single select | To Review, Approved, Needs Editing, Rejected |
| Markdown Source | Long text | |
| AI Notes or Edits | Long text | |
| Tags / Categories | Multiple select | |
| Scheduled Date | Date | |
| Post URL | URL | |

### 4. Run the Bot

```bash
python scripts/telegram_bot.py
```

### 5. Start Using

1. Find your bot on Telegram
2. Send `/start` to initialize
3. Upload a `.md` file
4. Review and approve generated posts
5. Check Airtable for approved content

## 🔧 Commands

- `/start` - Initialize the bot
- `/help` - Show help information
- `/status` - Check system status
- Upload `.md` file - Generate Facebook post

## 📁 Project Structure

```
fb-posts/
├── scripts/
│   ├── telegram_bot.py          # Main bot application
│   ├── config_manager.py        # Configuration handling
│   ├── ai_content_generator.py  # OpenAI integration
│   └── airtable_connector.py    # Airtable integration
├── rules/
│   ├── tone_guidelines.mdc      # Brand tone definitions
│   └── ai_prompt_structure.mdc  # AI prompt templates
├── content/
│   ├── markdown_logs/           # Input markdown files
│   ├── generated_drafts/        # Generated post drafts
│   └── reviewed_drafts/         # Final reviewed posts
├── requirements.txt             # Python dependencies
├── setup.py                     # Setup script
├── instructions.md              # Detailed instructions
└── README.md                    # This file
```

## 🔄 Workflow

1. **Upload**: Send markdown file to Telegram bot
2. **Generate**: AI analyzes content and creates Facebook post
3. **Review**: Interactive approval/rejection via Telegram
4. **Refine**: Regenerate with different tone or approach
5. **Save**: Approved posts saved to Airtable
6. **Publish**: Copy from Airtable to Facebook

## 🛠 Advanced Configuration

### Custom Tone Styles

Edit `rules/tone_guidelines.mdc` to modify or add new tone styles.

### AI Prompt Customization

Modify `rules/ai_prompt_structure.mdc` to change how the AI generates content.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o` |
| `MAX_FILE_SIZE_MB` | Maximum markdown file size | `10` |
| `PROCESSING_TIMEOUT_SECONDS` | AI processing timeout | `60` |
| `DEBUG` | Enable debug logging | `False` |

## 🔍 Troubleshooting

### Common Issues

1. **Bot not responding**: Check `TELEGRAM_BOT_TOKEN` in `.env`
2. **AI generation fails**: Verify `OPENAI_API_KEY` and credits
3. **Airtable errors**: Confirm `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID`
4. **File upload fails**: Ensure file is `.md` and under size limit

### Debug Mode

Enable debug logging by setting `DEBUG=True` in `.env`.

### Connection Testing

Use `/status` command in Telegram to test all connections.

## 📊 Usage Analytics

The system tracks:
- Generated posts by tone style
- Approval/rejection rates
- Processing times
- Popular content tags

View analytics in your Airtable base.

## 🔒 Security

- API keys stored in environment variables
- No sensitive data logged
- File uploads are temporary
- User sessions are memory-based (consider Redis for production)

## 🚀 Deployment

### Local Development
```bash
python scripts/telegram_bot.py
```

### Production Deployment
- Use process manager (PM2, systemd)
- Set up proper logging
- Configure Redis for session storage
- Set up monitoring and alerts

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 💡 Tips for Best Results

1. **Write clear markdown**: Include project context, problems solved, and results
2. **Use descriptive titles**: Help the AI understand the content better
3. **Include technical details**: Mention tools, languages, and specific features
4. **Add outcomes**: Quantify results where possible (time saved, problems solved)
5. **Review and edit**: Always review generated content before publishing

## 🤝 Support

- Check `instructions.md` for detailed setup guide
- Use `/help` command in Telegram for quick reference
- Review logs for technical issues
- Test connections with `/status` command

---

**Ready to transform your project documentation into engaging Facebook posts? Start by running `python setup.py`!** 🚀 