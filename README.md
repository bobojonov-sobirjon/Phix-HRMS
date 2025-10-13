# Phix HRMS API

A comprehensive Human Resource Management System API built with FastAPI.

## Features

- **User Management**: Registration, authentication, and profile management
- **Gig Jobs**: Freelance job posting and management
- **Full-Time Jobs**: Corporate job posting and management
- **Corporate Profiles**: Company profile management with verification
- **Proposals**: Job application system for both gig and full-time jobs
- **Skills & Certifications**: User skill and certification management
- **Education & Experience**: User education and work experience tracking

## New Features (Latest Update)

### Video Calling System 🎥
- **Real-time Video Calls**: Agora.io integration for high-quality video calling
- **WebSocket Support**: Real-time communication for call management
- **Call Management**: Start, answer, reject, and end video calls
- **Token Generation**: Secure Agora RTC token generation
- **Multi-user Support**: Support for 1-on-1 video calls
- **Call Notifications**: Real-time call status updates via WebSocket

### Corporate Profile System
- **Create Corporate Profile**: Users can create company profiles
- **Email Verification**: OTP-based verification system
- **Profile Management**: Full CRUD operations for corporate profiles
- **One Profile Per User**: Each user can have only one corporate profile

### Full-Time Job System
- **Job Posting**: Create, update, and manage full-time job postings
- **Corporate Profile Requirement**: Only verified corporate profiles can post jobs
- **Job Management**: Full CRUD operations with status management
- **Search & Filter**: Advanced job search with multiple filters

### Enhanced Proposal System
- **Dual Support**: Support for both gig jobs and full-time jobs
- **Unified Interface**: Single proposal system for all job types
- **Validation**: Prevents duplicate applications

## API Endpoints

### Corporate Profile
- `POST /api/v1/corporate-profile/` - Create corporate profile
- `GET /api/v1/corporate-profile/` - Get all corporate profiles
- `GET /api/v1/corporate-profile/active` - Get active corporate profiles
- `GET /api/v1/corporate-profile/{profile_id}` - Get profile by ID
- `GET /api/v1/corporate-profile/user/me` - Get current user's profile
- `PUT /api/v1/corporate-profile/{profile_id}` - Update profile
- `DELETE /api/v1/corporate-profile/{profile_id}` - Delete profile
- `POST /api/v1/corporate-profile/verify` - Verify profile with OTP

### Full-Time Jobs
- `POST /api/v1/full-time-job/` - Create full-time job
- `GET /api/v1/full-time-job/` - Get all active jobs
- `GET /api/v1/full-time-job/search` - Search jobs with filters
- `GET /api/v1/full-time-job/{job_id}` - Get job by ID
- `GET /api/v1/full-time-job/user/me` - Get user's posted jobs
- `PUT /api/v1/full-time-job/{job_id}` - Update job
- `DELETE /api/v1/full-time-job/{job_id}` - Delete job
- `PATCH /api/v1/full-time-job/{job_id}/status` - Change job status

### Enhanced Proposals
- `POST /api/v1/proposals/` - Submit proposal (gig or full-time)
- `GET /api/v1/proposals/{proposal_id}` - Get proposal by ID
- `GET /api/v1/proposals/my-proposals` - Get user's proposals
- `PUT /api/v1/proposals/{proposal_id}` - Update proposal
- `DELETE /api/v1/proposals/{proposal_id}` - Delete proposal

### Chat & Messaging
- `WS /api/chat/ws` - WebSocket for real-time communication

## Database Models

### Corporate Profile
- Company information (name, industry, phone, location, etc.)
- Verification status (is_active, is_verified)
- One-to-one relationship with User

### Full-Time Job
- Job details (title, description, requirements, salary, etc.)
- Work mode (on-site, remote, hybrid)
- Experience level and job type
- Linked to Corporate Profile

### Enhanced Proposal
- Support for both gig_job_id and full_time_job_id
- Cover letter and attachments
- User and job relationships

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run the application: `uvicorn app.main:app --reload`

## Environment Variables

Create a `.env` file with:
```
DATABASE_URL=postgresql://user:password@localhost/dbname
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
OTP_EXPIRE_MINUTES=10
APP_NAME=Phix HRMS
```

## Usage

### Creating a Corporate Profile
1. User creates corporate profile
2. System sends verification email with OTP
3. User verifies profile with OTP
4. Profile becomes active and verified

### Posting Full-Time Jobs
1. User must have verified corporate profile
2. Create full-time job posting
3. Manage job status (active, closed, draft)
4. Receive and review proposals

### Submitting Proposals
1. Users can apply to both gig jobs and full-time jobs
2. Single proposal system for all job types
3. Prevents duplicate applications
4. Full CRUD operations on proposals

### Video Calling
1. Users can start video calls with other users
2. Real-time call notifications via WebSocket
3. Agora.io integration for high-quality video
4. Support for call management (answer, reject, end)
5. Test client available at `static/video_call_client.html`

## Security Features

- JWT-based authentication
- OTP verification for corporate profiles
- User authorization checks
- Input validation and sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. 