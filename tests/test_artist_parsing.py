#!/usr/bin/env python3
"""
Test script for the improved artist name parsing functionality
"""
import re

def clean_artist_name(artist_text):
    """
    Enhanced artist name cleaning function to handle various formats and remove duplications completely.
    Handles complex cases like groups+individuals, brands+artists, and remaining duplications.
    """
    if not artist_text:
        return ""
    
    # Normalize whitespace and newlines
    normalized = re.sub(r'\s+', ' ', artist_text.replace('\n', ' ')).strip()
    
    # Remove common prefixes/suffixes that might cause issues
    normalized = re.sub(r'^(featuring|feat\.?|ft\.?|with)\s+', '', normalized, flags=re.IGNORECASE)
    
    # Handle repeated artist names (like "Connie Francis Connie Francis")
    # Split by word and check for consecutive duplicates
    words = normalized.split()
    deduplicated_words = []
    prev_word = None
    
    for word in words:
        # Skip if current word is same as previous (case-insensitive)
        if prev_word is None or word.lower() != prev_word.lower():
            deduplicated_words.append(word)
            prev_word = word
    
    deduplicated_text = ' '.join(deduplicated_words)
    
    # Check for pattern repetition at phrase level (e.g., "Artist Name Artist Name")
    # Split by common delimiters first to avoid breaking valid artist names
    temp_delimiters = r'\s*[,&]\s*|\s+(?:featuring|feat\.?|ft\.?|with)\s+'
    temp_artists = [a.strip() for a in re.split(temp_delimiters, deduplicated_text, flags=re.IGNORECASE) if a.strip()]
    
    # For each artist segment, check for internal repetition
    processed_artists = []
    for artist_segment in temp_artists:
        # Check if artist name appears to be repeated within the segment
        words_in_segment = artist_segment.split()
        if len(words_in_segment) > 1:
            # Try to detect if first half equals second half
            mid = len(words_in_segment) // 2
            if (len(words_in_segment) % 2 == 0 and 
                ' '.join(words_in_segment[:mid]).lower() == ' '.join(words_in_segment[mid:]).lower()):
                # Use only first half if it's a perfect duplication
                artist_segment = ' '.join(words_in_segment[:mid])
        
        processed_artists.append(artist_segment)
    
    # Re-join and split again with all delimiters for final processing
    rejoined = ', '.join(processed_artists)
    delimiters = r'\s*[,&]\s*|\s+(?:featuring|feat\.?|ft\.?|with)\s+'
    artists = [a.strip() for a in re.split(delimiters, rejoined, flags=re.IGNORECASE) if a.strip()]
    
    # Remove duplicates while preserving order and handle special cases
    unique_artists = []
    seen_lower = set()
    
    for artist in artists:
        # Clean individual artist name
        cleaned = artist.strip()
        # Remove quotes and extra punctuation
        cleaned = re.sub(r'^["\'\s]+|["\'\s]+$', '', cleaned)
        
        # Additional cleaning for brand/label information (common patterns)
        cleaned = re.sub(r'\s*\([^)]*\)\s*$', '', cleaned)  # Remove parenthetical info at end
        cleaned = re.sub(r'\s*\[[^\]]*\]\s*$', '', cleaned)  # Remove bracketed info at end
        
        # Skip very short names or common non-artist words
        if len(cleaned) < 2:
            continue
            
        # Check for similarity to existing artists (handle slight variations)
        is_duplicate = False
        cleaned_lower = cleaned.lower()
        
        for seen in seen_lower:
            # Check if current artist is contained in or contains an existing one
            if (cleaned_lower in seen or seen in cleaned_lower) and abs(len(cleaned_lower) - len(seen)) <= 3:
                is_duplicate = True
                break
        
        if not is_duplicate and cleaned:
            unique_artists.append(cleaned)
            seen_lower.add(cleaned_lower)
    
    return ', '.join(unique_artists) if unique_artists else normalized

def test_artist_parsing():
    """Test cases for artist name parsing improvements"""
    test_cases = [
        # Duplication cases mentioned in POC review
        ("Connie Francis Connie Francis", "Connie Francis"),
        ("Taylor Swift Taylor Swift", "Taylor Swift"),
        
        # Complex featuring cases
        ("Artist A featuring Artist B & Artist C", "Artist A, Artist B, Artist C"),
        ("Main Artist feat. Guest Artist", "Main Artist, Guest Artist"),
        
        # Brand/label removal
        ("Artist Name (Official Music)", "Artist Name"),
        ("Singer [YG Entertainment]", "Singer"),
        
        # Multiple delimiters
        ("Artist1, Artist2 & Artist3 featuring Artist4", "Artist1, Artist2, Artist3, Artist4"),
        
        # Edge cases
        ("", ""),
        ("   ", ""),
        ("A", "A"),
        
        # Real-world complex cases
        ("BTS featuring Halsey (Big Hit Entertainment)", "BTS, Halsey"),
        ("NewJeans NewJeans & IVE", "NewJeans, IVE"),
    ]
    
    print("Testing improved artist name parsing...")
    print("=" * 60)
    
    all_passed = True
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = clean_artist_name(input_text)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        if result != expected:
            all_passed = False
        
        print(f"Test {i}: {status}")
        print(f"  Input:    '{input_text}'")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
        print()
    
    print("=" * 60)
    print(f"Overall Result: {'All tests passed!' if all_passed else 'Some tests failed!'}")
    return all_passed

if __name__ == "__main__":
    test_artist_parsing()