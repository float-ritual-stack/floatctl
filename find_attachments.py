#!/usr/bin/env python3
"""Find conversations with attachments in the test data."""

import json
from pathlib import Path

# Search for conversations with attachments
json_file = Path("/Users/evan/projects/float-workspace/operations/float-dropzone/wk 30/downloads/data-2025-08-04-17-33-14-batch-0000/conversations.json")

with open(json_file) as f:
    conversations = json.load(f)

found = False
for conv in conversations:
    conv_has_attachments = False
    for msg in conv.get('chat_messages', []):
        attachments = msg.get('attachments', [])
        if attachments:
            if not conv_has_attachments:
                print(f"\nConversation: {conv['name']}")
                print(f"UUID: {conv['uuid']}")
                conv_has_attachments = True
            
            print(f"\n  Message sender: {msg.get('sender')}")
            for att in attachments:
                print(f"    - {att.get('file_name')} ({att.get('file_size')} bytes, {att.get('file_type')})")
                if 'extracted_content' in att:
                    content_preview = att['extracted_content'][:100] + "..." if len(att['extracted_content']) > 100 else att['extracted_content']
                    print(f"      Content: {content_preview}")
            found = True
            
            # Create a sample test file with this structure
            if not found:
                sample = {
                    "uuid": conv['uuid'],
                    "name": conv['name'],
                    "created_at": conv['created_at'],
                    "updated_at": conv['updated_at'],
                    "chat_messages": [msg]
                }
                with open("test_conversation_with_attachment.json", "w") as out:
                    json.dump([sample], out, indent=2)
                print("\nCreated test_conversation_with_attachment.json")
                break
    
    if found:
        break

if not found:
    print("No conversations with attachments found in this file.")