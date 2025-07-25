# Phix HRMS Authentication API

Complete mobile authentication system with login, register, social login (Google, Facebook, Apple), and password recovery with OTP verification.

## Features

- ✅ **User Registration** - Email and password registration
- ✅ **User Login** - Email and password authentication
- ✅ **Social Login** - Google, Facebook, and Apple ID authentication
- ✅ **Password Reset** - OTP verification via email
- ✅ **JWT Authentication** - Secure token-based authentication
- ✅ **PostgreSQL Database** - Reliable data storage
- ✅ **Mobile Optimized** - CORS enabled for mobile apps
- ✅ **Email Integration** - SMTP email for OTP delivery

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login with email/password |
| POST | `/api/v1/auth/social-login` | Login with social provider |
| POST | `/api/v1/auth/forgot-password` | Send OTP for password reset |
| POST | `/api/v1/auth/verify-otp` | Verify OTP code |
| POST | `/api/v1/auth/reset-password` | Reset password with OTP |
| GET | `/api/v1/auth/me` | Get current user info |

## Setup Instructions

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

Create PostgreSQL database:

```sql
CREATE DATABASE phix_hrms;
```

### 4. Run the Application

```bash
# Development
python -m uvicorn app.main:app --reload

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Usage Examples

### 1. User Registration

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ahmed Khaled",
    "email": "ahmeduiux206@gmail.com",
    "password": "password123"
  }'
```

### 2. User Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ahmeduiux206@gmail.com",
    "password": "password123"
  }'
```

### 3. Social Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/social-login" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "access_token": "google-access-token"
  }'
```

### 4. Forgot Password

```bash
curl -X POST "http://localhost:8000/api/v1/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ahmeduiux206@gmail.com"
  }'
```

### 5. Verify OTP

```bash
curl -X POST "http://localhost:8000/api/v1/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ahmeduiux206@gmail.com",
    "otp_code": "123456"
  }'
```

### 6. Reset Password

```bash
curl -X POST "http://localhost:8000/api/v1/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ahmeduiux206@gmail.com",
    "otp_code": "123456",
    "new_password": "newpassword123"
  }'
```

### 7. Get Current User

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Mobile App Integration

### React Native Example

```javascript
// Login function
const login = async (email, password) => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        password: password,
      }),
    });
    
    const data = await response.json();
    // Store token in secure storage
    await SecureStore.setItemAsync('token', data.token.access_token);
    return data;
  } catch (error) {
    console.error('Login error:', error);
  }
};

// Social login function
const socialLogin = async (provider, accessToken) => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/auth/social-login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        provider: provider, // 'google', 'facebook', 'apple'
        access_token: accessToken,
      }),
    });
    
    const data = await response.json();
    await SecureStore.setItemAsync('token', data.token.access_token);
    return data;
  } catch (error) {
    console.error('Social login error:', error);
  }
};
```

## Database Schema

### Users Table
- `id` - Primary key
- `name` - User's full name
- `email` - Unique email address
- `password_hash` - Hashed password (nullable for social users)
- `google_id` - Google OAuth ID
- `facebook_id` - Facebook OAuth ID
- `apple_id` - Apple OAuth ID
- `phone` - Phone number
- `avatar_url` - Profile picture URL
- `is_active` - Account status
- `is_verified` - Email verification status
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp
- `last_login` - Last login timestamp

### OTPs Table
- `id` - Primary key
- `email` - Email address
- `otp_code` - OTP code
- `is_used` - Usage status
- `created_at` - Creation timestamp
- `expires_at` - Expiration timestamp

## Security Features

- **Password Hashing** - Bcrypt for secure password storage
- **JWT Tokens** - Secure authentication tokens
- **OTP Expiration** - Time-limited OTP codes
- **Input Validation** - Pydantic schema validation
- **CORS Protection** - Cross-origin resource sharing
- **SQL Injection Protection** - SQLAlchemy ORM

## Production Deployment

1. **Environment Variables** - Configure all environment variables
2. **Database** - Use production PostgreSQL instance
3. **Email Service** - Configure SMTP for OTP delivery
4. **Social OAuth** - Set up OAuth apps for each provider
5. **HTTPS** - Enable SSL/TLS encryption
6. **Rate Limiting** - Implement API rate limiting
7. **Monitoring** - Add logging and monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. 