--  This is for RDS bootstrapping.
SELECT 'CREATE DATABASE language_app'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'language_app')\gexec
\c language_app