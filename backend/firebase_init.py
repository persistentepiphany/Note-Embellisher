"""
Firebase Initialization Module
Safe to commit - no sensitive data, uses environment variables
"""
import firebase_admin
from firebase_admin import credentials
import os
import json

def initialize_firebase():
    """Initialize Firebase Admin SDK - supports multiple credential methods"""
    
    # Skip if already initialized
    if firebase_admin._apps:
        print("✅ Firebase already initialized")
        return True
    
    try:
        # Method 1: Try individual environment variables (Railway/Render approach)
        firebase_type = os.environ.get("type")
        project_id = os.environ.get("project_id")
        private_key_id = os.environ.get("private_key_id")
        private_key = os.environ.get("private_key")
        client_email = os.environ.get("client_email")
        client_id = os.environ.get("client_id")
        auth_uri = os.environ.get("auth_uri")
        token_uri = os.environ.get("token_uri")
        auth_provider_cert = os.environ.get("auth_provider_x509_cert_url")
        client_cert = os.environ.get("client_x509_cert_url")
        universe_domain = os.environ.get("universe_domain")
        
        if all([firebase_type, project_id, private_key, client_email]):
            print("✅ Using individual Firebase environment variables from Railway")
            cred_dict = {
                "type": firebase_type,
                "project_id": project_id,
                "private_key_id": private_key_id,
                "private_key": private_key.replace('\\n', '\n'),  # Fix escaped newlines
                "client_email": client_email,
                "client_id": client_id,
                "auth_uri": auth_uri,
                "token_uri": token_uri,
                "auth_provider_x509_cert_url": auth_provider_cert,
                "client_x509_cert_url": client_cert,
            }
            if universe_domain:
                cred_dict["universe_domain"] = universe_domain
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized successfully from individual env vars")
            return True
        
        # Method 2: Try JSON string in FIREBASE_CREDENTIALS
        firebase_creds = os.environ.get("FIREBASE_CREDENTIALS")
        if firebase_creds:
            print("✅ Using FIREBASE_CREDENTIALS JSON string")
            cred_dict = json.loads(firebase_creds)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized from FIREBASE_CREDENTIALS")
            return True
        
        # Method 3: Try local file (development only)
        if os.path.exists("firebaseadminsdk.json"):
            print("✅ Using local firebaseadminsdk.json file")
            cred = credentials.Certificate("firebaseadminsdk.json")
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized from local file")
            return True
        
        print("⚠️ No Firebase credentials found - Firebase features will be disabled")
        return False
        
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# Don't initialize on import - let the app decide when to initialize
print("📦 firebase_init module loaded (call initialize_firebase() to start)")
