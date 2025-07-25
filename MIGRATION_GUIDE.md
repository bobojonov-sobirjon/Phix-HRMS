# Database Migration Guide for Phix HRMS

This guide will help you set up the PostgreSQL database and run migrations for the Phix HRMS authentication system.

## Prerequisites

1. **PostgreSQL** must be installed and running
2. **Python dependencies** must be installed
3. **Environment variables** must be configured

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

Create a `.env` file in the root directory with your database credentials:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:0576@localhost:5432/phix_hrms

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

## Step 3: Database Setup

### Option A: Automatic Setup (Recommended)

Run the database setup script:

```bash
python setup_database.py
```

This script will:
- Create the `phix_hrms` database if it doesn't exist
- Run all migrations automatically

### Option B: Manual Setup

#### 3.1 Create Database

Connect to PostgreSQL and create the database:

```sql
CREATE DATABASE phix_hrms;
```

#### 3.2 Initialize Alembic

```bash
alembic init alembic
```

#### 3.3 Create Initial Migration

```bash
alembic revision --autogenerate -m "Initial migration"
```

#### 3.4 Run Migrations

```bash
alembic upgrade head
```

## Step 4: Verify Database Setup

Check that the tables were created:

```sql
\c phix_hrms
\dt
```

You should see:
- `users` table
- `otps` table
- `alembic_version` table

## Step 5: Test the Application

Run the FastAPI application:

```bash
python -m uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` to see the API documentation.

## Migration Commands Reference

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migrations
```bash
alembic downgrade -1
```

### Check migration status
```bash
alembic current
```

### View migration history
```bash
alembic history
```

## Troubleshooting

### Common Issues

1. **Connection Error**: Make sure PostgreSQL is running
   ```bash
   # Windows
   net start postgresql-x64-15
   
   # Linux/Mac
   sudo systemctl start postgresql
   ```

2. **Permission Error**: Check your PostgreSQL credentials
   ```sql
   -- Connect as postgres user
   psql -U postgres -h localhost
   ```

3. **Database Already Exists**: The setup script will handle this automatically

4. **Migration Errors**: Check the Alembic logs for specific error messages

### Reset Database (Development Only)

If you need to start fresh:

```bash
# Drop and recreate database
psql -U postgres -h localhost -c "DROP DATABASE IF EXISTS phix_hrms;"
psql -U postgres -h localhost -c "CREATE DATABASE phix_hrms;"

# Run migrations
alembic upgrade head
```

## Database Schema

After successful migration, you'll have these tables:

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    google_id VARCHAR(255) UNIQUE,
    facebook_id VARCHAR(255) UNIQUE,
    apple_id VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE
);
```

### OTPs Table
```sql
CREATE TABLE otps (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

## Next Steps

After successful database setup:

1. **Test the API endpoints** using the Swagger UI at `http://localhost:8000/docs`
2. **Configure email settings** for OTP functionality
3. **Set up social OAuth** applications for Google, Facebook, and Apple
4. **Deploy to production** with proper security configurations

## Support

If you encounter any issues:

1. Check the logs for specific error messages
2. Verify PostgreSQL is running and accessible
3. Ensure all environment variables are correctly set
4. Check that all dependencies are installed correctly 