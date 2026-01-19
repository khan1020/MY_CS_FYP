-- Enhanced RAG System - Database Migration
-- Run this script to add new tables and columns for advanced features
-- Compatible with MySQL/MariaDB

-- Drop the migration if tables already exist (for clean re-run)
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;

-- 1. Create document_chunks table if it doesn't exist
CREATE TABLE IF NOT EXISTS document_chunks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  file_id INT,
  chunk_text TEXT,
  page_number INT DEFAULT NULL,
  section_title VARCHAR(255) DEFAULT NULL,
  chunk_index INT DEFAULT 0,
  metadata JSON DEFAULT NULL,
  word_count INT DEFAULT 0,
  keywords JSON DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (file_id) REFERENCES user_files(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_page_number ON document_chunks(file_id, page_number);
CREATE FULLTEXT INDEX IF NOT EXISTS idx_chunk_text ON document_chunks(chunk_text);

-- 2. Create document_keywords table for keyword tracking
CREATE TABLE IF NOT EXISTS document_keywords (
  id INT AUTO_INCREMENT PRIMARY KEY,
  file_id INT NOT NULL,
  keyword VARCHAR(255) NOT NULL,
  frequency INT DEFAULT 0,
  page_numbers JSON DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (file_id) REFERENCES user_files(id) ON DELETE CASCADE,
  INDEX idx_keyword (file_id, keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Create query_history table for query re-execution
CREATE TABLE IF NOT EXISTS query_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  query_text TEXT NOT NULL,
  response_text TEXT,
  context_used JSON DEFAULT NULL,
  tools_used JSON DEFAULT NULL,
  intent VARCHAR(50) DEFAULT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  execution_time_ms INT DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user_timestamp (user_id, timestamp DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Create query_reruns table for tracking re-executions
CREATE TABLE IF NOT EXISTS query_reruns (
  id INT AUTO_INCREMENT PRIMARY KEY,
  original_query_id INT NOT NULL,
  rerun_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  new_response TEXT,
  differences TEXT,
  context_changes JSON DEFAULT NULL,
  FOREIGN KEY (original_query_id) REFERENCES query_history(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Create bookmarks table
CREATE TABLE IF NOT EXISTS bookmarks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  message_id INT NOT NULL,
  title VARCHAR(255) DEFAULT NULL,
  tags JSON DEFAULT NULL,
  notes TEXT DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
  INDEX idx_user_created (user_id, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Create bookmark_collections table
CREATE TABLE IF NOT EXISTS bookmark_collections (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT DEFAULT NULL,
  bookmark_ids JSON DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Create prompt_templates table
CREATE TABLE IF NOT EXISTS prompt_templates (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT DEFAULT NULL,  -- NULL for system templates
  name VARCHAR(255) NOT NULL,
  description TEXT DEFAULT NULL,
  template_text TEXT NOT NULL,
  category VARCHAR(100) DEFAULT 'general',
  variables JSON DEFAULT NULL,
  is_public BOOLEAN DEFAULT FALSE,
  usage_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_category (category),
  INDEX idx_public (is_public)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Create template_usage table  
CREATE TABLE IF NOT EXISTS template_usage (
  id INT AUTO_INCREMENT PRIMARY KEY,
  template_id INT NOT NULL,
  user_id INT NOT NULL,
  executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (template_id) REFERENCES prompt_templates(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Create message_branches table for conversation branching
CREATE TABLE IF NOT EXISTS message_branches (
  id INT AUTO_INCREMENT PRIMARY KEY,
  chat_id INT NOT NULL,
  message_id INT NOT NULL,
  parent_message_id INT DEFAULT NULL,  -- NULL for root messages
  branch_name VARCHAR(255) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE,
  FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
  FOREIGN KEY (parent_message_id) REFERENCES messages(id) ON DELETE SET NULL,
  INDEX idx_chat_parent (chat_id, parent_message_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Create branch_metadata table
CREATE TABLE IF NOT EXISTS branch_metadata (
  branch_id INT PRIMARY KEY,
  tool_configuration JSON DEFAULT NULL,
  quality_score FLOAT DEFAULT NULL,
  user_preference ENUM('preferred', 'neutral', 'rejected') DEFAULT 'neutral',
  FOREIGN KEY (branch_id) REFERENCES message_branches(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert default prompt templates
INSERT INTO prompt_templates (user_id, name, description, template_text, category, variables)
SELECT * FROM (SELECT 
  NULL as user_id,
  'Summarize Document' as name,
  'Summarize key findings and conclusions' as description,
  'Summarize the key findings, methodology, and conclusions from {document}. Focus on practical implications.' as template_text,
  'research' as category,
  '["document"]' as variables
) AS tmp
WHERE NOT EXISTS (
  SELECT 1 FROM prompt_templates WHERE name = 'Summarize Document'
) LIMIT 1;

INSERT INTO prompt_templates (user_id, name, description, template_text, category, variables)
SELECT * FROM (SELECT 
  NULL, 'Extract Findings', 'Extract all key findings with page references',
  'Extract all key findings from {document}. List them as bullet points with page references.',
  'research', '["document"]'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE name = 'Extract Findings') LIMIT 1;

INSERT INTO prompt_templates (user_id, name, description, template_text, category, variables)
SELECT * FROM (SELECT 
  NULL, 'Compare Methodologies', 'Compare research methods between documents',
  'Compare the methodologies between {document1} and {document2}. Highlight similarities and differences.',
  'research', '["document1", "document2"]'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE name = 'Compare Methodologies') LIMIT 1;

INSERT INTO prompt_templates (user_id, name, description, template_text, category, variables)
SELECT * FROM (SELECT 
  NULL, 'Legal Analysis', 'Analyze legal implications',
  'Analyze the legal implications of {section} in {document}. Cite relevant case law if available.',
  'law', '["section", "document"]'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE name = 'Legal Analysis') LIMIT 1;

INSERT INTO prompt_templates (user_id, name, description, template_text, category, variables)
SELECT * FROM (SELECT 
  NULL, 'Extract Keywords', 'Extract top keywords from document',
  'Extract the top 20 most important keywords from {document} and explain their significance.',
  'general', '["document"]'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE name = 'Extract Keywords') LIMIT 1;

INSERT INTO prompt_templates (user_id, name, description, template_text, category, variables)
SELECT * FROM (SELECT 
  NULL, 'Section Summary', 'Summarize specific section',
  'Provide a detailed summary of the {section} section in {document}.',
  'general', '["section", "document"]'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM prompt_templates WHERE name = 'Section Summary') LIMIT 1;

SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;

-- Migration complete
SELECT 'Database migration completed successfully!' AS status,
       'All tables created and default templates inserted' AS message;
