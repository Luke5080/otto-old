USE network_application_db;

CREATE TABLE IF NOT EXISTS network_applications (
    app_name VARCHAR(255) NOT NULL PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    ip_address VARCHAR(255)
);
