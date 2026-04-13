#!/usr/bin/env python3
"""
Category Matcher Function
Matches title words against category keywords and returns matching categories
"""

def categorize_by_keywords(title):
    """
    Categorize a title based on keyword matching.
    
    Args:
        title (str): The title string to categorize
        
    Returns:
        list: Array of categories that had keyword matches
    """
    
    # Define 12 categories with their keywords (all in UPPER CASE)
    categories = {
        'Arts & Culture': [
            'ART', 'GALLERY', 'EXHIBIT', 'EXHIBITION', 'PAINTING', 'SCULPTURE',
            'ARTIST', 'MUSEUM', 'CRAFT', 'POTTERY', 'DRAWING', 'CREATIVE',
            'VISUAL', 'STUDIO', 'ARTISAN', 'HANDMADE', 'SHOW'
        ],

        'Music': [
            'MUSIC', 'CONCERT', 'BAND', 'SINGER', 'JAZZ', 'ROCK', 'CLASSICAL',
            'ORCHESTRA', 'PERFORMANCE', 'LIVE', 'ACOUSTIC', 'FOLK', 'BLUES',
            'COUNTRY', 'POP', 'INSTRUMENTAL', 'SONG', 'GUITAR', 'PIANO'
        ],

        'Community & Civic': [
            'COMMUNITY', 'CIVIC',
            'COMMUNITY', 'MEETING', 'GATHERING', 'CLUB', 'ORGANIZATION',
            'GROUP', 'VOLUNTEER', 'CHARITY', 'FUNDRAISER', 'DONATION',
            'SERVICE', 'CIVIC', 'TOWN', 'NEIGHBORHOOD', 'LOCAL', 'PUBLIC'
        ],

        'Film & Theater': [
            'THEATER', 'THEATRE', 'PLAY', 'DRAMA', 'COMEDY', 'MUSICAL',
            'PRODUCTION', 'STAGE', 'PERFORMANCE', 'ACTING', 'ACTOR', 'SHOW',
            'REHEARSAL', 'BROADWAY', 'IMPROV',
            'FILM', 'MOVIE', 'CINEMA', 'SCREENING', 'DOCUMENTARY', 'SHORT',
            'FEATURE', 'PREMIERE', 'FESTIVAL', 'VIDEO', 'ANIMATION'
        ],

        'Education & Workshops': [
            'EDUCATION', 'WORKSHOP'
        ],
        
        'History': [
            'HISTORY', 'HISTORIC', 'HISTORICAL', 'HERITAGE', 'MUSEUM',
            'TOUR', 'CIVIL', 'WAR', 'COLONIAL', 'REVOLUTION', 'GHOST',
            'HAUNTED', 'ARCHAEOLOGICAL', 'ANTIQUE', 'PRESERVATION', 'LEGACY'
        ],

        'Health & Wellness': [
            'HEALTH', 'WELLNESS'
        ],
        
        'Outdoors & Nature': [
            'BIRD', 'BIRDING', 'HIKE', 'NATURE', 'OUTDOOR', 'PRESERVE', 
            'OUTDOOR', 'NATURE', 'HIKING', 'TRAIL', 'PARK', 'GARDEN',
            'WILDLIFE', 'CAMPING', 'FISHING', 'KAYAK', 'BIKE', 'WALK',
            'TOUR', 'ADVENTURE', 'ENVIRONMENTAL', 'CONSERVATION', 'TREES'
        ],

        'Family & Kids': [
            'FAMILY', 'KIDS', 'YOUTH', 
            'FAMILY', 'KIDS', 'CHILDREN', 'YOUTH', 'PARENT', 'CHILD',
            'TODDLER', 'BABY', 'TEEN', 'STORY', 'STORYTIME', 'PLAYGROUND',
            'ACTIVITIES', 'FRIENDLY',
        ],
        
        'Food & Drink': [
            'FOOD', 'DRINK'
        ],
        
        'Festivals & Fairs': [
            'HOLIDAY', 'CHRISTMAS', 'HALLOWEEN', 'THANKSGIVING', 'EASTER',
            'VALENTINES', 'INDEPENDENCE', 'MEMORIAL', 'LABOR', 'CELEBRATION',
            'FESTIVAL', 'SEASONAL', 'WINTER', 'SPRING', 'SUMMER', 'FALL',
            'AUTUMN', 'NEW', 'YEAR'
        ],
        
        'Sports & Recreation': [
            'SPORTS', 'GAME', 'TOURNAMENT', 'RACE', 'CHAMPIONSHIP', 'LEAGUE',
            'TEAM', 'FOOTBALL', 'BASKETBALL', 'BASEBALL', 'SOCCER', 'TENNIS',
            'GOLF', 'RUNNING', 'MARATHON', 'FITNESS', 'ATHLETIC', 'COMPETITION'
        ],
        
        'Spiritual & Religious': [
            'SPIRITUAL', 'RELIGIOUS'
        ],
        
        'Business & Networking': [
            'COMMUNITY', 'MEETING', 'GATHERING', 'CLUB', 'ORGANIZATION',
            'GROUP', 'VOLUNTEER', 'CHARITY', 'FUNDRAISER', 'DONATION',
            'SERVICE', 'CIVIC', 'TOWN', 'NEIGHBORHOOD', 'LOCAL', 'PUBLIC'
        ],
        
        'Volunteering & Service': [
            'COMMUNITY', 'MEETING', 'GATHERING', 'CLUB', 'ORGANIZATION',
            'GROUP', 'VOLUNTEER', 'CHARITY', 'FUNDRAISER', 'DONATION',
            'SERVICE', 'CIVIC', 'TOWN', 'NEIGHBORHOOD', 'LOCAL', 'PUBLIC'
        ]
    }
    
    # Convert title to uppercase and split into words
    title_upper = title.upper()
    # Remove common punctuation and split
    title_words = title_upper.replace(',', ' ').replace('.', ' ').replace('!', ' ').replace('?', ' ').split()
    
    # Find matching categories
    matched_categories = []
    
    for category, keywords in categories.items():
        # Check if any word from the title matches any keyword in this category
        for word in title_words:
            if word in keywords:
                matched_categories.append(category)
                break  # Only add category once, even if multiple keywords match
    
    return matched_categories


def categorize_by_keywords_detailed(title):
    """
    Categorize a title based on keyword matching with detailed results.
    
    Args:
        title (str): The title string to categorize
        
    Returns:
        dict: Dictionary with 'categories' (list) and 'matches' (dict showing which keywords matched)
    """
    
    # Define 12 categories with their keywords (all in UPPER CASE)
    categories = {
        'ARTS': [
            'ART', 'GALLERY', 'EXHIBIT', 'EXHIBITION', 'PAINTING', 'SCULPTURE',
            'ARTIST', 'MUSEUM', 'CRAFT', 'POTTERY', 'DRAWING', 'CREATIVE',
            'VISUAL', 'STUDIO', 'ARTISAN', 'HANDMADE', 'SHOW'
        ],
        
        'MUSIC': [
            'MUSIC', 'CONCERT', 'BAND', 'SINGER', 'JAZZ', 'ROCK', 'CLASSICAL',
            'ORCHESTRA', 'PERFORMANCE', 'LIVE', 'ACOUSTIC', 'FOLK', 'BLUES',
            'COUNTRY', 'POP', 'INSTRUMENTAL', 'SONG', 'GUITAR', 'PIANO'
        ],
        
        'THEATER': [
            'THEATER', 'THEATRE', 'PLAY', 'DRAMA', 'COMEDY', 'MUSICAL',
            'PRODUCTION', 'STAGE', 'PERFORMANCE', 'ACTING', 'ACTOR', 'SHOW',
            'REHEARSAL', 'BROADWAY', 'IMPROV'
        ],
        
        'FILM': [
            'FILM', 'MOVIE', 'CINEMA', 'SCREENING', 'DOCUMENTARY', 'SHORT',
            'FEATURE', 'PREMIERE', 'FESTIVAL', 'VIDEO', 'ANIMATION'
        ],
        
        'FOOD': [
            'FOOD', 'RESTAURANT', 'DINING', 'DINNER', 'LUNCH', 'BREAKFAST',
            'BRUNCH', 'COOKING', 'CHEF', 'CUISINE', 'MEAL', 'TASTING',
            'WINE', 'BEER', 'CAFE', 'COFFEE', 'BAKERY', 'MARKET', 'FARMERS'
        ],
        
        'SPORTS': [
            'SPORTS', 'GAME', 'TOURNAMENT', 'RACE', 'CHAMPIONSHIP', 'LEAGUE',
            'TEAM', 'FOOTBALL', 'BASKETBALL', 'BASEBALL', 'SOCCER', 'TENNIS',
            'GOLF', 'RUNNING', 'MARATHON', 'FITNESS', 'ATHLETIC', 'COMPETITION'
        ],
        
        'EDUCATION': [
            'EDUCATION', 'WORKSHOP', 'CLASS', 'SEMINAR', 'LECTURE', 'TRAINING',
            'COURSE', 'LEARNING', 'TEACHING', 'SCHOOL', 'COLLEGE', 'UNIVERSITY',
            'STUDY', 'TUTORIAL', 'LESSON', 'INSTRUCTION', 'CERTIFICATION'
        ],
        
        'COMMUNITY': [
            'COMMUNITY', 'MEETING', 'GATHERING', 'CLUB', 'ORGANIZATION',
            'GROUP', 'VOLUNTEER', 'CHARITY', 'FUNDRAISER', 'DONATION',
            'SERVICE', 'CIVIC', 'TOWN', 'NEIGHBORHOOD', 'LOCAL', 'PUBLIC'
        ],
        
        'FAMILY': [
            'FAMILY', 'KIDS', 'CHILDREN', 'YOUTH', 'PARENT', 'CHILD',
            'TODDLER', 'BABY', 'TEEN', 'STORY', 'STORYTIME', 'PLAYGROUND',
            'ACTIVITIES', 'FRIENDLY'
        ],
        
        'OUTDOOR': [
            'OUTDOOR', 'NATURE', 'HIKING', 'TRAIL', 'PARK', 'GARDEN',
            'WILDLIFE', 'CAMPING', 'FISHING', 'KAYAK', 'BIKE', 'WALK',
            'TOUR', 'ADVENTURE', 'ENVIRONMENTAL', 'CONSERVATION', 'TREES'
        ],
        
        'HISTORY': [
            'HISTORY', 'HISTORIC', 'HISTORICAL', 'HERITAGE', 'MUSEUM',
            'TOUR', 'CIVIL', 'WAR', 'COLONIAL', 'REVOLUTION', 'GHOST',
            'HAUNTED', 'ARCHAEOLOGICAL', 'ANTIQUE', 'PRESERVATION', 'LEGACY'
        ],
        
        'HOLIDAY': [
            'HOLIDAY', 'CHRISTMAS', 'HALLOWEEN', 'THANKSGIVING', 'EASTER',
            'VALENTINES', 'INDEPENDENCE', 'MEMORIAL', 'LABOR', 'CELEBRATION',
            'FESTIVAL', 'SEASONAL', 'WINTER', 'SPRING', 'SUMMER', 'FALL',
            'AUTUMN', 'NEW', 'YEAR'
        ]
    }
    
    # Convert title to uppercase and split into words
    title_upper = title.upper()
    title_words = title_upper.replace(',', ' ').replace('.', ' ').replace('!', ' ').replace('?', ' ').split()
    
    # Find matching categories with details
    matched_categories = []
    matches = {}
    
    for category, keywords in categories.items():
        matched_words = []
        for word in title_words:
            if word in keywords:
                matched_words.append(word)
        
        if matched_words:
            matched_categories.append(category)
            matches[category] = matched_words
    
    return {
        'categories': matched_categories,
        'matches': matches
    }


# Test examples
if __name__ == "__main__":
    print("="*70)
    print("CATEGORY MATCHER - TEST EXAMPLES")
    print("="*70)
    
    # Test cases
    test_titles = [
        "Ghost Tour! History Tour!!",
        "Live Music Concert at the Park",
        "Family Movie Night",
        "Farmers Market and Food Festival",
        "Christmas Art Show",
        "Community Workshop on Gardening",
        "Youth Soccer Tournament",
        "Historic Walking Tour",
        "Jazz Band Performance at Local Theater",
        "Outdoor Adventure Hiking Trail"
    ]
    
    print("\nBasic Function (categorize_by_keywords):")
    print("-" * 70)
    for title in test_titles:
        categories = categorize_by_keywords(title)
        print(f"\nTitle: '{title}'")
        print(f"Categories: {categories}")
    
    print("\n\n" + "="*70)
    print("Detailed Function (categorize_by_keywords_detailed):")
    print("-" * 70)
    
    # Show detailed results for a few examples
    detailed_examples = [
        "Ghost Tour! History Tour!!",
        "Live Music Concert at the Park",
        "Family Movie Night"
    ]
    
    for title in detailed_examples:
        result = categorize_by_keywords_detailed(title)
        print(f"\nTitle: '{title}'")
        print(f"Matched Categories: {result['categories']}")
        print(f"Keyword Matches:")
        for category, words in result['matches'].items():
            print(f"  {category}: {words}")
    
    print("\n" + "="*70)
    print("USAGE EXAMPLES")
    print("="*70)
    
    # Example 1: Simple usage
    print("\n# Example 1: Simple usage")
    print("categories = categorize_by_keywords('Summer Music Festival')")
    result = categorize_by_keywords('Summer Music Festival')
    print(f"Result: {result}")
    
    # Example 2: Check if specific category matched
    print("\n# Example 2: Check if specific category matched")
    title = "Winter Art Gallery Show"
    categories = categorize_by_keywords(title)
    print(f"Title: '{title}'")
    print(f"Is ARTS category? {'ARTS' in categories}")
    print(f"Is MUSIC category? {'MUSIC' in categories}")
    
    # Example 3: Multiple category matches
    print("\n# Example 3: Count categories")
    title = "Community Theater Musical Performance"
    categories = categorize_by_keywords(title)
    print(f"Title: '{title}'")
    print(f"Number of matching categories: {len(categories)}")
    print(f"Categories: {categories}")
