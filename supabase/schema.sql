-- Supabase Database Schema for BTEB Results
-- This file contains the SQL commands to create the necessary tables
-- Run these commands in your Supabase SQL editor

-- Enable Row Level Security (RLS) for all tables
-- You can disable this if you don't need RLS

-- 1. Programs table
CREATE TABLE IF NOT EXISTS programs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Regulations table
CREATE TABLE IF NOT EXISTS regulations (
    id SERIAL PRIMARY KEY,
    program_name VARCHAR(255) NOT NULL,
    year VARCHAR(4) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(program_name, year),
    FOREIGN KEY (program_name) REFERENCES programs(name) ON DELETE CASCADE
);

-- 3. Institutes table
CREATE TABLE IF NOT EXISTS institutes (
    id SERIAL PRIMARY KEY,
    program_name VARCHAR(255) NOT NULL,
    regulation_year VARCHAR(4) NOT NULL,
    institute_code VARCHAR(10) NOT NULL,
    name VARCHAR(500) NOT NULL,
    district VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(program_name, regulation_year, institute_code),
    FOREIGN KEY (program_name, regulation_year) REFERENCES regulations(program_name, year) ON DELETE CASCADE
);

-- 4. Students table
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    program_name VARCHAR(255) NOT NULL,
    regulation_year VARCHAR(4) NOT NULL,
    institute_code VARCHAR(10) NOT NULL,
    roll_number VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(program_name, regulation_year, institute_code, roll_number),
    FOREIGN KEY (program_name, regulation_year, institute_code) REFERENCES institutes(program_name, regulation_year, institute_code) ON DELETE CASCADE
);

-- 5. GPA Records table
CREATE TABLE IF NOT EXISTS gpa_records (
    id SERIAL PRIMARY KEY,
    program_name VARCHAR(255) NOT NULL,
    regulation_year VARCHAR(4) NOT NULL,
    institute_code VARCHAR(10) NOT NULL,
    roll_number VARCHAR(20) NOT NULL,
    semester INTEGER NOT NULL CHECK (semester >= 1 AND semester <= 8),
    gpa DECIMAL(3,2) CHECK (gpa >= 0.0 AND gpa <= 4.0),
    is_reference BOOLEAN DEFAULT FALSE,
    ref_subjects TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(program_name, regulation_year, institute_code, roll_number, semester),
    FOREIGN KEY (program_name, regulation_year, institute_code, roll_number) REFERENCES students(program_name, regulation_year, institute_code, roll_number) ON DELETE CASCADE
);

-- 6. CGPA Records table
CREATE TABLE IF NOT EXISTS cgpa_records (
    id SERIAL PRIMARY KEY,
    program_name VARCHAR(255) NOT NULL,
    regulation_year VARCHAR(4) NOT NULL,
    institute_code VARCHAR(10) NOT NULL,
    roll_number VARCHAR(20) NOT NULL,
    cgpa DECIMAL(3,2) NOT NULL CHECK (cgpa >= 0.0 AND cgpa <= 4.0),
    calculated_from VARCHAR(50) DEFAULT 'all_semesters',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(program_name, regulation_year, institute_code, roll_number),
    FOREIGN KEY (program_name, regulation_year, institute_code, roll_number) REFERENCES students(program_name, regulation_year, institute_code, roll_number) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_programs_name ON programs(name);
CREATE INDEX IF NOT EXISTS idx_regulations_program_year ON regulations(program_name, year);
CREATE INDEX IF NOT EXISTS idx_institutes_program_year_code ON institutes(program_name, regulation_year, institute_code);
CREATE INDEX IF NOT EXISTS idx_students_program_year_code_roll ON students(program_name, regulation_year, institute_code, roll_number);
CREATE INDEX IF NOT EXISTS idx_gpa_records_program_year_code_roll_sem ON gpa_records(program_name, regulation_year, institute_code, roll_number, semester);
CREATE INDEX IF NOT EXISTS idx_cgpa_records_program_year_code_roll ON cgpa_records(program_name, regulation_year, institute_code, roll_number);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_gpa_records_roll ON gpa_records(roll_number);
CREATE INDEX IF NOT EXISTS idx_gpa_records_semester ON gpa_records(semester);
CREATE INDEX IF NOT EXISTS idx_students_roll ON students(roll_number);
CREATE INDEX IF NOT EXISTS idx_institutes_code ON institutes(institute_code);

-- Enable Row Level Security (optional - comment out if not needed)
-- ALTER TABLE programs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE regulations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE institutes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE students ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE gpa_records ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE cgpa_records ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust as needed for your security requirements)
-- CREATE POLICY "Allow public read access" ON programs FOR SELECT USING (true);
-- CREATE POLICY "Allow public read access" ON regulations FOR SELECT USING (true);
-- CREATE POLICY "Allow public read access" ON institutes FOR SELECT USING (true);
-- CREATE POLICY "Allow public read access" ON students FOR SELECT USING (true);
-- CREATE POLICY "Allow public read access" ON gpa_records FOR SELECT USING (true);
-- CREATE POLICY "Allow public read access" ON cgpa_records FOR SELECT USING (true);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_programs_updated_at BEFORE UPDATE ON programs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_regulations_updated_at BEFORE UPDATE ON regulations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_institutes_updated_at BEFORE UPDATE ON institutes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_gpa_records_updated_at BEFORE UPDATE ON gpa_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cgpa_records_updated_at BEFORE UPDATE ON cgpa_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create useful views for common queries

-- View: Student GPA Summary
CREATE OR REPLACE VIEW student_gpa_summary AS
SELECT 
    s.program_name,
    s.regulation_year,
    s.institute_code,
    i.name as institute_name,
    i.district,
    s.roll_number,
    COUNT(g.semester) as total_semesters,
    AVG(g.gpa) as average_gpa,
    MAX(g.gpa) as highest_gpa,
    MIN(g.gpa) as lowest_gpa,
    COUNT(CASE WHEN g.is_reference THEN 1 END) as reference_semesters,
    c.cgpa
FROM students s
LEFT JOIN institutes i ON s.program_name = i.program_name 
    AND s.regulation_year = i.regulation_year 
    AND s.institute_code = i.institute_code
LEFT JOIN gpa_records g ON s.program_name = g.program_name 
    AND s.regulation_year = g.regulation_year 
    AND s.institute_code = g.institute_code 
    AND s.roll_number = g.roll_number
LEFT JOIN cgpa_records c ON s.program_name = c.program_name 
    AND s.regulation_year = c.regulation_year 
    AND s.institute_code = c.institute_code 
    AND s.roll_number = c.roll_number
GROUP BY s.program_name, s.regulation_year, s.institute_code, i.name, i.district, s.roll_number, c.cgpa;

-- View: Institute Statistics
CREATE OR REPLACE VIEW institute_statistics AS
SELECT 
    i.program_name,
    i.regulation_year,
    i.institute_code,
    i.name as institute_name,
    i.district,
    COUNT(DISTINCT s.roll_number) as total_students,
    COUNT(DISTINCT g.semester) as total_semesters,
    AVG(g.gpa) as average_gpa,
    COUNT(CASE WHEN g.is_reference THEN 1 END) as total_reference_records,
    COUNT(CASE WHEN g.gpa >= 3.5 THEN 1 END) as high_gpa_count,
    COUNT(CASE WHEN g.gpa < 2.0 THEN 1 END) as low_gpa_count
FROM institutes i
LEFT JOIN students s ON i.program_name = s.program_name 
    AND i.regulation_year = s.regulation_year 
    AND i.institute_code = s.institute_code
LEFT JOIN gpa_records g ON s.program_name = g.program_name 
    AND s.regulation_year = g.regulation_year 
    AND s.institute_code = g.institute_code 
    AND s.roll_number = g.roll_number
GROUP BY i.program_name, i.regulation_year, i.institute_code, i.name, i.district;

-- View: Program Statistics
CREATE OR REPLACE VIEW program_statistics AS
SELECT 
    p.name as program_name,
    COUNT(DISTINCT r.year) as total_regulations,
    COUNT(DISTINCT i.institute_code) as total_institutes,
    COUNT(DISTINCT s.roll_number) as total_students,
    AVG(g.gpa) as average_gpa,
    COUNT(CASE WHEN g.is_reference THEN 1 END) as total_reference_records
FROM programs p
LEFT JOIN regulations r ON p.name = r.program_name
LEFT JOIN institutes i ON r.program_name = i.program_name AND r.year = i.regulation_year
LEFT JOIN students s ON i.program_name = s.program_name 
    AND i.regulation_year = s.regulation_year 
    AND i.institute_code = s.institute_code
LEFT JOIN gpa_records g ON s.program_name = g.program_name 
    AND s.regulation_year = g.regulation_year 
    AND s.institute_code = g.institute_code 
    AND s.roll_number = g.roll_number
GROUP BY p.name;

-- Grant necessary permissions (adjust as needed)
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
-- GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
