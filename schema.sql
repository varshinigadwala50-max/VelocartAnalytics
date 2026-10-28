-- ============================================================
-- VeloCart Analytics — Database Schema
-- Compatible with: MySQL 8+, PostgreSQL 14+, SQLite 3
-- Run this file in your database tool (phpMyAdmin, DBeaver,
-- SQLite CLI, or MySQL Workbench) before using a real backend.
-- ============================================================

-- ---------- Business Managers (founders, sales, ops) ----------
CREATE TABLE IF NOT EXISTS business_users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,  -- SERIAL for PostgreSQL / INT AUTO_INCREMENT for MySQL
  username      VARCHAR(50)  NOT NULL UNIQUE,
  email         VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,              -- store hashed passwords in production
  company_name  VARCHAR(150) NOT NULL,
  location      VARCHAR(150) NOT NULL,
  job_title     VARCHAR(100) DEFAULT 'Manager',
  phone         VARCHAR(30),
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login    TIMESTAMP NULL
);

-- ---------- Customers / company visitors ----------
CREATE TABLE IF NOT EXISTS customer_users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      VARCHAR(50)  NOT NULL UNIQUE,
  email         VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  brand         VARCHAR(100) NOT NULL,              -- brand they care about / follow
  product       VARCHAR(150) NOT NULL,              -- product interest
  location      VARCHAR(150) NOT NULL,
  phone         VARCHAR(30)  NOT NULL,
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login    TIMESTAMP NULL
);

-- ---------- Sessions (optional server-side) ----------
CREATE TABLE IF NOT EXISTS sessions (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id       INTEGER NOT NULL,
  user_type     VARCHAR(20) NOT NULL CHECK (user_type IN ('business', 'customer')),
  token         VARCHAR(64) NOT NULL UNIQUE,
  expires_at    TIMESTAMP NOT NULL,
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Products (for analytics + customer deals) ----------
CREATE TABLE IF NOT EXISTS products (
  id            VARCHAR(20) PRIMARY KEY,
  name          VARCHAR(150) NOT NULL,
  category      VARCHAR(80)  NOT NULL,
  price         DECIMAL(10,2) NOT NULL,
  stock         INTEGER NOT NULL DEFAULT 0,
  sold          INTEGER NOT NULL DEFAULT 0,
  image_url     VARCHAR(255),
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Discount requests (customer → company) ----------
CREATE TABLE IF NOT EXISTS discount_requests (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id   INTEGER NOT NULL,
  product_id    VARCHAR(20) NOT NULL,
  percent       INTEGER NOT NULL CHECK (percent BETWEEN 5 AND 50),
  message       TEXT NOT NULL,
  status        VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customer_users(id),
  FOREIGN KEY (product_id)  REFERENCES products(id)
);

-- ---------- Indexes ----------
CREATE INDEX IF NOT EXISTS idx_business_email ON business_users(email);
CREATE INDEX IF NOT EXISTS idx_customer_email ON customer_users(email);
CREATE INDEX IF NOT EXISTS idx_requests_status ON discount_requests(status);

-- ---------- Sample business user (password: admin123 — plain for demo only) ----------
-- INSERT INTO business_users (username, email, password_hash, company_name, location, job_title, phone)
-- VALUES ('admin', 'admin@velocart.com', 'admin123', 'VeloCart Inc', 'San Francisco, CA', 'Founder', '+1-555-0100');
