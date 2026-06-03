-- PostgreSQL initialization script for Enterprise RAG
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  username VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'engineering', 'hr', 'operations', 'support')),
  departments_allowed TEXT[] NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  doc_name VARCHAR(500) NOT NULL,
  department VARCHAR(100) NOT NULL CHECK (department IN ('engineering', 'hr', 'operations', 'product_support')),
  category VARCHAR(100) NOT NULL CHECK (category IN ('policy', 'guide', 'faq', 'incident', 'release_notes')),
  version VARCHAR(50),
  doc_date DATE,
  file_size_bytes INTEGER,
  page_count INTEGER,
  language VARCHAR(10) DEFAULT 'en',
  chunk_count INTEGER DEFAULT 0,
  fixed_chunk_count INTEGER DEFAULT 0,
  semantic_chunk_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_by UUID REFERENCES users(id)
);

CREATE TABLE feedback (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id VARCHAR(255) NOT NULL,
  user_id UUID REFERENCES users(id),
  query_text TEXT NOT NULL,
  response_text TEXT,
  helpful BOOLEAN,
  comment TEXT,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_sessions (
  id VARCHAR(255) PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP,
  messages_count INTEGER DEFAULT 0,
  feedback_provided BOOLEAN DEFAULT FALSE
);

CREATE TABLE experiment_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  experiment_name VARCHAR(255) NOT NULL,
  experiment_type VARCHAR(50) NOT NULL CHECK (experiment_type IN ('retrieval', 'chunking', 'reranking')),
  query_number INTEGER,
  query_text TEXT NOT NULL,
  expected_department VARCHAR(100),
  expected_doc_type VARCHAR(100),
  retrieval_mode VARCHAR(50) CHECK (retrieval_mode IN ('vector', 'hybrid')),
  chunking_strategy VARCHAR(50) CHECK (chunking_strategy IN ('fixed', 'semantic')),
  answer_text TEXT,
  score INTEGER CHECK (score >= 0 AND score <= 3),
  mrr FLOAT8,
  hit_in_top_k INTEGER,
  execution_time_ms INTEGER,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_department_category ON documents(department, category);
CREATE INDEX idx_feedback_created_at ON feedback(created_at);
CREATE INDEX idx_experiment_results_created_at ON experiment_results(created_at);

-- Seed demo users
INSERT INTO users (username, password_hash, role, departments_allowed) VALUES
  ('admin', 'admin123', 'admin', ARRAY['engineering', 'hr', 'operations', 'product_support']),
  ('alice_hr', 'hr123', 'hr', ARRAY['hr']),
  ('bob_eng', 'eng123', 'engineering', ARRAY['engineering']),
  ('charlie_ops', 'ops123', 'operations', ARRAY['operations']),
  ('diana_support', 'support123', 'support', ARRAY['product_support']);
