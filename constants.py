
# Rank System: Maps level ranges to rank details
# Format: (min_level, max_level): (name, icon, color)
RANKS = {
    (1, 5): ('Bronze', 'fa-shield-halved', '#CD7F32'),  # Beginner
    (6, 10): ('Silver', 'fa-shield-halved', '#C0C0C0'),  # Intermediate
    (11, 20): ('Gold', 'fa-shield-halved', '#FFD700'),  # Advanced
    (21, 35): ('Platinum', 'fa-gem', '#E5E4E2'),  # Expert
    (36, 50): ('Diamond', 'fa-gem', '#b9f2ff'),  # Master
    (51, 75): ('Heroic', 'fa-crown', '#ff4d4d'),  # Elite
    (76, 100): ('Master', 'fa-crown', '#ff0000'),  # Legendary
    (101, 10000000000000): ('Grandmaster', 'fa-dragon', '#800080')
}

# Shop Items Catalog
SHOP_ITEMS = {
    # === THEMES ===
    'theme_neon_city': {
        'id': 'theme_neon_city',
        'name': 'Neon City Theme 🌃',
        'description': 'Urban neon lights cityscape.',
        'price': 3800,
        'icon': 'fa-city',
        'type': 'theme',
        'color': '#06b6d4'
    },
    'theme_sakura': {
        'id': 'theme_sakura',
        'name': 'Sakura Theme 🌸',
        'description': 'Cherry blossom pink serenity.',
        'price': 2800,
        'icon': 'fa-spa',
        'type': 'theme',
        'color': '#f9a8d4'
    },
    'theme_cyberpunk': {
        'id': 'theme_cyberpunk',
        'name': 'Cyberpunk Theme 🤖',
        'description': 'Neon purple visuals and glitch effects.',
        'price': 4000,
        'icon': 'fa-vr-cardboard',
        'type': 'theme',
        'color': '#d946ef'
    },
    'theme_synthwave': {
        'id': 'theme_synthwave',
        'name': 'Synthwave Theme 🎵',
        'description': '80s retro neon grid aesthetic.',
        'price': 3500,
        'icon': 'fa-compact-disc',
        'type': 'theme',
        'color': '#f472b6'
    },
     'theme_aurora': {
        'id': 'theme_aurora',
        'name': 'Aurora Theme 🌌',
        'description': 'Northern lights with flowing colors.',
        'price': 3000,
        'icon': 'fa-wand-magic-sparkles',
        'type': 'theme',
        'color': '#a78bfa'
    },
    
    # === FRAMES ===
    'frame_gold': {
        'id': 'frame_gold',
        'name': 'Golden Frame 🏆',
        'description': 'Shiny gold border with pulsing glow.',
        'price': 2500,
        'icon': 'fa-crown',
        'type': 'frame',
        'color': '#eab308'
    },
    'frame_diamond': {
        'id': 'frame_diamond',
        'name': 'Diamond Frame 💎',
        'description': 'Sparkling diamond border with shimmer.',
        'price': 7500,
        'icon': 'fa-gem',
        'type': 'frame',
        'color': '#a78bfa'
    },
    'frame_fire': {
        'id': 'frame_fire',
        'name': 'Fire Frame 🔥',
        'description': 'Blazing flames surrounding your avatar.',
        'price': 4000,
        'icon': 'fa-fire',
        'type': 'frame',
        'color': '#f97316'
    },
    'frame_ice': {
        'id': 'frame_ice',
        'name': 'Ice Frame ❄️',
        'description': 'Frozen crystal border with frost effect.',
        'price': 3500,
        'icon': 'fa-snowflake',
        'type': 'frame',
        'color': '#38bdf8'
    },
    'frame_glitch': {
        'id': 'frame_glitch',
        'name': 'Glitched Frame 👾',
        'description': 'Animated glitch effect with RGB split.',
        'price': 5000,
        'icon': 'fa-bug',
        'type': 'frame',
        'color': '#ef4444'
    },
    
    # === POWER UPS ===
    'xp_multiplier': {
        'id': 'xp_multiplier',
        'name': '2x XP Boost (24h) ⚡',
        'description': 'Double XP from all sources for 24 hours.',
        'price': 1500,
        'icon': 'fa-bolt',
        'type': 'consumable',
        'effect': 'xp_multiplier',
        'duration': 86400, # 24h
        'color': '#fbbf24'
    },
    'mega_xp_multiplier': {
        'id': 'mega_xp_multiplier',
        'name': '5x Mega Boost (1h) 🚀',
        'description': '5x XP for 1 hour! Good for intense grinding.',
        'price': 3000,
        'icon': 'fa-rocket',
        'type': 'consumable',
        'effect': 'mega_xp_multiplier',
        'duration': 3600, # 1h
        'color': '#f472b6'
    },
    'time_multiplier': {
        'id': 'time_multiplier',
        'name': 'Time Warp (24h) ⏳',
        'description': 'Focus sessions count as double time for quests.',
        'price': 2000,
        'icon': 'fa-hourglass-half',
        'type': 'consumable',
        'effect': 'time_multiplier',
        'duration': 86400,
        'color': '#38bdf8'
    },
    'xp_protection': {
        'id': 'xp_protection',
        'name': 'XP Shield (3 Battles) 🛡️',
        'description': 'No XP loss from lost battles (3 charges).',
        'price': 500,
        'icon': 'fa-shield-heart',
        'type': 'consumable',
        'effect': 'xp_protection',
        'duration': 86400 * 7, # 7 days to use
        'color': '#a3e635'
    },
     'instant_level': {
        'id': 'instant_level',
        'name': 'Level Up Potion 🧪',
        'description': 'Instantly gain 500 XP (Enough for 1 Level).',
        'price': 5000,
        'icon': 'fa-flask',
        'type': 'consumable',
        'effect': 'instant_level',
        'color': '#818cf8'
    }
}
