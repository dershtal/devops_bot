
CREATE USER repl_user REPLICATION LOGIN PASSWORD 'Qq12345';

CREATE DATABASE base_pt;

\c base_pt;

CREATE TABLE IF NOT EXISTS phone_numbers (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) NOT NULL
);

INSERT INTO emails (email) VALUES ('dershtal@gmail.com'), ('dershtal@yandex.ru');
INSERT INTO phone_numbers (phone_number) VALUES ('89675431212'), ('+79685311551');