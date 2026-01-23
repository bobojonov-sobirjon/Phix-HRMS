# 🚀 Phix HRMS API

> A comprehensive Human Resource Management System API built with modern technologies

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.9+-3776ab?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Demo Account](#-demo-account)
- [API Documentation](#-api-documentation)
- [Database Schema](#-database-schema)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 👥 User Management
- User registration and authentication (JWT-based)
- Social authentication (Google, Facebook, Apple)
- Profile management with avatar upload
- Skills, certifications, education, and experience tracking
- Role-based access control (Admin, User)

### 💼 Job Management
- **Gig Jobs**: Freelance and short-term project postings
- **Full-Time Jobs**: Corporate job postings with verification
- Advanced job search with multiple filters
- Job status management (draft, active, closed)
- Saved jobs functionality

### 🏢 Corporate Profile System
- Company profile creation and verification
- Email OTP-based verification
- Logo upload and company information management
- One profile per user restriction
- Team member management

### 📝 Proposal System
- Unified proposal system for both gig and full-time jobs
- Cover letter and attachment support
- Duplicate application prevention
- Full CRUD operations with status tracking

### 💬 Real-Time Communication
- **Chat System**: Real-time messaging with WebSocket
- **Video Calling**: Agora.io integration for HD video calls
- Call management (start, answer, reject, end)
- Secure token generation for video calls
- Real-time presence and typing indicators

### 📧 Notification System
- Email notifications (Brevo/SendGrid integration)
- Firebase push notifications
- In-app notifications
- Real-time notification delivery

### 🌍 Localization & Data
- Multi-language support
- Pre-populated data (companies, universities, certifications)
- Location and category management
- Country and city data with flags

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL 14+
- **ORM**: SQLAlchemy
- **Migration**: Alembic
- **Authentication**: JWT (PyJWT)
- **Password Hashing**: bcrypt

### Real-Time Communication
- **WebSocket**: FastAPI WebSockets
- **Video Calling**: Agora.io RTC
- **Chat**: Custom WebSocket implementation

### Third-Party Services
- **Email**: Brevo (Sendinblue) / SendGrid
- **Push Notifications**: Firebase Cloud Messaging
- **Storage**: Local file system (configurable)

### DevOps
- **Server**: Uvicorn (ASGI)
- **Proxy**: Nginx (optional)
- **Environment**: Python venv

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- PostgreSQL 14 or higher
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/phix-hrms.git
cd phix-hrms
```

2. **Create virtual environment**
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
python utils/setup_db.py
```

6. **Run migrations**
```bash
alembic upgrade head
```

7. **Start the server**
```bash
python run_server.py
# Or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

8. **Access the API**
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🎭 Demo Account

For testing purposes, a demo account is available with pre-configured credentials and permanent OTP.

### Setup Demo Account
```bash
python setup_demo_account.py
```

### Demo Credentials
- **Email**: `cheker@test.com`
- **Password**: `12345678@#hello_phix`
- **OTP Code**: `12345` (permanent, never expires)

### OTP Types Available
- `password_reset` - For forgot password flow
- `email_verification` - For email verification
- `corporate_verification` - For corporate profile verification

### Testing with Demo Account

1. **Login**
```bash
POST /api/v1/auth/login
{
  "email": "cheker@test.com",
  "password": "12345678@#hello_phix"
}
```

2. **Verify Corporate Profile**
```bash
POST /api/v1/corporate-profile/verify
{
  "otp_code": "12345"
}
```

3. **Reset Password**
```bash
POST /api/v1/auth/verify-otp
{
  "email": "cheker@test.com",
  "otp_code": "12345"
}
```

> **Note**: Demo account is for testing only. Do not use in production!

## 📚 API Documentation

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | User registration |
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/forgot-password` | Request password reset |
| POST | `/api/v1/auth/verify-otp` | Verify OTP code |
| POST | `/api/v1/auth/reset-password` | Reset password with OTP |

### Profile
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/profile/me` | Get current user profile |
| PUT | `/api/v1/profile/me` | Update user profile |
| POST | `/api/v1/profile/avatar` | Upload avatar |
| POST | `/api/v1/profile/education` | Add education |
| POST | `/api/v1/profile/experience` | Add experience |
| POST | `/api/v1/profile/certification` | Add certification |

### Corporate Profile
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/corporate-profile/` | Create corporate profile |
| GET | `/api/v1/corporate-profile/` | Get all corporate profiles |
| GET | `/api/v1/corporate-profile/active` | Get active profiles |
| GET | `/api/v1/corporate-profile/{id}` | Get profile by ID |
| GET | `/api/v1/corporate-profile/user/me` | Get user's profile |
| PUT | `/api/v1/corporate-profile/{id}` | Update profile |
| DELETE | `/api/v1/corporate-profile/{id}` | Delete profile |
| POST | `/api/v1/corporate-profile/verify` | Verify with OTP |

### Full-Time Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/full-time-job/` | Create job posting |
| GET | `/api/v1/full-time-job/` | Get all active jobs |
| GET | `/api/v1/full-time-job/search` | Search jobs |
| GET | `/api/v1/full-time-job/{id}` | Get job by ID |
| GET | `/api/v1/full-time-job/user/me` | Get user's jobs |
| PUT | `/api/v1/full-time-job/{id}` | Update job |
| DELETE | `/api/v1/full-time-job/{id}` | Delete job |
| PATCH | `/api/v1/full-time-job/{id}/status` | Change job status |

### Gig Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/gig-jobs/` | Create gig job |
| GET | `/api/v1/gig-jobs/` | Get all gig jobs |
| GET | `/api/v1/gig-jobs/search` | Search gig jobs |
| GET | `/api/v1/gig-jobs/{id}` | Get gig job by ID |
| PUT | `/api/v1/gig-jobs/{id}` | Update gig job |
| DELETE | `/api/v1/gig-jobs/{id}` | Delete gig job |

### Proposals
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/proposals/` | Submit proposal |
| GET | `/api/v1/proposals/{id}` | Get proposal by ID |
| GET | `/api/v1/proposals/my-proposals` | Get user's proposals |
| PUT | `/api/v1/proposals/{id}` | Update proposal |
| DELETE | `/api/v1/proposals/{id}` | Delete proposal |

### Chat & Video
| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/api/v1/chat/ws` | WebSocket connection |
| POST | `/api/v1/chat/rooms` | Create chat room |
| GET | `/api/v1/chat/rooms` | Get user's rooms |
| POST | `/api/v1/chat/messages` | Send message |
| POST | `/api/v1/chat/video-call/token` | Get Agora token |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/users` | Get all users |
| PUT | `/api/v1/admin/users/{id}/verify` | Verify user |
| DELETE | `/api/v1/admin/users/{id}` | Delete user |

> **Full API Documentation**: Visit `/docs` for interactive Swagger UI

## 🗄 Database Schema

### Core Models
- **User**: User accounts and authentication
- **Role**: User roles (Admin, User)
- **OTP**: One-Time Password for verification

### Profile Models
- **Education**: User education history
- **Experience**: Work experience
- **Certification**: Professional certifications
- **Project**: Portfolio projects
- **Skill**: User skills and expertise
- **Language**: Language proficiency

### Job Models
- **GigJob**: Freelance job postings
- **FullTimeJob**: Full-time job postings
- **Proposal**: Job applications
- **SavedJob**: Saved job listings

### Company Models
- **CorporateProfile**: Company profiles
- **TeamMember**: Corporate team members
- **Company**: Pre-populated company data

### Communication Models
- **ChatRoom**: Chat rooms
- **ChatMessage**: Chat messages
- **ChatParticipant**: Room participants
- **AgoraChannel**: Video call channels
- **Notification**: User notifications

### Master Data
- **Location**: Countries and cities
- **Category**: Job categories
- **EducationFacility**: Universities
- **CertificationCenter**: Certification providers

## ⚙ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/phix_hrms

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (Brevo)
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=noreply@phix.com

# OTP
OTP_EXPIRE_MINUTES=10

# Agora (Video Calling)
AGORA_APP_ID=your-agora-app-id
AGORA_APP_CERTIFICATE=your-agora-app-certificate

# Firebase (Push Notifications)
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json

# App
APP_NAME=Phix HRMS
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Database Setup

1. **Create PostgreSQL database**
```sql
CREATE DATABASE phix_hrms;
```

2. **Run setup script**
```bash
python utils/setup_db.py
```

3. **Apply migrations**
```bash
alembic upgrade head
```

## 📖 Usage Guide

### 1. Creating a Corporate Profile

```python
# Step 1: Create profile
POST /api/v1/corporate-profile/
{
  "company_name": "Tech Company",
  "phone_number": "1234567890",
  "country_code": "+1",
  "location_id": 1,
  "overview": "We are a tech company...",
  "website_url": "https://techcompany.com",
  "company_size": "50-200",
  "category_id": 1
}

# Step 2: Verify with OTP (sent to email)
POST /api/v1/corporate-profile/verify
{
  "otp_code": "123456"
}
```

### 2. Posting a Job

```python
# Create full-time job (requires verified corporate profile)
POST /api/v1/full-time-job/
{
  "title": "Senior Backend Developer",
  "description": "We are looking for...",
  "requirements": "5+ years experience...",
  "location_id": 1,
  "work_mode": "remote",
  "job_type": "full_time",
  "experience_level": "senior",
  "salary_min": 80000,
  "salary_max": 120000,
  "skills": [1, 2, 3]
}
```

### 3. Submitting a Proposal

```python
# Apply to a job
POST /api/v1/proposals/
{
  "full_time_job_id": 1,
  "cover_letter": "I am interested in this position...",
  "expected_salary": 100000
}
```

### 4. Starting a Video Call

```python
# Get Agora token
POST /api/v1/chat/video-call/token
{
  "room_id": 1,
  "uid": 12345,
  "role": "publisher",
  "expire_seconds": 3600
}

# Use token with Agora SDK in client application
```

## 🔒 Security

### Authentication & Authorization
- JWT-based authentication with access and refresh tokens
- Password hashing using bcrypt with salt
- Role-based access control (RBAC)
- Token expiration and refresh mechanism

### Data Protection
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (input sanitization)
- CORS configuration for API security
- Environment variable security

### OTP & Verification
- Time-limited OTPs (configurable expiration)
- One-time use OTP validation
- Email verification for corporate profiles
- Secure OTP storage with hashing

### Best Practices
- HTTPS recommended for production
- Regular security updates
- Database connection pooling
- Rate limiting (recommended to add)
- Input validation and sanitization

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Add tests**
5. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
6. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for functions and classes
- Add comments for complex logic

### Testing
```bash
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Authors

- **Your Name** - *Initial work*

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- Agora.io for video calling integration
- PostgreSQL for robust database
- All contributors who helped with this project

## 📞 Support

For support, email support@phix.com or open an issue on GitHub.

---

<div align="center">
  <strong>⭐ Star this repository if you find it helpful!</strong>
</div>
