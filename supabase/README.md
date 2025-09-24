# BTEB Results PDF to Supabase Transfer Tool

This tool transfers BTEB (Bangladesh Technical Education Board) results from PDF files to a Supabase database with a hierarchical structure: `program → regulation → institute → student → gpa_records`.

## 🚀 Quick Start

### Option 1: Direct PostgreSQL Connection (Recommended)

1. **Setup Database Schema**
   - Go to your Supabase dashboard → SQL Editor
   - Run the SQL commands from `schema.sql` to create the necessary tables

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variable**
   ```bash
   export POSTGRES_PASSWORD="your-postgres-password"
   ```

4. **Run Setup Script**
   ```bash
   python setup.py
   ```

5. **Run the Tool**
   ```bash
   python postgresql.py
   ```

### Option 2: Supabase Client (Alternative)

1. **Setup Supabase Database**
   - Create a new Supabase project at [supabase.com](https://supabase.com)
   - Go to the SQL Editor in your Supabase dashboard
   - Run the SQL commands from `schema.sql` to create the necessary tables

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**
   ```bash
   export SUPABASE_URL="your-supabase-project-url"
   export SUPABASE_KEY="your-supabase-anon-key"
   ```

4. **Run the Tool**
   ```bash
   python supabase.py
   ```

## 📊 Database Structure

The tool creates the following hierarchical structure:

```
programs
├── regulations
    ├── institutes
        ├── students
            ├── gpa_records (semester-wise GPA data)
            └── cgpa_records (overall CGPA)
```

### Tables Created:

1. **programs** - Stores program information (e.g., "Diploma in Engineering")
2. **regulations** - Stores regulation years for each program
3. **institutes** - Stores institute information (code, name, district)
4. **students** - Stores student information (roll number)
5. **gpa_records** - Stores semester-wise GPA data
6. **cgpa_records** - Stores overall CGPA data

## 🔧 Features

- **Hierarchical Data Structure**: Maintains proper relationships between programs, regulations, institutes, and students
- **Batch Processing**: Efficiently processes large PDF files with batch operations
- **GPA Validation**: Validates GPA values (0.0-4.0 range)
- **Reference Subject Support**: Handles students with "REF" status and their reference subjects
- **Duplicate Prevention**: Uses upsert operations to prevent duplicate data
- **Progress Tracking**: Shows real-time progress during data transfer
- **Error Handling**: Comprehensive error handling with retry mechanisms

## 📋 Usage Example

```python
from supabase import supabase

# Initialize (done automatically when importing)
# supabase = initialize_supabase()

# Transfer PDF data
success = transfer_pdf_to_supabase(
    pdf_path="4th2022.pdf",
    program="Diploma in Engineering", 
    regulation="2022"
)
```

## 🔍 Query Examples

### Get all students for a specific institute:
```sql
SELECT s.*, i.name as institute_name 
FROM students s 
JOIN institutes i ON s.institute_code = i.institute_code 
WHERE i.institute_code = '13085';
```

### Get GPA summary for a student:
```sql
SELECT roll_number, semester, gpa, is_reference, ref_subjects 
FROM gpa_records 
WHERE roll_number = '702521' 
ORDER BY semester;
```

### Get institute statistics:
```sql
SELECT * FROM institute_statistics 
WHERE institute_code = '13085';
```

## 🛠️ Configuration

### Environment Variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anonymous key

### Batch Size:
- Default batch size: 1000 operations
- Adjustable in `batch_write_to_supabase()` function

## 📈 Performance

- **Batch Processing**: Processes up to 1000 operations per batch
- **Upsert Operations**: Prevents duplicate data and handles updates efficiently
- **Indexed Queries**: Database includes optimized indexes for common queries
- **Progress Tracking**: Real-time progress updates during transfer

## 🔒 Security

- **Row Level Security**: Optional RLS policies (commented out by default)
- **Foreign Key Constraints**: Maintains data integrity
- **Input Validation**: Validates GPA ranges and data formats

## 🐛 Troubleshooting

### Common Issues:

1. **Supabase Connection Error**: Check your URL and API key
2. **PDF Parse Error**: Ensure PDF format matches expected BTEB format
3. **Batch Write Error**: Check database permissions and connection stability
4. **Memory Issues**: Reduce batch size for very large PDFs

### Debug Mode:
Enable debug mode by setting `debug=True` in `parse_pdf_results()`:

```python
institutes = parse_pdf_results(pdf_path, debug=True)
```

## 📝 Notes

- The tool maintains the original hierarchical structure as requested
- All foreign key relationships are properly maintained
- The database includes useful views for common queries
- Automatic timestamp tracking with `created_at` and `updated_at` fields
- Support for up to 8 semesters per student

## 🤝 Contributing

Feel free to submit issues and enhancement requests!
