from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify Firebase ID token and return user info
    """
    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(credentials.credentials)
        user_id = decoded_token['uid']
        user_email = decoded_token.get('email', '')
        
        logger.info(f"Authenticated user: {user_id} ({user_email})")
        
        return {
            'uid': user_id,
            'email': user_email,
            'token': decoded_token
        }
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )

class CurrentUser:
    """
    Dependency class to get current authenticated user
    """
    def __init__(self, user_data: dict = Depends(get_current_user)):
        self.uid = user_data['uid']
        self.email = user_data['email']
        self.token = user_data['token']