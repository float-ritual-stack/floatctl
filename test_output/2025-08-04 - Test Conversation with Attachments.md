---
conversation_title: "Test Conversation with Attachments"
conversation_id: test-attachments-123
conversation_src: https://claude.ai/chat/test-attachments-123
conversation_created: 2025-08-04T10:00:00Z
conversation_updated: 2025-08-04T11:00:00Z
conversation_dates:
  - 2025-08-04
markers:
  - type: "start_time"
    content: "2025-08-04T10:00:00Z"
    lines: [6]
attachments:
  - filename: "pasted.txt"
    size: 120
    type: "text/plain"
    message_index: 0
    inline: true
  - filename: "report.pdf"
    size: 24184
    type: "application/pdf"
    message_index: 2
    inline: false
    saved_to: "2025-08-04 - Test Conversation with Attachments.attachments/report.pdf"
  - filename: "data.csv"
    size: 2048
    type: "text/csv"
    message_index: 2
    inline: true
total_lines: 39
thinking_blocks_count: 0
attachments_count: 3
---

# Test Conversation with Attachments

## Conversation

### 👤 Human
- start_time:: 2025-08-04T10:00:00Z

Here's a small code snippet:

```pasted.txt
def hello_world():
    print('Hello, World!')

hello_world()
```

---

### 🤖 Assistant

That's a simple Python function that prints 'Hello, World!'.

---

### 👤 Human

And here's a larger document:

{Attachment: report.pdf → 24184 bytes}

```data.csv
Date,Sales,Revenue
2024-01-01,100,5000
2024-01-02,120,6000
2024-01-03,95,4750
```

---
