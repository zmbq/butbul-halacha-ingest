"""
Hebrew date utilities for parsing and converting Hebrew dates to Gregorian dates.
"""

import re
from datetime import date
from pyluach import dates


# Mapping of Hebrew month names to month numbers (following pyluach's numbering: Nissan=1, Tishrei=7)
HEBREW_MONTHS = {
    # Standard months
    "ניסן": 1,
    "אייר": 2,
    "סיון": 3,
    "סיוון": 3,  # Alternative spelling
    "תמוז": 4,
    "אב": 5,
    "אלול": 6,
    "תשרי": 7,
    "חשון": 8,
    "חשוון": 8,
    "כסלו": 9,
    "טבת": 10,
    "שבט": 11,
    "אדר": 12,
    "אדר א": 12,  # First Adar in leap year
    "אדר ב": 13,  # Second Adar in leap year (only in leap years)
}

# Hebrew numerals mapping
HEBREW_NUMERALS = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50, "ס": 60, "ע": 70, "פ": 80, "צ": 90,
    "ק": 100, "ר": 200, "ש": 300, "ת": 400
}


def parse_hebrew_numeral(numeral: str) -> int | None:
    """
    Parse a Hebrew numeral string to an integer.
    
    Examples:
        ג' -> 3
        י"א -> 11
        כ"ה -> 25
        
    Args:
        numeral: Hebrew numeral string
        
    Returns:
        Integer value or None if parsing fails
    """
    if not numeral:
        return None
    
    # Remove apostrophes and quotes
    cleaned = numeral.replace("'", "").replace('"', "")
    
    total = 0
    for char in cleaned:
        if char in HEBREW_NUMERALS:
            total += HEBREW_NUMERALS[char]
        else:
            return None
    
    return total if total > 0 else None


def parse_hebrew_year(year_str: str) -> int | None:
    """
    Parse a Hebrew year string.
    
    Examples:
        התשפ"ו -> 5786
        תשפ"ו -> 5786
        
    Args:
        year_str: Hebrew year string
        
    Returns:
        Full Hebrew year (e.g., 5786) or None
    """
    if not year_str:
        return None
    
    # Remove the ה prefix if present
    cleaned = year_str.replace("ה", "", 1) if year_str.startswith("ה") else year_str
    
    # Parse the numeral
    year_value = parse_hebrew_numeral(cleaned)
    
    if year_value is None:
        return None
    
    # Hebrew years in the 6th millennium (current era)
    # If we get a value like 786, it means 5786
    if year_value < 1000:
        year_value += 5000
    
    return year_value


def parse_hebrew_date_string(hebrew_date: str) -> tuple[int | None, int | None, int | None]:
    """
    Parse a Hebrew date string to extract day, month, and year.
    
    Expected format: "[day_of_week]? [day] [month] [year]"
    Examples:
        "ג' תשרי התשפ\"ו" -> (3, 1, 5786)
        "י\"א תשרי התשפ\"ו" -> (11, 1, 5786)
        "כ\"ה כסלו התשפ\"ו" -> (25, 3, 5786)
        
    Args:
        hebrew_date: Hebrew date string
        
    Returns:
        Tuple of (day, month, year) or (None, None, None) if parsing fails
    """
    if not hebrew_date:
        return None, None, None
    
    # Clean up the string - remove WhatsApp text if present
    date_str = hebrew_date.split('\n')[0].strip()
    
    # Check if it starts with a single letter day of week prefix (א', ב', ג', etc.)
    # Pattern: single letter + apostrophe + space
    single_letter_pattern = r"^([א-ת])'?\s+"
    match = re.match(single_letter_pattern, date_str)
    
    if match:
        # This could be a day of week (ג' = Tuesday) or a day number (ג' = 3rd)
        # If the match is a single letter, it's likely the day of the month
        # We'll use it as the day number
        letter = match.group(1)
        day = HEBREW_NUMERALS.get(letter)
        
        # Remove the prefix
        remaining = date_str[match.end():]
        
        # Parse the rest: [month] [year]
        parts = remaining.split()
        
        if len(parts) >= 2:
            month_name = parts[0]
            month = HEBREW_MONTHS.get(month_name)
            # Year token may be split (e.g. 'התשפ"' and 'ג'), try parsing parts[1]
            year = parse_hebrew_year(parts[1])
            if year is None and len(parts) >= 3:
                # Try joining the next token (remove intervening space)
                candidate = parts[1] + parts[2]
                year = parse_hebrew_year(candidate)
            
            return day, month, year
    
    # Handle "שבת" prefix
    if date_str.startswith("שבת "):
        date_str = date_str.replace("שבת ", "", 1)
    
    # Split into parts - expecting [day] [month] [year]
    parts = date_str.split()
    
    if len(parts) < 3:
        return None, None, None
    
    # Parse day (first part)
    day = parse_hebrew_numeral(parts[0])
    
    # Parse month (second part)
    month_name = parts[1]
    month = HEBREW_MONTHS.get(month_name)
    
    # Parse year (third part). Handle case where year is split across tokens
    year = parse_hebrew_year(parts[2])
    if year is None and len(parts) >= 4:
        # Try joining parts[2] and parts[3] (e.g., 'התשפ"' + 'ג' -> 'התשפ"ג')
        candidate = parts[2] + parts[3]
        year = parse_hebrew_year(candidate)
    
    return day, month, year


def hebrew_to_gregorian(hebrew_date_str: str) -> date | None:
    """
    Convert a Hebrew date string to a Gregorian date.
    
    Args:
        hebrew_date_str: Hebrew date string (e.g., "ג' תשרי התשפ\"ו")
        
    Returns:
        Python date object or None if conversion fails
    """
    day, month, year = parse_hebrew_date_string(hebrew_date_str)
    
    if day is None or month is None or year is None:
        return None
    
    try:
        # Create HebrewDate object
        hebrew_date = dates.HebrewDate(year, month, day)
        
        # Convert to Gregorian
        gregorian_date = hebrew_date.to_pydate()
        
        return gregorian_date
    except (ValueError, AttributeError) as e:
        # Invalid date
        return None


def get_day_of_week(hebrew_date_str: str) -> str | None:
    """
    Get the day of week from a Hebrew date string.
    
    Args:
        hebrew_date_str: Hebrew date string
        
    Returns:
        Hebrew day name (e.g., "ראשון", "שני", "שלישי") or None if conversion fails
    """
    gregorian = hebrew_to_gregorian(hebrew_date_str)
    
    if gregorian is None:
        return None
    
    # Python's weekday(): Monday=0, Sunday=6
    # Convert to Hebrew days: Sunday=0, Monday=1, etc.
    weekday = gregorian.weekday()
    
    # Convert Python weekday (Mon=0) to Hebrew weekday (Sun=0)
    hebrew_weekday = (weekday + 1) % 7
    
    hebrew_days = [
        "ראשון",   # Sunday (0)
        "שני",     # Monday (1)
        "שלישי",   # Tuesday (2)
        "רביעי",   # Wednesday (3)
        "חמישי",   # Thursday (4)
        "שישי",    # Friday (5)
        "שבת"      # Saturday (6)
    ]
    
    return hebrew_days[hebrew_weekday]


def get_day_abbreviation(day_name: str) -> str | None:
    """
    Get the abbreviated form of a Hebrew day name.
    
    Args:
        day_name: Full Hebrew day name (e.g., "שלישי")
        
    Returns:
        Abbreviated form (e.g., "ג'") or None
    """
    abbreviations = {
        "ראשון": "א'",
        "שני": "ב'",
        "שלישי": "ג'",
        "רביעי": "ד'",
        "חמישי": "ה'",
        "שישי": "ו'",
        "שבת": "שבת"
    }
    
    return abbreviations.get(day_name)


def parse_hebrew_date(hebrew_date_str: str) -> dict:
    """
    Parse a Hebrew date string and extract all components including Gregorian conversion.
    
    Args:
        hebrew_date_str: Hebrew date string (e.g., "ג' תשרי התשפ\"ו")
        
    Returns:
        Dictionary with parsed information
    """
    day, month, year = parse_hebrew_date_string(hebrew_date_str)
    gregorian = hebrew_to_gregorian(hebrew_date_str)
    day_name = get_day_of_week(hebrew_date_str)
    day_abbrev = get_day_abbreviation(day_name) if day_name else None
    
    return {
        "original": hebrew_date_str,
        "hebrew_day": day,
        "hebrew_month": month,
        "hebrew_year": year,
        "gregorian_date": gregorian,
        "day_of_week_name": day_name,
        "day_of_week_abbrev": day_abbrev
    }
