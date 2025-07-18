# Guidelines for Creating High-Quality Markdown Content (.mdc)

This document outlines the best practices for creating markdown content to ensure the AI Content Generator produces the highest quality, most engaging, and contextually relevant Facebook posts.

**Core Principle:** The AI is trained to think in terms of **Problem → Solution → Result**. Your markdown file should be a detailed "developer's journal" entry that tells a clear story about a specific piece of work. The more structured and explicit you are, the better the AI can translate your technical achievements into compelling content for different audiences.

**CRITICAL PERSONAL PROJECT PERSPECTIVE:**
These are PERSONAL projects that you built to solve YOUR OWN problems. You are sharing your journey of building tools for yourself, not creating services for others.

✅ CORRECT PERSPECTIVE:
- "I built this tool to solve my own problem with..."
- "I needed a way to handle my own..."
- "This helps me manage my own..."
- "I created this for my own use because..."

❌ INCORRECT PERSPECTIVE:
- "I built this for farmers to..."
- "This helps farmers with..."
- "Farmers can now..."
- "This system serves farmers by..."

---

## 1. Content Structure: Use Clear Headings

Structure your markdown file with the following headings. Not all are required for every post, but providing them helps the AI understand the narrative.

### Required Headings

-   `## What I Built`
    -   **Purpose:** A clear, concise summary of the feature or fix.
    -   **Example:** "I built a Telegram bot that automatically logs daily income and expenses from simple text commands."

-   `## The Problem`
    -   **Purpose:** Describe the pain point, challenge, or need this work addresses. Be specific.
    -   **Example:** "Small business owners struggle with tracking finances. They either use complex apps or forget to update spreadsheets. They need something as easy as sending a WhatsApp message."

-   `## My Solution`
    -   **Purpose:** Explain how you solved the problem. Detail the key features and how they work from a user's perspective.
    -   **Example:** "I created a bot that understands commands like `/log income 5000 rent`. It saves the entry to a Google Sheet automatically. Users get a confirmation message right in Telegram."

### Recommended Headings

-   `## How It Works: The Technical Details`
    -   **Purpose:** Provide the technical specifics. This is crucial for generating "Technical" audience posts.
    -   **Content:** Mention architecture, key libraries, APIs, database schema, or code snippets.
    -   **Example:** "The bot is a Python script hosted on a Raspberry Pi. It uses the `python-telegram-bot` library to handle messages and `gspread` to connect to the Google Sheets API. A simple regex `(/log (income|expense) (\d+) (.+))` parses the command."

-   `## The Impact / Result`
    -   **Purpose:** Quantify the outcome. How did this help?
    -   **Example:** "The bot saves at least 10 minutes per day. It has eliminated manual data entry errors and provides a real-time view of cash flow. Beta testers have reported feeling more in control of their finances."

-   `## Key Lessons Learned`
    -   **Purpose:** Share insights, "aha" moments, or things you'd do differently. This is great for "Mini Lesson" or "What Broke" posts.
    -   **Example:** "Lesson 1: Keep it simple. My first version had too many commands. Lesson 2: Error handling is critical. The bot needs to guide the user when they make a mistake."

---

## 2. Formatting and Style

-   **Use Markdown:** Use `#`, `##`, `###` for headings, `*` or `-` for lists, and `**bold**` for emphasis.
-   **Keep Paragraphs Short:** Write in short, scannable paragraphs (1-3 sentences).
-   **Be Specific:** Instead of "made it faster," say "reduced page load time by 50%."
-   **Use Active Voice:** "I built..." is better than "It was built..."
-   **Include Code Snippets:** Use markdown code blocks (```) for short, illustrative code examples.

---

## 3. What to Avoid

-   **Vagueness:** Avoid generic statements like "improved the system."
-   **Jargon without Explanation:** If you use a technical term, briefly explain it if it's central to the story.
-   **One Giant Block of Text:** Structure is key. Use headings and lists to break up content.

---

## 4. Example `.mdc` File

Here is a template demonstrating these guidelines in action.

```markdown
# Telegram Bot for Financial Logging

## What I Built
A simple Telegram bot that allows users to log their daily income and expenses directly from chat using simple commands.

## The Problem
Many small business owners in my community find bookkeeping apps too complicated and time-consuming. They often forget to log transactions, leading to inaccurate financial records. They needed a tool that was as fast and easy as sending a message to a friend.

## My Solution
I developed a Telegram bot that acts as a personal bookkeeper. A user can send a message like `/log income 5000 Shop 1 sales` or `/log expense 1500 transport`, and the bot instantly records the transaction in a private Google Sheet.

**Key Features:**
-   **Simple Commands:** No complex interface, just two main commands.
-   **Instant Confirmation:** The bot replies immediately to confirm the entry.
-   **Google Sheets Integration:** All data is stored in a familiar, accessible format.

## How It Works: The Technical Details
The bot is built with Python and hosted on a small server.
-   **Core Library:** `python-telegram-bot` for interacting with the Telegram API.
-   **Data Storage:** `gspread` library to authenticate and write to a specific Google Sheet.
-   **Command Parsing:** A regular expression (`/log (income|expense) (\d+) (.+)`) is used to parse the user's message into structured data (type, amount, description).
-   **Error Handling:** If a command is malformed, the bot sends back a helpful message with the correct format.

## The Impact / Result
-   **Time Saved:** Users report saving 5-10 minutes daily compared to manual spreadsheet entry.
-   **Improved Accuracy:** Real-time logging has reduced forgotten entries by over 90% in beta testing.
-   **Peace of Mind:** Business owners feel more confident and in control of their finances.

## Key Lessons Learned
The biggest lesson was the importance of the user experience. The first version required multiple steps, but simplifying it to a single command made all the difference in adoption. Securely managing API keys using environment variables was also a critical security measure.
``` 