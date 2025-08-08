"""Tests for attachment handling in conversations plugin."""

import json
from pathlib import Path
import pytest
import tempfile

from floatctl.plugins.conversations import ConversationsPlugin


@pytest.fixture
def conversations_plugin():
    """Create a ConversationsPlugin instance."""
    return ConversationsPlugin()


@pytest.fixture
def conversation_with_attachments():
    """Create a sample conversation with attachments."""
    return {
        "uuid": "test-attachments-123",
        "name": "Test Conversation with Attachments",
        "created_at": "2025-08-04T10:00:00Z",
        "updated_at": "2025-08-04T11:00:00Z",
        "chat_messages": [
            {
                "sender": "human",
                "content": [
                    {
                        "type": "text",
                        "text": "Here's a small code snippet:",
                        "start_timestamp": "2025-08-04T10:00:00Z"
                    }
                ],
                "attachments": [
                    {
                        "file_name": "pasted.txt",
                        "file_size": 120,
                        "file_type": "text/plain",
                        "extracted_content": "def hello_world():\n    print('Hello, World!')\n\nhello_world()"
                    }
                ],
                "created_at": "2025-08-04T10:00:00Z",
                "updated_at": "2025-08-04T10:00:00Z"
            },
            {
                "sender": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "That's a simple Python function that prints 'Hello, World!'."
                    }
                ],
                "attachments": [],
                "created_at": "2025-08-04T10:01:00Z",
                "updated_at": "2025-08-04T10:01:00Z"
            },
            {
                "sender": "human",
                "content": [
                    {
                        "type": "text",
                        "text": "And here's a larger document:"
                    }
                ],
                "attachments": [
                    {
                        "file_name": "report.pdf",
                        "file_size": 24184,
                        "file_type": "application/pdf",
                        "extracted_content": "Annual Report 2024\n\nExecutive Summary\nThis report covers the key achievements and challenges faced during the fiscal year 2024...\n\n[Content continues for many pages...]"
                    },
                    {
                        "file_name": "data.csv",
                        "file_size": 2048,
                        "file_type": "text/csv",
                        "extracted_content": "Date,Sales,Revenue\n2024-01-01,100,5000\n2024-01-02,120,6000\n2024-01-03,95,4750"
                    }
                ],
                "created_at": "2025-08-04T10:02:00Z",
                "updated_at": "2025-08-04T10:02:00Z"
            }
        ]
    }


def test_extract_attachments(conversations_plugin, conversation_with_attachments):
    """Test that attachments are properly extracted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "test_conversation"
        
        # Extract attachments
        attachment_info = conversations_plugin._extract_and_save_attachments(
            conversation_with_attachments, 
            base_path
        )
        
        # Check attachment metadata
        assert len(attachment_info['attachments']) == 3
        
        # Check small text file is marked for inline
        pasted = next(att for att in attachment_info['attachments'] if att['filename'] == 'pasted.txt')
        assert pasted['inline'] is True
        assert pasted['size'] == 120
        assert 'content' in pasted
        assert 'def hello_world()' in pasted['content']
        
        # Check large files are saved to disk
        report = next(att for att in attachment_info['attachments'] if att['filename'] == 'report.pdf')
        assert report['inline'] is False
        assert report['saved_to'] is not None
        assert 'test_conversation.attachments/report.pdf' in report['saved_to']
        
        # Verify attachment directory was created
        assert attachment_info['attachments_dir'] is not None
        assert attachment_info['attachments_dir'].exists()
        
        # Verify files were saved
        report_path = attachment_info['attachments_dir'] / 'report.pdf'
        assert report_path.exists()
        assert 'Annual Report 2024' in report_path.read_text()


def test_inline_attachment_in_markdown(conversations_plugin, conversation_with_attachments):
    """Test that inline attachments appear in markdown output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "test_conversation"
        
        # Extract attachments
        attachment_info = conversations_plugin._extract_and_save_attachments(
            conversation_with_attachments, 
            base_path
        )
        
        # Create markdown
        markdown = conversations_plugin._format_conversation_markdown(
            conversation_with_attachments,
            None,
            attachment_info
        )
        
        # Check inline attachment appears as code block
        assert '```pasted.txt' in markdown
        assert "def hello_world():" in markdown
        assert "print('Hello, World!')" in markdown
        assert '```' in markdown
        
        # Check large attachment references
        assert '{Attachment: report.pdf → 24184 bytes}' in markdown
        # data.csv is small enough to be inlined
        assert '```data.csv' in markdown


def test_attachment_yaml_frontmatter(conversations_plugin, conversation_with_attachments):
    """Test that attachments appear in YAML frontmatter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "test_conversation"
        
        # Extract attachments
        attachment_info = conversations_plugin._extract_and_save_attachments(
            conversation_with_attachments, 
            base_path
        )
        
        # Create markdown
        markdown = conversations_plugin._format_conversation_markdown(
            conversation_with_attachments,
            None,
            attachment_info
        )
        
        # Check YAML frontmatter contains attachment info
        assert 'attachments:' in markdown
        assert 'attachments_count: 3' in markdown
        assert '- filename: "pasted.txt"' in markdown
        assert '  size: 120' in markdown
        assert '  type: "text/plain"' in markdown
        assert '  inline: true' in markdown
        assert '- filename: "report.pdf"' in markdown
        assert '  inline: false' in markdown
        assert '  saved_to: "test_conversation.attachments/report.pdf"' in markdown


def test_conversation_without_attachments(conversations_plugin):
    """Test handling of conversations without attachments."""
    conversation = {
        "uuid": "test-no-attachments",
        "name": "No Attachments",
        "created_at": "2025-08-04T10:00:00Z",
        "updated_at": "2025-08-04T10:00:00Z",
        "chat_messages": [
            {
                "sender": "human",
                "content": [{"type": "text", "text": "Hello"}],
                "attachments": []
            },
            {
                "sender": "assistant",
                "content": [{"type": "text", "text": "Hi there!"}],
                "attachments": []
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "test_conversation"
        
        # Extract attachments
        attachment_info = conversations_plugin._extract_and_save_attachments(
            conversation, 
            base_path
        )
        
        # Check no attachments found
        assert len(attachment_info['attachments']) == 0
        assert attachment_info['attachments_dir'] is None
        
        # Create markdown
        markdown = conversations_plugin._format_conversation_markdown(
            conversation,
            None,
            attachment_info
        )
        
        # Check no attachment references in output
        assert 'attachments:' not in markdown
        assert 'attachments_count: 0' in markdown
        assert '{Attachment:' not in markdown


def test_text_file_types_inline(conversations_plugin):
    """Test that various text file types are inlined when small."""
    conversation = {
        "uuid": "test-text-types",
        "name": "Text File Types",
        "created_at": "2025-08-04T10:00:00Z",
        "updated_at": "2025-08-04T10:00:00Z",
        "chat_messages": [
            {
                "sender": "human",
                "content": [{"type": "text", "text": "Various files"}],
                "attachments": [
                    {
                        "file_name": "script.js",
                        "file_size": 100,
                        "file_type": "application/javascript",
                        "extracted_content": "console.log('test');"
                    },
                    {
                        "file_name": "data.json",
                        "file_size": 50,
                        "file_type": "application/json",
                        "extracted_content": '{"key": "value"}'
                    },
                    {
                        "file_name": "style.css",
                        "file_size": 80,
                        "file_type": "text/css",
                        "extracted_content": "body { margin: 0; }"
                    }
                ]
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "test_conversation"
        
        # Extract attachments
        attachment_info = conversations_plugin._extract_and_save_attachments(
            conversation, 
            base_path
        )
        
        # All small text files should be inline
        assert all(att['inline'] for att in attachment_info['attachments'])
        assert attachment_info['attachments_dir'] is None  # No files saved to disk