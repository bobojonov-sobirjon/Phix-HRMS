# Testing Relevance Scores for User ID 2

## JWT Token Details
- **User ID**: 2
- **Token**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzU4ODczMzMyLCJ0eXBlIjoiYWNjZXNzIn0.lAAH-zkdJuiAr7tjwhE1UhXOuyycglS4n77Tjs8E8Dw`

## API Endpoints to Test

### 1. Get All Gig Jobs with Relevance Scores
```bash
curl -X GET "http://localhost:8000/gig-jobs/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzU4ODczMzMyLCJ0eXBlIjoiYWNjZXNzIn0.lAAH-zkdJuiAr7tjwhE1UhXOuyycglS4n77Tjs8E8Dw" \
  -H "Content-Type: application/json" \
  -G -d "page=1" -d "size=10"
```

### 2. Get All Full-Time Jobs with Relevance Scores
```bash
curl -X GET "http://localhost:8000/full-time-jobs/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzU4ODczMzMyLCJ0eXBlIjoiYWNjZXNzIn0.lAAH-zkdJuiAr7tjwhE1UhXOuyycglS4n77Tjs8E8Dw" \
  -H "Content-Type: application/json" \
  -G -d "page=1" -d "size=10"
```

### 3. Search Gig Jobs with Relevance Scores
```bash
curl -X GET "http://localhost:8000/gig-jobs/filter/search" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzU4ODczMzMyLCJ0eXBlIjoiYWNjZXNzIn0.lAAH-zkdJuiAr7tjwhE1UhXOuyycglS4n77Tjs8E8Dw" \
  -H "Content-Type: application/json" \
  -G -d "q=python" -d "page=1" -d "size=5"
```

### 4. Search Full-Time Jobs with Relevance Scores
```bash
curl -X GET "http://localhost:8000/full-time-jobs/search" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzU4ODczMzMyLCJ0eXBlIjoiYWNjZXNzIn0.lAAH-zkdJuiAr7tjwhE1UhXOuyycglS4n77Tjs8E8Dw" \
  -H "Content-Type: application/json" \
  -G -d "title=developer" -d "page=1" -d "size=5"
```

## Expected Response Format

Each job in the response will now include:

```json
{
  "id": 1,
  "title": "Job Title",
  "description": "Job Description",
  "all_jobs_count": 5,
  "relevance_score": 85.5,
  "skills": [
    {
      "id": 1,
      "name": "Python",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00",
      "is_deleted": false
    }
  ],
  // ... other job fields
}
```

## Relevance Score Calculation

The relevance score (0.0 - 100.0) is calculated based on:

1. **Skill Matching** (Primary): Percentage of job skills that match user's skills
2. **Experience Level Match**: +10 points if user's experience matches job requirement
3. **Location Match**: +5 points if user's location matches job location
4. **Salary Range Match**: +15 points if user's expected salary is within job range
5. **Work Mode Match**: +8 points (full-time jobs only)
6. **Job Type Match**: +7 points (full-time jobs only)

## Notes

- **relevance_score** will be `null` if no token is provided
- **relevance_score** will be calculated for ALL users, including job creators
- **all_jobs_count** shows total jobs created by the job author
- Scores are capped at 100.0 maximum
