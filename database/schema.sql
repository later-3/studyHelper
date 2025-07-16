-- StudyHelper Database Schema
-- PostgreSQL Database Schema for StudyHelper Platform
-- Version: 3.0
-- Created: 2025-01-15
-- Description: Complete database schema supporting multi-role user system, 
--              school management, question management, and submission tracking

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSONB for better JSON performance
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- 1. SCHOOL MANAGEMENT TABLES
-- ============================================================================

-- Schools table
CREATE TABLE schools (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    principal_id VARCHAR(50), -- Will be foreign key to users table
    total_students INTEGER DEFAULT 0,
    total_teachers INTEGER DEFAULT 0,
    total_classes INTEGER DEFAULT 0,
    total_grades INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Grades table
CREATE TABLE grades (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    grade_level INTEGER NOT NULL CHECK (grade_level >= 1 AND grade_level <= 12),
    manager_id VARCHAR(50), -- Will be foreign key to users table
    school_id VARCHAR(50) NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    total_classes INTEGER DEFAULT 0,
    total_students INTEGER DEFAULT 0,
    total_teachers INTEGER DEFAULT 0,
    average_accuracy DECIMAL(5,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(school_id, grade_level)
);

-- Classes table
CREATE TABLE classes (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    grade_id VARCHAR(50) NOT NULL REFERENCES grades(id) ON DELETE CASCADE,
    teacher_id VARCHAR(50), -- Will be foreign key to users table
    school_id VARCHAR(50) NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_count INTEGER DEFAULT 0,
    average_accuracy DECIMAL(5,2) DEFAULT 0.00,
    subject_performance JSONB, -- Store subject performance data
    needs_attention_students JSONB, -- Array of student IDs needing attention
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(school_id, grade_id, name)
);

-- ============================================================================
-- 2. USER MANAGEMENT TABLES
-- ============================================================================

-- Users table (unified table for all user types)
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'teacher', 'grade_manager', 'principal', 'admin')),
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(100) NOT NULL,
    
    -- Role-specific fields
    school_id VARCHAR(50) REFERENCES schools(id) ON DELETE CASCADE,
    grade_id VARCHAR(50) REFERENCES grades(id) ON DELETE CASCADE,
    class_id VARCHAR(50) REFERENCES classes(id) ON DELETE CASCADE,
    
    -- Student-specific fields
    student_number VARCHAR(20),
    gender VARCHAR(10) CHECK (gender IN ('男', '女', '其他')),
    birth_date DATE,
    parent_phone VARCHAR(20),
    
    -- Teacher-specific fields
    subject_teach JSONB, -- Array of subjects taught
    manages_classes JSONB, -- Array of class IDs managed
    
    -- Common fields
    permissions JSONB, -- Array of permission strings
    learning_stats JSONB, -- Student learning statistics
    last_login TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User sessions table for JWT token management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. QUESTION MANAGEMENT TABLES
-- ============================================================================

-- Questions table (canonical questions)
CREATE TABLE questions (
    id VARCHAR(100) PRIMARY KEY, -- SHA256 hash of canonical text
    canonical_text TEXT NOT NULL,
    subject VARCHAR(50) NOT NULL,
    difficulty_level INTEGER CHECK (difficulty_level >= 1 AND difficulty_level <= 5),
    knowledge_points JSONB, -- Array of knowledge points
    tags JSONB, -- Array of tags
    first_submission_image TEXT,
    first_seen_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_submissions INTEGER DEFAULT 0,
    correct_submissions INTEGER DEFAULT 0,
    accuracy_rate DECIMAL(5,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'flagged')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Question analysis table (master analysis for each question)
CREATE TABLE question_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id VARCHAR(100) NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    subject VARCHAR(50) NOT NULL,
    is_correct BOOLEAN,
    error_analysis TEXT,
    correct_answer TEXT,
    solution_steps TEXT,
    knowledge_point TEXT,
    common_mistakes TEXT,
    difficulty_assessment INTEGER CHECK (difficulty_assessment >= 1 AND difficulty_assessment <= 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id)
);

-- Question images table (for perceptual hashing)
CREATE TABLE question_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id VARCHAR(100) NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    image_path TEXT NOT NULL,
    perceptual_hash VARCHAR(16) NOT NULL,
    file_size INTEGER,
    image_dimensions JSONB, -- {width: int, height: int}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(perceptual_hash)
);

-- ============================================================================
-- 4. SUBMISSION MANAGEMENT TABLES
-- ============================================================================

-- Submissions table
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id VARCHAR(100) REFERENCES questions(id) ON DELETE SET NULL,
    submitted_ocr_text TEXT,
    image_path TEXT,
    subject VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Submission analysis table
CREATE TABLE submission_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    subject VARCHAR(50) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    error_analysis TEXT,
    correct_answer TEXT,
    solution_steps TEXT,
    knowledge_point TEXT,
    common_mistakes TEXT,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0.00 AND confidence_score <= 1.00),
    processing_time_ms INTEGER,
    ai_model_used VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(submission_id)
);

-- ============================================================================
-- 5. MISTAKE BOOK TABLES
-- ============================================================================

-- Mistake book entries table
CREATE TABLE mistake_book_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    submission_id UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    question_id VARCHAR(100) REFERENCES questions(id) ON DELETE SET NULL,
    subject VARCHAR(50) NOT NULL,
    knowledge_point TEXT,
    error_type VARCHAR(100),
    difficulty_level INTEGER CHECK (difficulty_level >= 1 AND difficulty_level <= 5),
    review_count INTEGER DEFAULT 0,
    last_reviewed_at TIMESTAMP WITH TIME ZONE,
    mastery_level INTEGER DEFAULT 1 CHECK (mastery_level >= 1 AND mastery_level <= 5),
    notes TEXT,
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 6. VECTOR DATABASE TABLES (for semantic search)
-- ============================================================================

-- Question embeddings table
CREATE TABLE question_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id VARCHAR(100) NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    embedding_vector REAL[], -- Store the actual embedding vector
    embedding_model VARCHAR(100) NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, embedding_model)
);

-- ============================================================================
-- 7. ANALYTICS AND REPORTING TABLES
-- ============================================================================

-- User learning analytics table
CREATE TABLE user_learning_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_submissions INTEGER DEFAULT 0,
    correct_submissions INTEGER DEFAULT 0,
    accuracy_rate DECIMAL(5,2) DEFAULT 0.00,
    subjects_covered JSONB, -- {subject: count}
    knowledge_points_covered JSONB, -- {knowledge_point: count}
    study_time_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Class performance analytics table
CREATE TABLE class_performance_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id VARCHAR(50) NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_submissions INTEGER DEFAULT 0,
    correct_submissions INTEGER DEFAULT 0,
    accuracy_rate DECIMAL(5,2) DEFAULT 0.00,
    subject_performance JSONB, -- {subject: {total: int, correct: int, accuracy: decimal}}
    top_mistakes JSONB, -- Array of most common mistakes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_id, date)
);

-- ============================================================================
-- 8. INDEXES FOR PERFORMANCE
-- ============================================================================

-- Users table indexes
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_school_id ON users(school_id);
CREATE INDEX idx_users_grade_id ON users(grade_id);
CREATE INDEX idx_users_class_id ON users(class_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);

-- User sessions indexes
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_is_active ON user_sessions(is_active);

-- Questions table indexes
CREATE INDEX idx_questions_subject ON questions(subject);
CREATE INDEX idx_questions_difficulty_level ON questions(difficulty_level);
CREATE INDEX idx_questions_accuracy_rate ON questions(accuracy_rate);
CREATE INDEX idx_questions_status ON questions(status);
CREATE INDEX idx_questions_canonical_text_gin ON questions USING gin(to_tsvector('chinese', canonical_text));

-- Question images indexes
CREATE INDEX idx_question_images_question_id ON question_images(question_id);
CREATE INDEX idx_question_images_perceptual_hash ON question_images(perceptual_hash);

-- Submissions table indexes
CREATE INDEX idx_submissions_user_id ON submissions(user_id);
CREATE INDEX idx_submissions_question_id ON submissions(question_id);
CREATE INDEX idx_submissions_timestamp ON submissions(timestamp);
CREATE INDEX idx_submissions_subject ON submissions(subject);
CREATE INDEX idx_submissions_processing_status ON submissions(processing_status);

-- Submission analyses indexes
CREATE INDEX idx_submission_analyses_submission_id ON submission_analyses(submission_id);
CREATE INDEX idx_submission_analyses_is_correct ON submission_analyses(is_correct);
CREATE INDEX idx_submission_analyses_subject ON submission_analyses(subject);

-- Mistake book indexes
CREATE INDEX idx_mistake_book_entries_user_id ON mistake_book_entries(user_id);
CREATE INDEX idx_mistake_book_entries_subject ON mistake_book_entries(subject);
CREATE INDEX idx_mistake_book_entries_knowledge_point ON mistake_book_entries(knowledge_point);
CREATE INDEX idx_mistake_book_entries_mastery_level ON mistake_book_entries(mastery_level);

-- Analytics indexes
CREATE INDEX idx_user_learning_analytics_user_id_date ON user_learning_analytics(user_id, date);
CREATE INDEX idx_class_performance_analytics_class_id_date ON class_performance_analytics(class_id, date);

-- ============================================================================
-- 9. TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to all tables with updated_at column
CREATE TRIGGER update_schools_updated_at BEFORE UPDATE ON schools FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_grades_updated_at BEFORE UPDATE ON grades FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_classes_updated_at BEFORE UPDATE ON classes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_sessions_updated_at BEFORE UPDATE ON user_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_questions_updated_at BEFORE UPDATE ON questions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_question_analyses_updated_at BEFORE UPDATE ON question_analyses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mistake_book_entries_updated_at BEFORE UPDATE ON mistake_book_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_learning_analytics_updated_at BEFORE UPDATE ON user_learning_analytics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_class_performance_analytics_updated_at BEFORE UPDATE ON class_performance_analytics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 10. VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for user statistics
CREATE VIEW user_statistics AS
SELECT 
    u.id,
    u.name,
    u.role,
    u.school_id,
    u.grade_id,
    u.class_id,
    COUNT(s.id) as total_submissions,
    COUNT(sa.id) as analyzed_submissions,
    COUNT(CASE WHEN sa.is_correct = true THEN 1 END) as correct_submissions,
    CASE 
        WHEN COUNT(sa.id) > 0 THEN 
            ROUND(COUNT(CASE WHEN sa.is_correct = true THEN 1 END)::DECIMAL / COUNT(sa.id) * 100, 2)
        ELSE 0 
    END as accuracy_rate
FROM users u
LEFT JOIN submissions s ON u.id = s.user_id
LEFT JOIN submission_analyses sa ON s.id = sa.submission_id
GROUP BY u.id, u.name, u.role, u.school_id, u.grade_id, u.class_id;

-- View for question statistics
CREATE VIEW question_statistics AS
SELECT 
    q.id,
    q.canonical_text,
    q.subject,
    q.difficulty_level,
    COUNT(s.id) as total_submissions,
    COUNT(sa.id) as analyzed_submissions,
    COUNT(CASE WHEN sa.is_correct = true THEN 1 END) as correct_submissions,
    CASE 
        WHEN COUNT(sa.id) > 0 THEN 
            ROUND(COUNT(CASE WHEN sa.is_correct = true THEN 1 END)::DECIMAL / COUNT(sa.id) * 100, 2)
        ELSE 0 
    END as accuracy_rate
FROM questions q
LEFT JOIN submissions s ON q.id = s.question_id
LEFT JOIN submission_analyses sa ON s.id = sa.submission_id
GROUP BY q.id, q.canonical_text, q.subject, q.difficulty_level;

-- View for class performance
CREATE VIEW class_performance AS
SELECT 
    c.id as class_id,
    c.name as class_name,
    g.name as grade_name,
    s.name as school_name,
    COUNT(DISTINCT u.id) as student_count,
    COUNT(sb.id) as total_submissions,
    COUNT(sa.id) as analyzed_submissions,
    COUNT(CASE WHEN sa.is_correct = true THEN 1 END) as correct_submissions,
    CASE 
        WHEN COUNT(sa.id) > 0 THEN 
            ROUND(COUNT(CASE WHEN sa.is_correct = true THEN 1 END)::DECIMAL / COUNT(sa.id) * 100, 2)
        ELSE 0 
    END as accuracy_rate
FROM classes c
JOIN grades g ON c.grade_id = g.id
JOIN schools s ON c.school_id = s.id
LEFT JOIN users u ON c.id = u.class_id AND u.role = 'student'
LEFT JOIN submissions sb ON u.id = sb.user_id
LEFT JOIN submission_analyses sa ON sb.id = sa.submission_id
GROUP BY c.id, c.name, g.name, s.name;

-- ============================================================================
-- 11. COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE schools IS 'Schools information table';
COMMENT ON TABLE grades IS 'Grade levels within schools';
COMMENT ON TABLE classes IS 'Classes within grades';
COMMENT ON TABLE users IS 'Unified users table for all user types (students, teachers, managers, principals)';
COMMENT ON TABLE user_sessions IS 'User session management for JWT tokens';
COMMENT ON TABLE questions IS 'Canonical questions identified by content hash';
COMMENT ON TABLE question_analyses IS 'Master analysis for each question';
COMMENT ON TABLE question_images IS 'Question images with perceptual hashing for duplicate detection';
COMMENT ON TABLE submissions IS 'User submissions of questions';
COMMENT ON TABLE submission_analyses IS 'AI analysis results for each submission';
COMMENT ON TABLE mistake_book_entries IS 'Automatically generated mistake book entries';
COMMENT ON TABLE question_embeddings IS 'Vector embeddings for semantic search';
COMMENT ON TABLE user_learning_analytics IS 'Daily learning analytics for users';
COMMENT ON TABLE class_performance_analytics IS 'Daily performance analytics for classes';

-- ============================================================================
-- 12. SAMPLE DATA INSERTION (Optional - for testing)
-- ============================================================================

-- Insert sample school
INSERT INTO schools (id, name, address, phone, email, total_students, total_teachers, total_classes, total_grades) 
VALUES ('school_01', '智慧未来实验小学', '北京市朝阳区智慧路123号', '010-12345678', 'info@zhihui.edu.cn', 6, 3, 3, 2);

-- Insert sample grades
INSERT INTO grades (id, name, grade_level, school_id, total_classes, total_students, total_teachers, average_accuracy) 
VALUES 
('grade_05', '五年级', 5, 'school_01', 2, 62, 2, 78.5),
('grade_06', '六年级', 6, 'school_01', 1, 28, 1, 76.2);

-- Insert sample classes
INSERT INTO classes (id, name, grade_id, school_id, student_count, average_accuracy, subject_performance, needs_attention_students) 
VALUES 
('class_01', '五年级一班', 'grade_05', 'school_01', 32, 82.0, '{"数学": {"average": 85.0, "weak_points": ["分数计算"]}, "语文": {"average": 88.0, "weak_points": []}, "英语": {"average": 75.0, "weak_points": ["语法"]}}', '["student_08", "student_12"]'),
('class_02', '五年级二班', 'grade_05', 'school_01', 30, 75.0, '{"数学": {"average": 78.0, "weak_points": ["几何"]}, "语文": {"average": 82.0, "weak_points": ["阅读理解"]}, "英语": {"average": 70.0, "weak_points": ["词汇", "语法"]}}', '["student_15", "student_18", "student_22"]'),
('class_03', '六年级一班', 'grade_06', 'school_01', 28, 76.2, '{"数学": {"average": 80.0, "weak_points": ["应用题"]}, "语文": {"average": 85.0, "weak_points": ["作文"]}, "英语": {"average": 72.0, "weak_points": ["听力"]}}', '["student_25", "student_28"]'); 