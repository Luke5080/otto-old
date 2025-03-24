USE authentication_db;

CREATE TABLE IF NOT EXISTS network_applications (
    username VARCHAR(255) NOT NULL PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    ip_address VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(255) NOT NULL PRIMARY KEY,
    password VARCHAR(255) NOT NULL
);

INSERT INTO users(name, username, password) VALUES('admin', 'admin');
