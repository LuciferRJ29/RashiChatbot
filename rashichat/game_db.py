"""
RashiChatbot Game Database Collections
Uses sync PyMongo (mongodb) from rashichat.__init__
All game data stored in 'Rashi' database, separate collections.
"""
from rashichat import mongodb

# Game collections
users_col = mongodb.game_users          # Player profiles (coins, xp, kills, inventory, etc.)
groups_col = mongodb.game_groups        # Group data (msg count, claim status)
group_members_col = mongodb.group_members  # (user_id, group_id) mapping for group ranking
gangs_col = mongodb.gangs               # Gang data
riddles_col = mongodb.riddles           # Active riddles per group

# Create indexes for fast queries
try:
    users_col.create_index("user_id", unique=True)
    users_col.create_index("balance")
    users_col.create_index("kills")
    groups_col.create_index("chat_id", unique=True)
    group_members_col.create_index([("user_id", 1), ("group_id", 1)], unique=True)
    group_members_col.create_index("group_id")
    gangs_col.create_index("name")
    riddles_col.create_index("chat_id")
except Exception:
    pass
