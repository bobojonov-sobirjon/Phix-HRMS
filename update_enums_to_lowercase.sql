-- Update all enum types to lowercase values
-- Run this script in PostgreSQL: sudo -u postgres psql -d phix_hrms -f update_enums_to_lowercase.sql

BEGIN;

-- 1. TeamMemberRole: OWNER -> owner, etc.
ALTER TYPE teammemberrole RENAME TO teammemberrole_old;
CREATE TYPE teammemberrole AS ENUM ('owner', 'admin', 'hr_manager', 'recruiter', 'viewer');
ALTER TABLE team_members ALTER COLUMN role TYPE teammemberrole USING role::text::teammemberrole;
ALTER TABLE full_time_jobs ALTER COLUMN created_by_role TYPE teammemberrole USING created_by_role::text::teammemberrole;
DROP TYPE teammemberrole_old;

-- 2. TeamMemberStatus: PENDING -> pending, etc.
ALTER TYPE teammemberstatus RENAME TO teammemberstatus_old;
CREATE TYPE teammemberstatus AS ENUM ('pending', 'accepted', 'rejected');
ALTER TABLE team_members ALTER COLUMN status TYPE teammemberstatus USING status::text::teammemberstatus;
DROP TYPE teammemberstatus_old;

-- 3. PayPeriod: PER_HOUR -> per_hour (already done, but making sure)
ALTER TYPE payperiod RENAME TO payperiod_old;
CREATE TYPE payperiod AS ENUM ('per_hour', 'per_day', 'per_week', 'per_month', 'per_year');
ALTER TABLE full_time_jobs ALTER COLUMN pay_period TYPE payperiod USING pay_period::text::payperiod;
DROP TYPE payperiod_old;

-- 4. GigJob ExperienceLevel: ENTRY_LEVEL -> entry_level
-- First check if this is a separate type or same as full_time_job experiencelevel
-- If gig_jobs uses a different experience level enum, update it here
-- Note: This may not exist as a separate type

-- 5. ProjectLength: LESS_THAN_ONE_MONTH -> less_than_one_month
ALTER TYPE projectlength RENAME TO projectlength_old;
CREATE TYPE projectlength AS ENUM ('less_than_one_month', 'one_to_three_months', 'three_to_six_months', 'more_than_six_months');
ALTER TABLE gig_jobs ALTER COLUMN project_length TYPE projectlength USING project_length::text::projectlength;
DROP TYPE projectlength_old;

COMMIT;

-- Verify changes
SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'teammemberrole') ORDER BY enumsortorder;
SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'teammemberstatus') ORDER BY enumsortorder;
SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'payperiod') ORDER BY enumsortorder;
SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'projectlength') ORDER BY enumsortorder;
