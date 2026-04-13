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
    
    # Define categories with their keywords (all in UPPER CASE)
    categories = {
        'Arts & Culture': [
            'ART', 'GALLERY', 'EXHIBIT', 'EXHIBITION', 'PAINTING', 'SCULPTURE',
            'ARTIST', 'MUSEUM', 'CRAFT', 'POTTERY', 'DRAWING', 'CREATIVE',
            'VISUAL', 'STUDIO', 'ARTISAN', 'HANDMADE', 'SHOW'
        ],

        'Community & Civic': [
            'COMMUNITY', 'CIVIC',
            'COMMUNITY', 'MEETING', 'GATHERING', 'CLUB', 'ORGANIZATION',
            'GROUP', 'VOLUNTEER', 'CHARITY', 'FUNDRAISER', 'DONATION',
            'SERVICE', 'CIVIC', 'TOWN', 'NEIGHBORHOOD', 'LOCAL', 'PUBLIC'
        ],

        'Education & Workshops': [
            'EDUCATION', 'WORKSHOP', 'LEARNING'
        ],
        
        'Family & Kids': [
            'FAMILY', 'KIDS', 'YOUTH', 
            'FAMILY', 'KIDS', 'CHILDREN', 'YOUTH', 'PARENT', 'CHILD',
            'TODDLER', 'BABY', 'TEEN', 'STORY', 'STORYTIME', 'PLAYGROUND',
            'ACTIVITIES', 'FRIENDLY',
        ],

        'Games': [
            'PUZZLE', 'CHESS', 'GAMES', 'TRIVIA', 'BINGO'
        ],

        'Health & Wellness': [
            'HEALTH', 'WELLNESS', 'MEDITATION'
        ],

        'History': [
            'HISTORY', 'HISTORIC', 'HISTORICAL', 'HERITAGE', 'MUSEUM',
            'TOUR', 'CIVIL', 'WAR', 'COLONIAL', 'REVOLUTION', 'GHOST',
            'HAUNTED', 'ARCHAEOLOGICAL', 'ANTIQUE', 'PRESERVATION', 'LEGACY',
            'GHOST'
        ],

        'Holidays & Fairs': [
            'HOLIDAY', 'CHRISTMAS', 'HALLOWEEN', 'THANKSGIVING', 'EASTER',
            'VALENTINE', 'INDEPENDENCE', 'MEMORIAL'
        ],

        "Film & Performing Arts": [
            'THEATER', 'THEATRE', 'PLAY', 'DRAMA', 'COMEDY', 'MUSICAL',
            'PRODUCTION', 'STAGE', 'PERFORMANCE', 'ACTING', 'ACTOR', 'SHOW',
            'REHEARSAL', 'BROADWAY', 'IMPROV',
            'FILM', 'MOVIE', 'CINEMA', 'SCREENING', 'DOCUMENTARY', 'SHORT',
            'FEATURE', 'PREMIERE', 'FESTIVAL', 'VIDEO', 'ANIMATION',
            'MUSIC', 'CONCERT', 'BAND', 'SINGER', 'JAZZ', 'ROCK', 'CLASSICAL',
            'ORCHESTRA', 'PERFORMANCE', 'LIVE', 'ACOUSTIC', 'FOLK', 'BLUES',
            'COUNTRY', 'POP', 'INSTRUMENTAL', 'SONG', 'GUITAR', 'PIANO'
        ],
        
        'Outdoors & Nature': [
            'BIRD', 'BIRDING', 'HIKE', 'NATURE', 'OUTDOOR', 'PRESERVE', 
            'OUTDOOR', 'NATURE', 'HIKING', 'TRAIL', 'PARK', 'GARDEN',
            'WILDLIFE', 'CAMPING', 'FISHING', 'KAYAK', 'BIKE', 'WALK',
            'TOUR', 'ADVENTURE', 'ENVIRONMENTAL', 'CONSERVATION', 'TREES'
        ],
                
        'Seniors': [
            'SENIOR'
        ],

        'Spiritual & Religious': [
            'SPIRITUAL', 'RELIGIOUS'
        ],

        'Sports': [
            'SPORTS', 'TOURNAMENT', 'RACE', 'CHAMPIONSHIP', 'LEAGUE',
            'FOOTBALL', 'BASKETBALL', 'BASEBALL', 'SOCCER', 'TENNIS',
            'GOLF', 'RUNNING', 'MARATHON', 'ATHLETIC'
        ],
        
        "Health & Wellness": [
            'YOGA', 'T’AI CHI', 'QIGONG'
        ]
                
    }
    
    # Convert title to uppercase and split into words
    title_upper = title.upper()
    # Remove common punctuation and split
    # title_words = title_upper.replace(',', ' ').replace('.', ' ').replace('!', ' ').replace('?', ' ').split()
    title_words = title_upper.replace(',', ' ').replace('.', ' ').replace('!', ' ').replace('?', ' ').replace("’", "") #.split()

    
    # Find matching categories
    matched_categories = []
    
    for category, keywords in categories.items():
        # Check if any word from the title matches any keyword in this category
        for word in keywords:
            if word in title_words:
                # print('category:', category, 'word:', word, 'title_words:', title_words)
                matched_categories.append(category)
                break  # Only add category once, even if multiple keywords match
    
    return matched_categories


