-- 人员部分的建表语句：
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_keywords (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keyword VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);