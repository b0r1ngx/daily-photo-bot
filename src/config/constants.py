"""Application constants. Layer: Config (depends on: types only)."""

BOT_VERSION: str = '0.2.0'

# Schedule interval options (label, seconds)
SCHEDULE_INTERVALS: list[tuple[str, int]] = [
    ("5 min", 300),
    ("10 min", 600),
    ("30 min", 1800),
    ("1 hour", 3600),
    ("3 hours", 10800),
    ("6 hours", 21600),
    ("12 hours", 43200),
]

# Hours for fixed-time schedule picker
SCHEDULE_HOURS: list[int] = list(range(24))

# Minutes for fixed-time schedule picker
SCHEDULE_MINUTES: list[int] = [0, 15, 30, 45]

# Pexels API
PEXELS_SEARCH_URL: str = "https://api.pexels.com/v1/search"
PEXELS_PER_PAGE: int = 80
PEXELS_MAX_PAGE: int = 5

# Unsplash API
UNSPLASH_RANDOM_URL: str = "https://api.unsplash.com/photos/random"
UNSPLASH_COUNT: int = 20

# Photo sending
PHOTO_REQUEST_TIMEOUT: int = 10

# Conversation states
STATE_AWAITING_TOPIC: int = 0
STATE_MAIN_MENU: int = 1
STATE_AWAITING_NEW_TOPIC: int = 2
STATE_SCHEDULE_SELECT_TOPIC: int = 3
STATE_SCHEDULE_TYPE: int = 4
STATE_SCHEDULE_INTERVAL: int = 5
STATE_SCHEDULE_HOUR: int = 6
STATE_SCHEDULE_MINUTE: int = 7
STATE_TOPIC_MANAGE: int = 8
STATE_EDIT_TOPIC_NAME: int = 9

# Keyboard labels (used for matching in handlers)
KB_ADD_TOPIC: str = "➕ Add topic"
KB_MY_TOPICS: str = "📋 My Topics"
KB_SCHEDULE: str = "⏰ Schedule"
KB_BACK: str = "◀️ Back"
