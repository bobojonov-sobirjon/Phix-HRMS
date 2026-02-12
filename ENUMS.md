# API Enum Values Documentation

**Last Updated**: 2026-02-12  
**Important**: All enum values are now **LOWERCASE** for frontend compatibility!

---

## 1. Full-Time Job Enums

### ExperienceLevel
**API Path**: `/api/v1/full-time-jobs/`

```json
{
  "experience_level": "entry_level" | "junior" | "mid_level" | "director"
}
```

**Available Values**:
- `entry_level` - Entry level position
- `junior` - Junior level
- `mid_level` - Mid level
- `director` - Director level

**Example**:
```json
{
  "title": "Software Engineer",
  "experience_level": "mid_level",
  ...
}
```

---

### JobType
**API Path**: `/api/v1/full-time-jobs/`

```json
{
  "job_type": "full_time" | "part_time" | "contract" | "internship"
}
```

**Available Values**:
- `full_time` - Full-time position
- `part_time` - Part-time position
- `contract` - Contract position
- `internship` - Internship position

---

### WorkMode
**API Path**: `/api/v1/full-time-jobs/`

```json
{
  "work_mode": "on_site" | "remote" | "hybrid"
}
```

**Available Values**:
- `on_site` - On-site work
- `remote` - Remote work
- `hybrid` - Hybrid work

---

### JobStatus
**API Path**: `/api/v1/full-time-jobs/`

```json
{
  "status": "draft" | "active" | "closed" | "expired"
}
```

**Available Values**:
- `draft` - Draft (not published)
- `active` - Active/Published
- `closed` - Closed (no longer accepting applications)
- `expired` - Expired

---

### PayPeriod
**API Path**: `/api/v1/full-time-jobs/`

```json
{
  "pay_period": "per_hour" | "per_day" | "per_week" | "per_month" | "per_year"
}
```

**Available Values**:
- `per_hour` - Hourly rate
- `per_day` - Daily rate
- `per_week` - Weekly rate
- `per_month` - Monthly rate
- `per_year` - Yearly rate

---

## 2. Gig Job Enums

### ExperienceLevel (Gig)
**API Path**: `/api/v1/gig-jobs/`

```json
{
  "experience_level": "entry_level" | "mid_level" | "junior" | "director"
}
```

**Available Values**:
- `entry_level` - Entry level
- `mid_level` - Mid level
- `junior` - Junior level
- `director` - Director level

**Note**: Same as Full-Time Job but only these 4 values!

---

### GigJobStatus
**API Path**: `/api/v1/gig-jobs/`

```json
{
  "status": "active" | "in_progress" | "completed" | "cancelled"
}
```

**Available Values**:
- `active` - Active (accepting proposals)
- `in_progress` - In progress
- `completed` - Completed
- `cancelled` - Cancelled

---

### ProjectLength
**API Path**: `/api/v1/gig-jobs/`

```json
{
  "project_length": "less_than_one_month" | "one_to_three_months" | "three_to_six_months" | "more_than_six_months"
}
```

**Available Values**:
- `less_than_one_month` - Less than 1 month
- `one_to_three_months` - 1-3 months
- `three_to_six_months` - 3-6 months
- `more_than_six_months` - More than 6 months

---

### DatePosted (for filtering)
**API Path**: `/api/v1/gig-jobs/` (query parameter)

```json
{
  "date_posted": "any_time" | "past_24_hours" | "past_week" | "past_month"
}
```

**Available Values**:
- `any_time` - Any time
- `past_24_hours` - Last 24 hours
- `past_week` - Last 7 days
- `past_month` - Last 30 days

---

### SortBy (for filtering)
**API Path**: `/api/v1/gig-jobs/` (query parameter)

```json
{
  "sort_by": "newest" | "oldest" | "budget_high_to_low" | "budget_low_to_high"
}
```

**Available Values**:
- `newest` - Newest first
- `oldest` - Oldest first
- `budget_high_to_low` - Highest budget first
- `budget_low_to_high` - Lowest budget first

---

## 3. Corporate Profile Enums

### CompanySize
**API Path**: `/api/v1/corporate-profile/`

```json
{
  "company_size": "1-10" | "10-50" | "50-200" | "200-1000" | "1000+"
}
```

**Available Values**:
- `1-10` - Startup (1-10 employees)
- `10-50` - Small (10-50 employees)
- `50-200` - Medium (50-200 employees)
- `200-1000` - Large (200-1000 employees)
- `1000+` - Enterprise (1000+ employees)

---

## 4. Team Member Enums

### TeamMemberRole
**API Path**: `/api/v1/team-member/`

```json
{
  "role": "owner" | "admin" | "member"
}
```

**Available Values**:
- `owner` - Owner (full access)
- `admin` - Admin (manage team)
- `member` - Member (limited access)

---

### TeamMemberStatus
**API Path**: `/api/v1/team-member/`

```json
{
  "status": "active" | "inactive"
}
```

**Available Values**:
- `active` - Active member
- `inactive` - Inactive member

---

## 5. Notification Enums

### NotificationType
**API Path**: `/api/v1/notifications/`

```json
{
  "type": "application" | "message" | "system" | "job_update"
}
```

**Available Values**:
- `application` - Job application notification
- `message` - Chat message notification
- `system` - System notification
- `job_update` - Job update notification

---

## 6. Chat Enums

### MessageType
**API Path**: `/api/v1/chat/`

```json
{
  "message_type": "text" | "image" | "file" | "voice"
}
```

**Available Values**:
- `text` - Text message
- `image` - Image message
- `file` - File attachment
- `voice` - Voice message

---

## Migration Summary

### Changed from UPPERCASE to lowercase:
1. **ExperienceLevel**: 
   - ❌ Old: `ENTRY`, `MID`, `SENIOR`, `LEAD`
   - ✅ New: `entry_level`, `mid_level`, `junior`, `director`

2. **GigJobStatus**: 
   - ❌ Old: `ACTIVE`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`
   - ✅ New: `active`, `in_progress`, `completed`, `cancelled`

3. **TeamMemberRole**: 
   - ❌ Old: `OWNER`, `ADMIN`, `MEMBER`
   - ✅ New: `owner`, `admin`, `member`

4. **TeamMemberStatus**: 
   - ❌ Old: `ACTIVE`, `INACTIVE`
   - ✅ New: `active`, `inactive`

### Already lowercase (no changes):
- JobType: `full_time`, `part_time`, etc.
- WorkMode: `on_site`, `remote`, `hybrid`
- JobStatus: `draft`, `active`, `closed`, `expired`
- PayPeriod: `per_hour`, `per_day`, etc.
- ProjectLength: `less_than_one_month`, etc.
- CompanySize: `1-10`, `10-50`, etc.
- NotificationType: `application`, `message`, etc.
- MessageType: `text`, `image`, `file`, `voice`

---

## Important Notes for Frontend

1. **All enum values are case-sensitive** - use exact lowercase values
2. **Validation errors** will occur if you send UPPERCASE values
3. **When filtering/searching**, use lowercase values in query parameters
4. **When displaying to users**, you can format them nicely:
   - `entry_level` → "Entry Level"
   - `mid_level` → "Mid Level"
   - `one_to_three_months` → "1-3 months"

---

## Example API Requests

### Create Full-Time Job
```json
POST /api/v1/full-time-jobs/
{
  "title": "Senior Developer",
  "experience_level": "mid_level",
  "job_type": "full_time",
  "work_mode": "remote",
  "pay_period": "per_month",
  "status": "active",
  ...
}
```

### Create Gig Job
```json
POST /api/v1/gig-jobs/
{
  "title": "Website Design",
  "experience_level": "mid_level",
  "project_length": "one_to_three_months",
  "status": "active",
  ...
}
```

### Create Corporate Profile
```json
POST /api/v1/corporate-profile/
{
  "company_name": "Tech Company",
  "company_size": "10-50",
  ...
}
```

---

**Contact**: Backend team for any questions about enum values
**Last Migration**: 2026-02-12
