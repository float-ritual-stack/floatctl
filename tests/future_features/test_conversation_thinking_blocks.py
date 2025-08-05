"""Tests for thinking block extraction in conversations plugin."""

import json
from pathlib import Path
import pytest

from floatctl.plugins.conversations import ConversationsPlugin


@pytest.fixture
def conversations_plugin():
    """Create a ConversationsPlugin instance."""
    return ConversationsPlugin()


@pytest.fixture
def sample_conversation_with_thinking():
    """Create a sample conversation with thinking blocks."""
    return {
        "uuid": "test-123",
        "name": "Test Conversation",
        "created_at": "2025-08-02T03:00:00Z",
        "updated_at": "2025-08-02T04:00:00Z",
        "chat_messages": [
            {
                "sender": "human",
                "content": [
                    {
                        "type": "text",
                        "text": "What is 2 + 2?",
                        "start_timestamp": "2025-08-02T03:00:00Z"
                    }
                ]
            },
            {
                "sender": "assistant",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "This is a simple arithmetic question.\nI need to add 2 + 2.\nThe answer is 4.",
                        "start_timestamp": "2025-08-02T03:01:00Z",
                        "stop_timestamp": "2025-08-02T03:01:02Z",
                        "summaries": [
                            {"summary": "Analyzing arithmetic problem"}
                        ],
                        "cut_off": False
                    },
                    {
                        "type": "text",
                        "text": "2 + 2 = 4"
                    }
                ]
            },
            {
                "sender": "human",
                "content": [
                    {
                        "type": "text",
                        "text": "Can you use a tool?"
                    }
                ]
            },
            {
                "sender": "assistant",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "The user wants me to use a tool.\nI should demonstrate tool usage.",
                        "start_timestamp": "2025-08-02T03:02:00Z",
                        "stop_timestamp": "2025-08-02T03:02:01Z",
                        "summaries": [],
                        "cut_off": False
                    },
                    {
                        "type": "text",
                        "text": "I'll use a tool for you."
                    },
                    {
                        "type": "tool_use",
                        "id": "tool_123",
                        "name": "calculator",
                        "input": {"expression": "2 + 2"}
                    }
                ]
            }
        ]
    }


def test_extract_thinking_blocks(conversations_plugin, sample_conversation_with_thinking):
    """Test that thinking blocks are properly extracted."""
    # Create markdown content
    markdown = conversations_plugin._format_conversation_markdown(
        sample_conversation_with_thinking, 
        None,
        None
    )
    
    # Extract patterns
    patterns = conversations_plugin._extract_patterns(
        markdown,
        sample_conversation_with_thinking
    )
    
    # Check thinking blocks were extracted
    assert len(patterns['thinking_blocks']) == 2
    
    # Check first thinking block
    first_block = patterns['thinking_blocks'][0]
    assert first_block['id'] == 'thinking_1'
    assert first_block['sender'] == 'assistant'
    assert 'simple arithmetic question' in first_block['content']
    assert 'The answer is 4' in first_block['content']
    
    # Check second thinking block
    second_block = patterns['thinking_blocks'][1]
    assert second_block['id'] == 'thinking_2'
    assert second_block['sender'] == 'assistant'
    assert 'user wants me to use a tool' in second_block['content']


def test_thinking_blocks_in_yaml_frontmatter(conversations_plugin, sample_conversation_with_thinking):
    """Test that thinking blocks appear in YAML frontmatter."""
    # Create markdown content
    markdown = conversations_plugin._format_conversation_markdown(
        sample_conversation_with_thinking,
        None
    )
    
    # Check YAML frontmatter contains thinking blocks
    assert 'thinking_blocks:' in markdown
    assert 'thinking_blocks_count: 2' in markdown
    assert 'thinking_1' in markdown
    assert 'thinking_2' in markdown


def test_thinking_blocks_preserved_in_content(conversations_plugin, sample_conversation_with_thinking):
    """Test that thinking blocks are preserved in conversation content."""
    # Create markdown content
    markdown = conversations_plugin._format_conversation_markdown(
        sample_conversation_with_thinking,
        None
    )
    
    # Check that thinking blocks appear in the conversation body
    assert '<thinking>' in markdown
    assert '</thinking>' in markdown
    assert 'This is a simple arithmetic question' in markdown
    assert 'The user wants me to use a tool' in markdown


def test_empty_thinking_blocks(conversations_plugin):
    """Test handling of conversations without thinking blocks."""
    conversation = {
        "uuid": "test-no-thinking",
        "name": "No Thinking Blocks",
        "created_at": "2025-08-02T03:00:00Z",
        "updated_at": "2025-08-02T04:00:00Z",
        "chat_messages": [
            {
                "sender": "human",
                "content": [{"type": "text", "text": "Hello"}]
            },
            {
                "sender": "assistant",
                "content": [{"type": "text", "text": "Hi there!"}]
            }
        ]
    }
    
    markdown = conversations_plugin._format_conversation_markdown(conversation, None, None)
    patterns = conversations_plugin._extract_patterns(markdown, conversation)
    
    assert patterns['thinking_blocks'] == []
    assert 'thinking_blocks_count: 0' in markdown


def test_nested_thinking_blocks(conversations_plugin):
    """Test extraction of complex nested thinking content."""
    conversation = {
        "uuid": "test-nested",
        "name": "Nested Thinking",
        "created_at": "2025-08-02T03:00:00Z",
        "updated_at": "2025-08-02T04:00:00Z",
        "chat_messages": [
            {
                "sender": "assistant",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "Main thought:\n- Sub-thought 1\n- Sub-thought 2\n  - Nested thought\n\nConclusion: This is complex.",
                        "summaries": [],
                        "cut_off": False
                    },
                    {
                        "type": "text",
                        "text": "Here's my response."
                    }
                ]
            }
        ]
    }
    
    markdown = conversations_plugin._format_conversation_markdown(conversation, None, None)
    patterns = conversations_plugin._extract_patterns(markdown, conversation)
    
    assert len(patterns['thinking_blocks']) == 1
    block = patterns['thinking_blocks'][0]
    assert 'Main thought:' in block['content']
    assert 'Sub-thought 1' in block['content']
    assert 'Nested thought' in block['content']
    assert 'Conclusion: This is complex.' in block['content']