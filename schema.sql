-- Operation (e.g., a suspected influence campaign)
CREATE TABLE IF NOT EXISTS operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    suspected_actor TEXT,
    region TEXT,
    time_range TEXT,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Channel (e.g., Twitter account, Telegram, etc.)
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    platform TEXT,
    url TEXT,
    notes TEXT,
    FOREIGN KEY (operation_id) REFERENCES operations(id)
);

-- Indicators attached to channels
CREATE TABLE IF NOT EXISTS indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    type TEXT CHECK(type IN ('technical', 'behavioral')) NOT NULL,
    name TEXT NOT NULL,
    weight INTEGER NOT NULL,
    confidence TEXT CHECK(confidence IN ('High', 'Medium', 'Low')),
    evidence TEXT,
    source_type TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels(id)
);

-- Relationships between channels within an operation
CREATE TABLE IF NOT EXISTS channel_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id INTEGER NOT NULL,
    from_channel_id INTEGER NOT NULL,
    to_channel_id INTEGER NOT NULL,
    link_type TEXT,
    confidence TEXT,
    evidence TEXT,
    FOREIGN KEY (operation_id) REFERENCES operations(id),
    FOREIGN KEY (from_channel_id) REFERENCES channels(id),
    FOREIGN KEY (to_channel_id) REFERENCES channels(id)
);

CREATE TABLE IF NOT EXISTS indicator_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_type TEXT CHECK(group_type IN ('technical', 'behavioral')) NOT NULL,
    category TEXT NOT NULL,
    subtype TEXT NOT NULL,
    default_weight INTEGER NOT NULL,
    default_confidence TEXT CHECK(default_confidence IN ('High', 'Medium', 'Low')) NOT NULL
);


