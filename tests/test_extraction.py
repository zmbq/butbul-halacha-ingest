"""
Test the metadata extraction logic.
"""

from src.pipeline.s02_extract_metadata import extract_hebrew_date_and_subject
from src.hebrew_date_utils import get_day_of_week


def test_extraction():
    """Test extraction with sample data."""
    
    # Test cases from the actual data
    test_cases = [
        {
            "title": "הגאון הרב אהרון בוטבול - הלכה יומית - ג' תשרי התשפ\"ו - יום כנגד שנה: כוחם של עשרת ימי תשובה",
            "expected_date": "ג' תשרי התשפ\"ו",
            "expected_day_of_week": "חמישי",  # Thursday, Sept 25, 2025
            "expected_subject": "יום כנגד שנה: כוחם של עשרת ימי תשובה"
        },
        {
            "title": "הגאון הרב אהרון בוטבול - הלכה יומית - ד' תשרי התשפ\"ו - גדולה שבת שמסלקת את היסורים",
            "expected_date": "ד' תשרי התשפ\"ו",
            "expected_day_of_week": "שישי",  # Friday, Sept 26, 2025
            "expected_subject": "גדולה שבת שמסלקת את היסורים"
        },
        {
            "description": "הלכה יומית - י\"א תשרי התשפ\"ו - כיצד לרכוש ארבעת המינים?",
            "expected_date": "י\"א תשרי התשפ\"ו",
            "expected_day_of_week": "שישי",  # Friday, Oct 3, 2025 (today!)
            "expected_subject": "כיצד לרכוש ארבעת המינים?"
        }
    ]
    
    print("Testing metadata extraction:")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        text = test.get('title') or test.get('description')
        hebrew_date, subject = extract_hebrew_date_and_subject(text)
        day_of_week = get_day_of_week(hebrew_date) if hebrew_date else None
        
        print(f"\nTest {i}:")
        print(f"Input: {text[:80]}...")
        print(f"Expected Date: {test['expected_date']}")
        print(f"Extracted Date: {hebrew_date}")
        print(f"Expected Day of Week: {test['expected_day_of_week']}")
        print(f"Extracted Day of Week: {day_of_week}")
        print(f"Expected Subject: {test['expected_subject']}")
        print(f"Extracted Subject: {subject}")
        
        date_match = hebrew_date == test['expected_date']
        day_match = day_of_week == test['expected_day_of_week']
        subject_match = subject == test['expected_subject']
        
        if date_match and day_match and subject_match:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            if not date_match:
                print(f"  Date mismatch!")
            if not day_match:
                print(f"  Day of week mismatch!")
            if not subject_match:
                print(f"  Subject mismatch!")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_extraction()
