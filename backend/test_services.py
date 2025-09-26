"""
Simple test script to verify API functionality
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from firestore_service import firestore_service
from chatgpt_service import chatgpt_service, ProcessingSettings

async def test_firestore_connection():
    """Test Firestore connection"""
    try:
        print("Testing Firestore connection...")
        
        # Try to get notes for a test user
        notes = await firestore_service.get_user_notes("test_user_123", limit=1)
        print(f"✓ Firestore connection successful. Found {len(notes)} notes for test user.")
        return True
    except Exception as e:
        print(f"✗ Firestore connection failed: {str(e)}")
        return False

async def test_chatgpt_service():
    """Test ChatGPT service"""
    try:
        print("Testing ChatGPT service...")
        
        settings = ProcessingSettings(add_bullet_points=True)
        result = await chatgpt_service.process_text_with_chatgpt("Test text", settings)
        print(f"✓ ChatGPT service working. Result length: {len(result)} chars")
        return True
    except Exception as e:
        print(f"✗ ChatGPT service failed: {str(e)}")
        return False

async def main():
    print("=== API Service Test ===")
    
    firestore_ok = await test_firestore_connection()
    chatgpt_ok = await test_chatgpt_service()
    
    if firestore_ok and chatgpt_ok:
        print("\n✓ All services are working correctly!")
    else:
        print("\n✗ Some services have issues.")

if __name__ == "__main__":
    asyncio.run(main())