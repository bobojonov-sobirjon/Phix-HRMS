# Skills Implementation for Jobs

## Overview

This document describes the new skills implementation for both Gig Jobs and Full-time Jobs. The system now supports skill names instead of skill IDs, with automatic creation of new skills when they don't exist.

## What Changed

### Before (Old Implementation)
```json
{
  "skills_required": "Python, JavaScript, React"
}
```

### After (New Implementation)
```json
{
  "skill_names": ["Python", "JavaScript", "React"]
}
```

## How It Works

1. **Skill Names Input**: Users send skill names as an array of strings
2. **Automatic Skill Creation**: If a skill doesn't exist, it's automatically created
3. **Case-Insensitive Matching**: Skills are matched case-insensitively (e.g., "python" matches "Python")
4. **Empty String Handling**: Empty strings in the array are automatically skipped

## API Usage Examples

### Creating a Gig Job with Skills

```json
POST /api/v1/gig-jobs/gig-job
{
  "title": "Python Developer Needed",
  "description": "We need a Python developer for a project",
  "location": "Remote",
  "experience_level": "mid_level",
  "job_type": "freelance",
  "work_mode": "remote",
  "remote_only": true,
  "skill_names": ["Python", "JavaScript", "React"],
  "min_salary": 1000.0,
  "max_salary": 5000.0,
  "deadline_days": 30
}
```

### Creating a Full-time Job with Skills

```json
POST /api/v1/full-time-jobs/
{
  "title": "Senior React Developer",
  "description": "We need a senior React developer",
  "location": "New York",
  "experience_level": "senior",
  "skill_names": ["JavaScript", "React", "Node.js"],
  "min_salary": 80000.0,
  "max_salary": 120000.0
}
```

## Response Format

Both job types now return skills with full details:

```json
{
  "id": 1,
  "title": "Python Developer Needed",
  "description": "We need a Python developer for a project",
  "skill_names": ["Python", "JavaScript", "React"],
  "skills": [
    {
      "id": 1,
      "name": "Python",
      "created_at": "2025-01-27T10:00:00Z"
    },
    {
      "id": 2,
      "name": "JavaScript",
      "created_at": "2025-01-27T10:00:00Z"
    },
    {
      "id": 3,
      "name": "React",
      "created_at": "2025-01-27T10:00:00Z"
    }
  ],
  "min_salary": 1000.0,
  "max_salary": 5000.0
}
```

## Database Structure

### New Tables
- `gig_job_skills` - Junction table for gig jobs and skills
- `full_time_job_skills` - Junction table for full-time jobs and skills

### Updated Models
- `GigJob` - Now has `skills` relationship instead of `skills_required` text field
- `FullTimeJob` - Now has `skills` relationship instead of `skills_required` text field
- `Skill` - Added back references to both job types

## Benefits

1. **Flexibility**: Users can send any skill names without worrying about IDs
2. **Automatic Creation**: New skills are created automatically
3. **Data Consistency**: Skills are properly normalized in the database
4. **Search Capability**: Can now search jobs by skills efficiently
5. **Type Safety**: Skill names are validated as strings

## Migration

The old `skills_required` text columns have been removed and replaced with proper many-to-many relationships. The migration `44fcefde72d6_add_job_skills_junction_tables` handles this transition.

## Error Handling

- Empty skill names are automatically skipped
- Skills are created with trimmed names (whitespace removed)
- Case-insensitive matching prevents duplicate skills with different cases

## Future Enhancements

- Skill categories/tags
- Skill popularity tracking
- Skill-based job recommendations
- Skill validation against predefined lists
