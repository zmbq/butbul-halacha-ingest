"""
Test Hebrew date parsing and day of week extraction using pyluach.
"""

from datetime import date
from src.hebrew_date_utils import (
    parse_hebrew_numeral,
    parse_hebrew_year,
    parse_hebrew_date_string,
    hebrew_to_gregorian,
    get_day_of_week,
    parse_hebrew_date
)


def test_hebrew_numeral_parsing():
    """Test parsing of Hebrew numerals."""
    
    print("=" * 80)
    print("Testing Hebrew Numeral Parsing")
    print("=" * 80)
    
    test_cases = [
        ("ג'", 3),
        ('י"א', 11),
        ('כ"ה', 25),
        ("ת", 400),
        ('תשפ"ו', 786),
    ]
    
    passed = 0
    failed = 0
    
    for numeral, expected in test_cases:
        result = parse_hebrew_numeral(numeral)
        status = "✓" if result == expected else "✗"
        print(f"{status} {numeral:10} -> {result:5} (expected {expected})")
        if result == expected:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    print("=" * 80)
    return failed == 0


def test_hebrew_to_gregorian_conversion():
    """Test conversion of Hebrew dates to Gregorian dates."""
    
    print("\n" + "=" * 80)
    print("Testing Hebrew to Gregorian Conversion")
    print("=" * 80)
    
    # Test with known conversions (verified with pyluach)
    test_cases = [
        # 3 Tishrei 5786 = September 25, 2025 (Thursday)
        ("ג' תשרי התשפ\"ו", date(2025, 9, 25)),
        # 4 Tishrei 5786 = September 26, 2025 (Friday)
        ("ד' תשרי התשפ\"ו", date(2025, 9, 26)),
        # 11 Tishrei 5786 = October 3, 2025 (Friday) - Today!
        ('י"א תשרי התשפ\"ו', date(2025, 10, 3)),
    ]
    
    passed = 0
    failed = 0
    
    for hebrew_str, expected_gregorian in test_cases:
        result = hebrew_to_gregorian(hebrew_str)
        
        print(f"\nHebrew: {hebrew_str}")
        print(f"Expected: {expected_gregorian}")
        print(f"Got:      {result}")
        
        if result == expected_gregorian:
            print("✓ PASS")
            passed += 1
        else:
            print("✗ FAIL")
            failed += 1
    
    print(f"\n{'-' * 80}")
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)
    return failed == 0


def test_day_of_week_calculation():
    """Test day of week calculation from Hebrew dates."""
    
    print("\n" + "=" * 80)
    print("Testing Day of Week Calculation")
    print("=" * 80)
    
    # Test with verified dates from pyluach
    test_cases = [
        # Format: (hebrew_date, expected_day_name, expected_gregorian)
        ("ג' תשרי התשפ\"ו", "חמישי", date(2025, 9, 25)),      # 3 Tishrei 5786 = Thursday
        ("ד' תשרי התשפ\"ו", "שישי", date(2025, 9, 26)),      # 4 Tishrei 5786 = Friday
        ('י"א תשרי התשפ\"ו', "שישי", date(2025, 10, 3)),    # 11 Tishrei 5786 = Friday (Today!)
    ]
    
    passed = 0
    failed = 0
    
    for hebrew_str, expected_day, expected_greg in test_cases:
        day_name = get_day_of_week(hebrew_str)
        gregorian = hebrew_to_gregorian(hebrew_str)
        
        print(f"\nHebrew Date: {hebrew_str}")
        print(f"Gregorian:   {gregorian} (expected {expected_greg})")
        print(f"Day of Week: {day_name} (expected {expected_day})")
        
        # Verify the Gregorian date matches
        greg_match = gregorian == expected_greg
        day_match = day_name == expected_day
        
        if greg_match and day_match:
            print("✓ PASS")
            passed += 1
        else:
            print("✗ FAIL")
            if not greg_match:
                print(f"  Gregorian date mismatch!")
            if not day_match:
                print(f"  Day of week mismatch!")
            failed += 1
    
    print(f"\n{'-' * 80}")
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)
    return failed == 0


def test_real_world_examples():
    """Test with actual examples from the video data."""
    
    print("\n" + "=" * 80)
    print("Testing Real-World Examples from Video Data")
    print("=" * 80)
    
    real_examples = [
        "ג' תשרי התשפ\"ו",
        "ד' תשרי התשפ\"ו",
        "ו' תשרי התשפ\"ו",
        'י"א תשרי התשפ\"ו',
    ]
    
    for hebrew_str in real_examples:
        print(f"\n{'-' * 80}")
        print(f"Parsing: {hebrew_str}")
        
        parsed = parse_hebrew_date(hebrew_str)
        
        print(f"  Hebrew components: day={parsed['hebrew_day']}, month={parsed['hebrew_month']}, year={parsed['hebrew_year']}")
        print(f"  Gregorian date: {parsed['gregorian_date']}")
        print(f"  Day of week: {parsed['day_of_week_name']} ({parsed['day_of_week_abbrev']})")
        
        if parsed['gregorian_date']:
            # Show what day of week it actually is
            python_weekday = parsed['gregorian_date'].weekday()
            weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            print(f"  Verification: {weekday_names[python_weekday]}")
    
    print("\n" + "=" * 80)


def test_full_extraction_pipeline():
    """Test the full extraction pipeline like it would be used in extract_metadata.py"""
    
    print("\n" + "=" * 80)
    print("Testing Full Extraction Pipeline")
    print("=" * 80)
    
    # Simulate what extract_metadata.py does
    sample_titles = [
        "הגאון הרב אהרון בוטבול - הלכה יומית - ג' תשרי התשפ\"ו - יום כנגד שנה: כוחם של עשרת ימי תשובה",
        "הגאון הרב אהרון בוטבול - הלכה יומית - ד' תשרי התשפ\"ו - גדולה שבת שמסלקת את היסורים",
    ]
    
    for title in sample_titles:
        print(f"\n{'-' * 80}")
        print(f"Title: {title[:70]}...")
        
        # Extract date (similar to extract_metadata.py logic)
        text = title
        if text.startswith("הגאון הרב אהרון בוטבול - "):
            text = text.replace("הגאון הרב אהרון בוטבול - ", "", 1)
        if text.startswith("הלכה יומית - "):
            text = text.replace("הלכה יומית - ", "", 1)
        
        # Get the date part (before the next " - ")
        parts = text.split(" - ")
        hebrew_date_str = parts[0].strip()
        
        print(f"Extracted date string: {hebrew_date_str}")
        
        # Get day of week
        day_of_week = get_day_of_week(hebrew_date_str)
        gregorian = hebrew_to_gregorian(hebrew_date_str)
        
        print(f"Day of week: {day_of_week}")
        print(f"Gregorian: {gregorian}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🧪 Hebrew Date Conversion and Day of Week Tests\n")
    
    # Run all tests
    test1 = test_hebrew_numeral_parsing()
    test2 = test_hebrew_to_gregorian_conversion()
    test3 = test_day_of_week_calculation()
    test_real_world_examples()
    test_full_extraction_pipeline()
    
    print("\n" + "=" * 80)
    if test1 and test2 and test3:
        print("✓ ALL CRITICAL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 80 + "\n")
