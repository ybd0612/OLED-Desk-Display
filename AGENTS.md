# AGENTS.md - OLED Screen Hook Configuration

## Auto-push Summary to OLED Screen

At the end of every conversation in this project, before yielding to the user:

1. Generate a title (max 10 Chinese chars / 20 English chars) — summarize what was accomplished, NOT the project/file name, no punctuation
2. Generate a summary (max 3 lines, each max 10 Chinese chars / 20 English chars) — complete thoughts, no truncation
3. Run this command to push to screen:

```bash
python python/conversation_hook.py "标题" "第一行" "第二行" "第三行"
```

Rules:
- Skip if the conversation was casual greetings or quick Q&A with no substantial work
- If conversation was simple, use fewer lines (1-2 is fine)
- Title captures the topic of what was done, each body line is a key result
- All text must fit within the screen limits — no "..." truncation
- conversation_hook.py sends with FLASH prefix, so the screen will flash 3 times before showing