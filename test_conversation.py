#!/usr/bin/env python3
"""Test script to simulate conversation with agent."""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

import httpx


# Use production server
API_BASE_URL = "http://doctor-agent-alb-1328234230.me-central-1.elb.amazonaws.com"
AGENT_ID = "elemental_egor_adamovich_2"  # Using existing agent from production


async def test_conversation():
    """Test conversation flow."""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        print("=" * 60)
        print("Testing Agent Conversation")
        print("=" * 60)
        print(f"Agent ID: {AGENT_ID}")
        print(f"API URL: {API_BASE_URL}")
        print()

        # Step 1: Create conversation
        print("Step 1: Creating conversation...")
        try:
            response = await client.post(
                "/api/v1/chat/conversations",
                json={"agent_id": AGENT_ID},
            )
            response.raise_for_status()
            conv_data = response.json()
            conversation_id = conv_data["conversation_id"]
            print(f"✓ Conversation created: {conversation_id}")
            print()
        except httpx.HTTPStatusError as e:
            print(f"✗ Failed to create conversation: {e}")
            print(f"Response: {e.response.text}")
            print("\n⚠️  Backend might not be running or not configured correctly.")
            print("Please start the backend with:")
            print("  cd backend")
            print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
            return
        except httpx.ConnectError:
            print("✗ Cannot connect to backend")
            print("\n⚠️  Backend is not running on http://localhost:8000")
            print("Please start the backend with:")
            print("  cd backend")
            print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
            return
        except Exception as e:
            print(f"✗ Error: {e}")
            print("\n⚠️  Make sure backend is running on http://localhost:8000")
            print("Start it with:")
            print("  cd backend")
            print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
            return

        # Messages to send (exact sequence from user's example)
        messages = [
            "Привет - хочу сделать инъекцию в губы, это вы делаете?",
            "Но я пока не хочу записываться - я хочу понять сколько по времени длится процедура и это больно или нет?",
            "ну про инъекцию в губы",
            "Мой номер телефона: +971501234567",
        ]

        # Step 2: Send messages sequentially
        for i, message in enumerate(messages, 1):
            print(f"{'=' * 60}")
            print(f"Message {i}/{len(messages)}")
            print(f"{'=' * 60}")
            print(f"User: {message}")
            print()

            try:
                response = await client.post(
                    f"/api/v1/chat/conversations/{conversation_id}/messages",
                    json={"content": message},
                )
                response.raise_for_status()
                result = response.json()

                # Check if escalation happened
                if result.get("role") == "user" and i < len(messages):
                    # This might indicate escalation or error
                    print(f"⚠ Response role is 'user' - might indicate escalation")
                    print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
                else:
                    agent_response = result.get("content", "")
                    role = result.get("role", "")
                    print(f"Agent ({role}): {agent_response}")
                    print()

                # Check conversation status after phone number
                if i == len(messages) and "телефона" in message.lower() or "+" in message:
                    print("Checking conversation status after phone number...")
                    conv_response = await client.get(
                        f"/api/v1/chat/conversations/{conversation_id}",
                    )
                    conv_response.raise_for_status()
                    conv_status = conv_response.json()
                    status = conv_status.get("status", "")
                    handoff_reason = conv_status.get("handoff_reason", "")
                    print(f"Conversation status: {status}")
                    if handoff_reason:
                        print(f"Handoff reason: {handoff_reason}")
                    print()

            except httpx.HTTPStatusError as e:
                print(f"✗ Failed to send message: {e}")
                print(f"Response: {e.response.text}")
                break
            except Exception as e:
                print(f"✗ Error: {e}")
                break

            # Small delay between messages
            await asyncio.sleep(1)

        # Step 3: Get full conversation history
        print("=" * 60)
        print("Final conversation history:")
        print("=" * 60)
        try:
            response = await client.get(
                f"/api/v1/chat/conversations/{conversation_id}/messages",
                params={"limit": 100},
            )
            response.raise_for_status()
            messages_history = response.json()

            # Sort by timestamp (oldest first) for better readability
            sorted_messages = sorted(messages_history, key=lambda x: x.get("timestamp", ""))

            print(f"Total messages: {len(sorted_messages)}")
            print()
            for i, msg in enumerate(sorted_messages, 1):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                # Truncate long messages for readability
                content_preview = content[:200] + "..." if len(content) > 200 else content
                print(f"{i}. [{role.upper()}] {content_preview}")
                print(f"   Time: {timestamp}")
                print()

        except Exception as e:
            print(f"✗ Failed to get history: {e}")

        print("=" * 60)
        print("Test completed!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_conversation())

