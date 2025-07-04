-- setup_database.sql
-- Purpose: Initializes the student_db database for the EduEnroll application.
-- Clears existing database (if any) and creates tables for admins and students.
-- Inserts a default admin user for authentication.

-- Drop the database if it exists to start fresh
DROP DATABASE IF EXISTS student_db;

-- Create the student_db database
CREATE DATABASE student_db;

-- Use the student_db database
USE student_db;

-- Create the admins table to store admin credentials
CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

-- Create the students table to store student information
CREATE TABLE students (
    student_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT,
    gender CHAR(10),
    department VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(15),
    status BOOLEAN DEFAULT TRUE
);

-- Insert a default admin user (plain-text password as per requirement)
INSERT INTO admins (username, password_hash) VALUES ('root', 'BatmanGokuSuper@12');

-- Grant privileges to the root user (optional, ensures access)
GRANT ALL PRIVILEGES ON student_db.* TO 'root'@'localhost';
FLUSH PRIVILEGES;