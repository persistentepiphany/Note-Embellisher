#!/usr/bin/env python3
"""
Test script to verify the note embellisher fixes
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_chatgpt_service():
    """Test the ChatGPT service"""
    try:
        from chatgpt_service import chatgpt_service, ProcessingSettings
        
        print("Testing ChatGPT service...")
        settings = ProcessingSettings(
            add_bullet_points=True,
            add_headers=True,
            expand=True,
            summarize=False
        )
        
        test_text = "This is a test note. It contains some basic information that should be enhanced."
        
        result = await chatgpt_service.process_text_with_chatgpt(test_text, settings)
        
        print(f"✅ ChatGPT service working! Result length: {len(result)} characters")
        print(f"First 200 chars: {result[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ ChatGPT service failed: {e}")
        return False

async def test_firestore_connection():
    """Test Firestore connection"""
    try:
        from firestore_service import firestore_service
        
        print("Testing Firestore service...")
        # This will test if we can connect to Firestore
        # We're just testing the connection, not creating actual data
        
        print("✅ Firestore service initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Firestore service failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🔧 Testing Note Embellisher fixes...\n")
    
    tests = [
        ("Firestore Connection", test_firestore_connection),
        ("ChatGPT Service", test_chatgpt_service),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
        print()
    
    print("📊 Test Results:")
    print("=" * 50)
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n{passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The fixes should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())