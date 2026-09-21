CREATE TABLE schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    whatsapp_number TEXT NOT NULL,
    scheduled_time DATETIME NOT NULL,
    message_content TEXT NOT NULL,
    template_name TEXT DEFAULT NULL,       -- Set if using approved template
    template_params TEXT DEFAULT NULL,     -- JSON array of parameters
    status TEXT CHECK(status IN ('PENDING', 'SENT', 'FAILED')) DEFAULT 'PENDING',
    response_log TEXT DEFAULT NULL,        -- Stores error message or Meta Message ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);