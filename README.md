# Phix HRMS - Human Resource Management System

A comprehensive HR management system with authentication, user management, and data import capabilities.

## Features

- ✅ **User Authentication** - Registration, login, and password recovery
- ✅ **Social Login** - Google, Facebook, and Apple ID authentication
- ✅ **JWT Authentication** - Secure token-based authentication
- ✅ **PostgreSQL Database** - Reliable data storage with migrations
- ✅ **Email Integration** - SMTP email for OTP delivery
- ✅ **Data Import** - Import companies, education facilities, and certifications
- ✅ **User Management** - Profile management, skills, roles, and languages
- ✅ **Mobile Optimized** - CORS enabled for mobile apps

## Project Structure

```
Phix-Hrms/
├── app/
│   ├── api/                 # API endpoints
│   ├── models/              # Database models
│   ├── repositories/        # Data access layer
│   ├── schemas/            # Pydantic schemas
│   ├── utils/              # Utility functions
│   ├── config.py           # Configuration settings
│   ├── database.py         # Database connection
│   └── main.py            # FastAPI application
├── alembic/                # Database migrations
├── static/                 # Static files (avatars, flags, projects)
├── test/                   # Test files
├── requirements.txt        # Python dependencies
├── env.example            # Environment variables template
└── README.md              # This file
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp env.example .env
```

Edit `.env` file with your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/phix_hrms

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration for OTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# OTP Configuration
OTP_EXPIRE_MINUTES=5
OTP_LENGTH=6

# Social Login Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FACEBOOK_CLIENT_ID=your-facebook-client-id
FACEBOOK_CLIENT_SECRET=your-facebook-client-secret
APPLE_CLIENT_ID=your-apple-client-id
APPLE_CLIENT_SECRET=your-apple-client-secret
```

### 3. Database Setup

#### Option A: Automatic Setup (Recommended)

```bash
# Create database and run migrations (like Django's migrate)
python setup_database.py
```

This script will:
- Create the database if it doesn't exist
- Run all pending migrations
- Test the database connection

#### Option B: Manual Setup

1. Create PostgreSQL database:
```sql
CREATE DATABASE phix_hrms;
```

2. Run migrations:
```bash
alembic upgrade head
```

#### Database Setup Commands

```bash
# Full setup (create DB + run migrations)
python setup_db.py

# Run migrations only (like Django's migrate)
python setup_db.py migrate

# Create new migration (like Django's makemigrations)
python setup_db.py makemigrations "Add new model"
```

### 4. Run the Application

```bash
# Development
python -m uvicorn app.main:app --reload

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 9000
```

The application will be available at:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Database Management

### Creating New Models

When adding new database models:

1. **Create the model** in `app/models/` directory
2. **Import the model** in `alembic/env.py`:
```python
from app.models.your_model import YourModel
```
3. **Generate migration**:
```bash
alembic revision --autogenerate -m "Add YourModel table"
```
4. **Apply migration**:
```bash
alembic upgrade head
```

### Migration Commands

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1

# Check migration status
alembic current

# View migration history
alembic history
```

### Database Schema

The system includes these main tables:

- **users** - User accounts and authentication
- **otps** - One-time passwords for verification
- **roles** - User roles and permissions
- **skills** - User skills and competencies
- **languages** - Language support
- **locations** - Geographic locations
- **companies** - Company information
- **education_facilities** - Educational institutions
- **certification_centers** - Certification providers
- **projects** - User projects and portfolios
- **experiences** - Work experience records
- **educations** - Educational background
- **certifications** - Professional certifications

## Email Configuration

### Gmail Setup

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Select 'Mail' and 'Other (Custom name)'
   - Enter 'Phix HRMS' as the name
   - Copy the 16-character password
3. **Update .env file** with your App Password

### Testing Email Configuration

```bash
# Test SMTP connection
python -c "
import smtplib
import os
from dotenv import load_dotenv
load_dotenv()

smtp_server = os.getenv('SMTP_SERVER')
smtp_port = int(os.getenv('SMTP_PORT'))
smtp_username = os.getenv('SMTP_USERNAME')
smtp_password = os.getenv('SMTP_PASSWORD')

server = smtplib.SMTP(smtp_server, smtp_port)
server.starttls()
server.login(smtp_username, smtp_password)
server.quit()
"
```

## Data Import

The system supports importing data from JSON files:

- **Companies**: `app/utils/files/it_companies.json`
- **Education Facilities**: `app/utils/files/education_institutions_corrected.json`
- **Certification Centers**: `app/utils/files/it_certifications.json`

Import data using the data management endpoints or run the import script.

## Testing

### Run Tests

```bash
# Run all tests
pytest test/

# Run specific test file
pytest test/test_auth.py
```

### Test Database Connection

```bash
python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:your_password@localhost:5432/your_database')
    conn.close()
except Exception as e:
    pass
"
```

## Security Features

- **Password Hashing** - Bcrypt for secure password storage
- **JWT Tokens** - Secure authentication tokens
- **OTP Expiration** - Time-limited OTP codes
- **Input Validation** - Pydantic schema validation
- **CORS Protection** - Cross-origin resource sharing
- **SQL Injection Protection** - SQLAlchemy ORM

## Production Deployment

### Environment Setup

1. **Environment Variables** - Configure all environment variables
2. **Database** - Use production PostgreSQL instance
3. **Email Service** - Configure SMTP for OTP delivery
4. **Social OAuth** - Set up OAuth apps for each provider
5. **HTTPS** - Enable SSL/TLS encryption
6. **Rate Limiting** - Implement API rate limiting
7. **Monitoring** - Add logging and monitoring

### Nginx Configuration

The project includes an `nginx.conf` file for production deployment with:
- Reverse proxy to FastAPI application
- Static file serving
- SSL/TLS configuration
- Security headers

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running
   - Check database credentials in `.env`
   - Verify database exists

2. **Email Authentication Error**
   - Enable 2-Factor Authentication on Gmail
   - Use App Password instead of regular password
   - Check SMTP settings in `.env`

3. **Migration Errors**
   - Ensure all models are imported in `alembic/env.py`
   - Check for conflicting migrations
   - Verify database is up to date

4. **Import Errors**
   - Check JSON file paths
   - Verify database tables exist
   - Ensure proper permissions

### Reset Database (Development Only)

```bash
# Drop and recreate database
psql -U postgres -h localhost -c "DROP DATABASE IF EXISTS phix_hrms;"
psql -U postgres -h localhost -c "CREATE DATABASE phix_hrms;"

# Run migrations
alembic upgrade head
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for specific error messages
3. Verify all environment variables are correctly set
4. Ensure all dependencies are installed correctly 