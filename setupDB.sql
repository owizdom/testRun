-- setupDB.sql
-- Creates the student_db database and required tables for EduEnroll
DROP DATABASE IF EXISTS student_db;
CREATE DATABASE student_db;
USE student_db;

CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

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

-- Insert default admin user
INSERT INTO admins (username, password_hash) VALUES ('Apple', 'BatmanGokuSuper@12');

-- Note: After running this script, grant privileges to your MySQL user:
-- GRANT ALL PRIVILEGES ON student_db.* TO 'your_username'@'localhost' IDENTIFIED BY 'your_password';
-- FLUSH PRIVILEGES;