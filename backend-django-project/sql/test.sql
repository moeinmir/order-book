CREATE DATABASE orderbook;
CREATE USER orderbook WITH PASSWORD 'mypasswormypasswordd';
ALTER ROLE orderbook SET client_encoding TO 'utf8';
ALTER ROLE orderbook SET default_transaction_isolation TO 'read committed';
ALTER ROLE orderbook SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE orderbook TO orderbook;

