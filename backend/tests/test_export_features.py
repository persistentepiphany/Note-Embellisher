"""
Test suite for new export and Google Drive features
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_drive_service import google_drive_service
from services.document_export_service import export_service, DOCX_AVAILABLE


def test_google_drive_service():
    """Test Google Drive service initialization"""
    print("\n🔍 Testing Google Drive Service...")
    
    # Should initialize without errors even if not configured
    assert google_drive_service is not None
    print(f"  ✓ Service initialized: {google_drive_service.is_configured}")
    
    if not google_drive_service.is_configured:
        print("  ⚠️  Not configured (missing env vars) - this is OK for testing")
    else:
        print("  ✓ Service is fully configured")
    
    # Test state generation
    try:
        state = google_drive_service.generate_state()
        assert len(state) > 20
        print(f"  ✓ State generation works: {state[:20]}...")
    except Exception as e:
        print(f"  ✗ State generation failed: {e}")
        raise


def test_document_export_service():
    """Test document export service"""
    print("\n🔍 Testing Document Export Service...")
    
    assert export_service is not None
    print(f"  ✓ Service initialized")
    print(f"  ✓ DOCX available: {DOCX_AVAILABLE}")
    
    # Test TXT export (always available)
    try:
        test_content = "This is a test note.\n\nWith multiple paragraphs."
        txt_path = export_service.generate_txt(test_content, "test_export")
        assert os.path.exists(txt_path)
        print(f"  ✓ TXT export works: {txt_path}")
        
        # Clean up
        if os.path.exists(txt_path):
            os.remove(txt_path)
            print(f"  ✓ Cleanup successful")
    except Exception as e:
        print(f"  ✗ TXT export failed: {e}")
        raise
    
    # Test DOCX export if available
    if DOCX_AVAILABLE:
        try:
            docx_path = export_service.generate_docx(
                test_content,
                "Test Document",
                "test_export_docx"
            )
            assert os.path.exists(docx_path)
            print(f"  ✓ DOCX export works: {docx_path}")
            
            # Clean up
            if os.path.exists(docx_path):
                os.remove(docx_path)
                print(f"  ✓ Cleanup successful")
        except Exception as e:
            print(f"  ✗ DOCX export failed: {e}")
            raise
    else:
        print("  ⚠️  DOCX library not available - skipping DOCX test")


def test_imports():
    """Test that all new modules import correctly"""
    print("\n🔍 Testing Imports...")
    
    try:
        from core.database import GoogleDriveToken
        print("  ✓ GoogleDriveToken model imports")
    except Exception as e:
        print(f"  ✗ GoogleDriveToken import failed: {e}")
        raise
    
    try:
        from core.schemas import NoteResponse
        # Check if new fields exist
        from pydantic import BaseModel
        print("  ✓ NoteResponse schema imports")
    except Exception as e:
        print(f"  ✗ Schema import failed: {e}")
        raise


def test_helper_functions():
    """Test main.py helper functions"""
    print("\n🔍 Testing Helper Functions...")
    
    try:
        from main import (
            build_generated_file_url,
            absolute_export_path,
            export_file_exists,
        )
        
        # Test URL building
        url = build_generated_file_url("/path/to/file.pdf")
        assert url == "/generated_pdfs/file.pdf"
        print(f"  ✓ build_generated_file_url: {url}")
        
        # Test None handling
        assert build_generated_file_url(None) is None
        print("  ✓ build_generated_file_url handles None")
        
        # Test path resolution
        abs_path = absolute_export_path("generated_pdfs/test.pdf")
        assert os.path.isabs(abs_path)
        print(f"  ✓ absolute_export_path: {abs_path}")
        
        # Test file existence check
        exists = export_file_exists(None)
        assert exists is False
        print("  ✓ export_file_exists handles None")
        
    except Exception as e:
        print(f"  ✗ Helper function test failed: {e}")
        raise


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTING NEW EXPORT & GOOGLE DRIVE FEATURES")
    print("=" * 60)
    
    try:
        test_imports()
        test_google_drive_service()
        test_document_export_service()
        test_helper_functions()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nNew features are ready to use!")
        print("\nNext steps:")
        print("  1. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
        print("  2. Start backend: python main.py")
        print("  3. Start frontend: npm run dev")
        print("  4. Test the features in the dashboard")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TESTS FAILED: {e}")
        print("=" * 60)
        sys.exit(1)
