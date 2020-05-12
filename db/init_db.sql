CREATE DATABASE real_estate;
CREATE USER real_estate_user WITH PASSWORD '12345678';
ALTER ROLE real_estate_user SET client_encoding TO 'utf8';
ALTER ROLE real_estate_user SET timezone TO 'UTC';
ALTER USER real_estate_user CREATEDB;