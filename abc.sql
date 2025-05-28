-- Create Database
CREATE DATABASE IF NOT EXISTS attendance_system;
USE attendance_system;

-- Table: users
CREATE TABLE users (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    role ENUM('admin','employee') DEFAULT 'employee'
);

-- Insert default admin
INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin');

-- Table: employees
CREATE TABLE employees (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    position VARCHAR(100),
    phone VARCHAR(15),
    username VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: face_encodings
CREATE TABLE face_encodings (
    username VARCHAR(50) NOT NULL PRIMARY KEY,
    encoding_file VARCHAR(255)
);

-- Table: leaves
CREATE TABLE leaves (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100),
    leave_type VARCHAR(50),
    start_date DATE,
    end_date DATE,
    reason TEXT,
    status ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
    INDEX (username)
);

-- Table: locations
CREATE TABLE locations (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    latitude VARCHAR(50),
    longitude VARCHAR(50),
    description TEXT
);

-- Table: attendance_logs
CREATE TABLE attendance_logs (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    date DATE,
    login_time TIME,
    logout_time TIME,
    login_location VARCHAR(100),
    logout_location VARCHAR(100)
);
