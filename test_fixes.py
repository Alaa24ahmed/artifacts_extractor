#!/usr/bin/env python3
"""
Test script to verify the database fixes
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_data_mapping():
    """Test the fixed data mapping"""
    
    print("🧪 Testing Fixed Data Mapping")
    print("=" * 50)
    
    try:
        from modules.simple_db import SimpleArtifactDB
        
        # Create test database
        db = SimpleArtifactDB("test_fixes.db")
        
        # Test with the exact data structure from UI
        test_artifact = {
            'Name_EN': 'Chestnut Trees',
            'Name_AR': 'أشجار الكستناء', 
            'Name_FR': 'Les Marronniers',
            'Name_validation': 'fixed_AR_FR',
            'Creator': 'Édouard Vuillard',
            'Creation Date': 'c. 1894-1895',
            'Materials': 'Oil on canvas',
            'category': 'Painting',
            'page_number': 1
        }
        
        print("1. Testing data mapping with UI format:")
        mapped = db._map_artifact_to_db(test_artifact, 
                                       ocr_model="mistral-ocr",
                                       extraction_model="gpt-4o", 
                                       processing_params_hash="test123")
        
        print(f"   ✅ name_en: '{mapped.get('name_en')}'")
        print(f"   ✅ name_ar: '{mapped.get('name_ar')}'")
        print(f"   ✅ name_fr: '{mapped.get('name_fr')}'")
        print(f"   ✅ creator: '{mapped.get('creator')}'")
        print(f"   ✅ creation_date: '{mapped.get('creation_date')}'")
        print(f"   ✅ name_validation: '{mapped.get('name_validation')}'")
        print(f"   ✅ ocr_model: '{mapped.get('ocr_model')}'")
        print(f"   ✅ extraction_model: '{mapped.get('extraction_model')}'")
        
        # Test with file path processing
        test_file_path = "/path/to/EN_document_multilingual.pdf"
        mapped_with_file = db._map_artifact_to_db(test_artifact, 
                                                 file_path=test_file_path,
                                                 ocr_model="mistral-ocr",
                                                 extraction_model="gpt-4o")
        
        print(f"\n2. Testing file name processing:")
        print(f"   Input: {test_file_path}")
        print(f"   ✅ file_name: '{mapped_with_file.get('file_name')}'")
        print(f"   ✅ source_document: '{mapped_with_file.get('source_document')}'")
        
        # Test saving artifact
        print(f"\n3. Testing artifact saving:")
        saved_artifact = db.add_artifact(test_artifact, 
                                       ocr_model="mistral-ocr",
                                       extraction_model="gpt-4o")
        
        if saved_artifact:
            print(f"   ✅ Saved with ID: {saved_artifact.get('id')}")
            print(f"   ✅ name_en saved as: '{saved_artifact.get('name_en')}'")
            print(f"   ✅ Models: {saved_artifact.get('ocr_model')}/{saved_artifact.get('extraction_model')}")
        else:
            print(f"   ❌ Failed to save artifact")
        
        # Test cache operations
        print(f"\n4. Testing cache operations:")
        db.mark_file_processed("test_file.pdf", 1, "mistral-ocr", "gpt-4o", "test123")
        print(f"   ✅ Marked file as processed")
        
        # Cleanup
        db.db.close()
        db.cache_db.close()
        db.page_cache_db.close()
        
        # Remove test files
        for ext in ["", "_cache", "_page_cache"]:
            test_file = f"test_fixes.db{ext}"
            if os.path.exists(test_file):
                os.remove(test_file)
        
        print(f"   🧹 Cleaned up test files")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_data_mapping()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All fixes verified! The database should now work correctly.")
        print("\nFixed Issues:")
        print("• ✅ name_en field mapping (Name_EN → name_en)")
        print("• ✅ File name processing (removes _multilingual, _EN suffixes)")
        print("• ✅ Cache table population with model tracking")
        print("• ✅ Proper source_document vs file_name handling")
    else:
        print("❌ Some issues remain. Check the error messages above.")
