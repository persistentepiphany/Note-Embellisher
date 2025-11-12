"""
Firebase Initialization Module
Safe to commit - no sensitive data, uses environment variables
"""
import firebase_admin
from firebase_admin import credentials
import os
import json

def initialize_firebase():
    """Initialize Firebase - called explicitly to avoid blocking app startup"""
    try:
        # Skip if already initialized
        if len(firebase_admin._apps) > 0:
            print("✅ Firebase already initialized")
            return True
            
        # Try to load from environment variable first (for deployment)
        firebase_creds = os.environ.get("FIREBASE_CREDENTIALS")
        if firebase_creds:
            print("✅ Loading Firebase credentials from environment variable")
            cred_dict = json.loads(firebase_creds)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized from environment variable")
            return True
        # Fall back to local file (for development)
        elif os.path.exists("firebaseadminsdk.json"):
            print("✅ Loading Firebase credentials from local file")
            cred = credentials.Certificate("firebaseadminsdk.json")
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized from local file")
            return True
        else:
            print("⚠️ No Firebase credentials found - Firebase features will be disabled")
            return False
    except Exception as e:
        print(f"⚠️ Failed to initialize Firebase: {e}")
        return False

# Don't initialize on import - let the app decide when to initialize
print("📦 firebase_init module loaded (call initialize_firebase() to start)")
