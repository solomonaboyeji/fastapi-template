CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    disabled BOOLEAN DEFAULT FALSE,
    hashed_password VARCHAR(255) NOT NULL,
    scopes VARCHAR[] DEFAULT '{}',
    email_verified BOOLEAN DEFAULT FALSE
);
