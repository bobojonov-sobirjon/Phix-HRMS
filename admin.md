# Admin Panel API Documentation

This document outlines all the API endpoints available for the admin panel. Admin users can view all data, and can add/edit/delete certain resources (like Locations, Skills, Categories, etc.), but **cannot create users** (users can only be viewed, blocked/unblocked, and verified).

**Base URL:** `/api/v1`

**Authentication:** All endpoints require Bearer token authentication. Admin-specific endpoints require admin role.

---

---

## ✅ EXISTING Admin-Specific Endpoints

### 1. Users Management

#### Get All Users
- **Endpoint:** `GET /api/v1/admin/users`
- **Description:** Get all users with filters and pagination (Admin only)
- **Authentication:** Required (Admin role)
- **Query Parameters:**
  - `page` (int, optional): Page number (default: 1)
  - `limit` (int, optional): Items per page (default: 20, max: 100)
  - `role` (string, optional): Filter by role (employer/worker)
  - `is_active` (bool, optional): Filter by active status
  - `is_verified` (bool, optional): Filter by verification status
  - `is_deleted` (bool, optional): Filter by deleted status
  - `search` (string, optional): Search by name or email
  - `date_from` (datetime, optional): Filter by registration date from
  - `date_to` (datetime, optional): Filter by registration date to
- **Response:** List of users with full details including:
  - Basic info (id, name, email, phone, avatar_url)
  - Profile info (about_me, current_position, location, language)
  - Category info (main_category, sub_category)
  - Account status (is_active, is_verified, is_deleted, blocked_at, block_reason, blocked_by)
  - Timestamps (created_at, updated_at, last_login)
  - Related data counts (gig_jobs_count, full_time_jobs_count, proposals_count, saved_jobs_count)
  - Has corporate profile flag

#### Block User
- **Endpoint:** `PATCH /api/v1/admin/users/{user_id}/block`
- **Description:** Block a user (set is_active to false)
- **Authentication:** Required (Admin role)
- **Request Body (optional):**
  - `reason` (string, optional): Reason for blocking
- **Response:** Success message with blocking details

#### Unblock User
- **Endpoint:** `PATCH /api/v1/admin/users/{user_id}/unblock`
- **Description:** Unblock a user (set is_active to true)
- **Authentication:** Required (Admin role)
- **Response:** Success message

---

## ✅ EXISTING Admin-Specific Endpoints

### 1. Users Management - Block/Unblock

#### Block User
- **Endpoint:** `PATCH /api/v1/admin/users/{user_id}/block`
- **Description:** Block a user (set is_active to false)
- **Authentication:** Required (Admin role)
- **Request Body (optional):**
  - `reason` (string, optional): Reason for blocking
- **Response:** Success message with blocking details

#### Unblock User
- **Endpoint:** `PATCH /api/v1/admin/users/{user_id}/unblock`
- **Description:** Unblock a user (set is_active to true)
- **Authentication:** Required (Admin role)
- **Response:** Success message

---

## ✅ EXISTING View Endpoints (Admin Can Use)

### 2. Users Management

#### Get User by ID
- **Endpoint:** `GET /api/v1/profile/user/{user_id}`
- **Description:** Get user profile by ID (public endpoint)
- **Authentication:** Not required
- **Path Parameters:**
  - `user_id` (int, required): User ID
- **Response:** Full user details including:
  - Basic info (id, name, email, phone, avatar_url)
  - Profile info (about_me, current_position, location, language)
  - Category info (main_category, sub_category)
  - Account status (is_active, is_verified, is_deleted)
  - Timestamps (created_at, updated_at, last_login)

**Note:** This endpoint exists but doesn't include all related data counts. For admin, we need a more detailed version.

---

### 3. Corporate Profiles Management

#### Get All Corporate Profiles
- **Endpoint:** `GET /api/v1/corporate-profile/`
- **Description:** Get all verified corporate profiles with pagination
- **Authentication:** Optional
- **Query Parameters:**
  - `page` (int, optional): Page number (default: 1)
  - `size` (int, optional): Page size (default: 10)
- **Response:** List of verified corporate profiles with:
  - id, phone_number, country_code, location_id
  - overview, website_url, company_size, logo_url
  - category_id, company_id
  - is_active, is_verified, is_deleted
  - user_id, created_at, updated_at
  - User information
  - Location information
  - Category information
  - Company information
  - Team members list
  - Followers count

#### Get Active Corporate Profiles
- **Endpoint:** `GET /api/v1/corporate-profile/active`
- **Description:** Get only active corporate profiles
- **Authentication:** Optional
- **Query Parameters:**
  - `page` (int, optional): Page number (default: 1)
  - `size` (int, optional): Page size (default: 10)

#### Get Corporate Profile by ID
- **Endpoint:** `GET /api/v1/corporate-profile/{profile_id}`
- **Description:** Get corporate profile by ID
- **Authentication:** Optional
- **Path Parameters:**
  - `profile_id` (int, required): Corporate profile ID
- **Response:** Full corporate profile details including:
  - All profile fields
  - User details
  - Location details
  - Category details
  - Company details
  - Team members list
  - Full-time jobs list
  - Followers list

**Note:** Current endpoint only shows verified/active profiles. Admin needs to see all profiles including unverified/inactive.

---

### 4. Gig Jobs Management

#### Get All Gig Jobs
- **Endpoint:** `GET /api/v1/gig-jobs/`
- **Description:** Get all gig jobs with advanced filtering and pagination
- **Authentication:** Optional (better results if authenticated)
- **Query Parameters:**
  - `page` (int, optional): Page number (default: 1)
  - `size` (int, optional): Page size (default: 10, max: 100)
  - `status_filter` (string, optional): Filter by status
  - `experience_level` (string, optional): Filter by experience level
  - `project_length` (string, optional): Filter by project length
  - `min_salary` (float, optional): Filter by minimum salary
  - `max_salary` (float, optional): Filter by maximum salary
  - `location_id` (int, optional): Filter by location ID
  - `category_id` (int, optional): Filter by category ID
  - `subcategory_id` (int, optional): Filter by subcategory ID
  - `date_posted` (string, optional): Filter by date posted
  - `sort_by` (string, optional): Sort by (most_recent, most_relevant)
- **Response:** List of gig jobs with:
  - Job details (id, title, description, location, experience_level, project_length)
  - Salary range (min_salary, max_salary)
  - Status and timestamps
  - Author information
  - Category and subcategory
  - Skills
  - Number of proposals

#### Get Gig Job by ID
- **Endpoint:** `GET /api/v1/gig-jobs/{gig_job_id}`
- **Description:** Get a specific gig job by ID
- **Authentication:** Optional
- **Path Parameters:**
  - `gig_job_id` (int, required): Gig job ID
- **Response:** Full gig job details including:
  - All job fields
  - Author details
  - Category and subcategory details
  - Location details
  - Skills list
  - Proposals list with user details

**Note:** Current endpoint doesn't show deleted jobs. Admin needs to see all jobs including deleted ones.

---

### 5. Full-Time Jobs Management

#### Get All Full-Time Jobs
- **Endpoint:** `GET /api/v1/full-time-jobs/`
- **Description:** Get all full-time jobs with pagination
- **Authentication:** Optional
- **Query Parameters:**
  - `page` (int, optional): Page number (default: 1)
  - `size` (int, optional): Page size (default: 10, max: 100)
  - `category_id` (int, optional): Filter by category ID
  - `subcategory_id` (int, optional): Filter by subcategory ID
- **Response:** List of full-time jobs with:
  - Job details (id, title, description, responsibilities, location)
  - Job type, work mode, experience level
  - Salary range (min_salary, max_salary, pay_period)
  - Status and timestamps
  - Company (corporate profile) information
  - Category and subcategory
  - Skills
  - Number of proposals

#### Search Full-Time Jobs
- **Endpoint:** `GET /api/v1/full-time-jobs/search`
- **Description:** Search full-time jobs with filters
- **Query Parameters:**
  - `title` (string, optional): Search by title
  - `location` (string, optional): Filter by location
  - `experience_level` (string, optional): Filter by experience level
  - `work_mode` (string, optional): Filter by work mode
  - `skill_ids` (string, optional): Comma-separated list of skill IDs
  - `category_id` (int, optional): Filter by category ID
  - `subcategory_id` (int, optional): Filter by subcategory ID
  - `min_salary` (float, optional): Filter by minimum salary
  - `max_salary` (float, optional): Filter by maximum salary
  - `page` (int, optional): Page number
  - `size` (int, optional): Page size

#### Get Full-Time Job by ID
- **Endpoint:** `GET /api/v1/full-time-jobs/{job_id}`
- **Description:** Get full-time job by ID
- **Authentication:** Optional
- **Path Parameters:**
  - `job_id` (int, required): Full-time job ID
- **Response:** Full job details including:
  - All job fields
  - Company (corporate profile) details
  - Category and subcategory details
  - Skills list
  - Proposals list with user details
  - Created by user information

**Note:** Current endpoint only shows ACTIVE jobs to non-owners. Admin needs to see all jobs regardless of status.

---

### 6. Proposals Management

#### Get Proposal by ID
- **Endpoint:** `GET /api/v1/proposals/{proposal_id}`
- **Description:** Get a specific proposal by ID
- **Authentication:** Required
- **Path Parameters:**
  - `proposal_id` (int, required): Proposal ID
- **Response:** Full proposal details including:
  - All proposal fields
  - User details
  - Job details (gig or full-time)
  - Attachments with file URLs

#### Get My Gig Job Proposals
- **Endpoint:** `GET /api/v1/proposals/my-proposals-gig-job`
- **Description:** Get gig job proposals submitted by the current user
- **Authentication:** Required
- **Query Parameters:**
  - `page` (int, optional): Page number (default: 1)
  - `size` (int, optional): Page size (default: 10, max: 100)

#### Get My Full-Time Job Proposals
- **Endpoint:** `GET /api/v1/proposals/my-proposals-full-time-jobs`
- **Description:** Get full-time job proposals submitted by the current user
- **Authentication:** Required
- **Query Parameters:**
  - `page` (int, optional): Page number (default: 1)
  - `size` (int, optional): Page size (default: 10, max: 100)

#### Get Gig Job Proposals
- **Endpoint:** `GET /api/v1/proposals/gig-job/{gig_job_id}`
- **Description:** Get all proposals for a specific gig job (only by the gig job author)
- **Authentication:** Required
- **Path Parameters:**
  - `gig_job_id` (int, required): Gig job ID
- **Query Parameters:**
  - `page` (int, optional): Page number (default: 1)
  - `size` (int, optional): Page size (default: 10, max: 100)

#### Get Full-Time Job Proposals
- **Endpoint:** `GET /api/v1/proposals/full-time-job/{full_time_job_id}`
- **Description:** Get all proposals for a specific full-time job (only by the full-time job author)
- **Authentication:** Required
- **Path Parameters:**
  - `full_time_job_id` (int, required): Full-time job ID
- **Query Parameters:**
  - `page` (int, optional): Page number (default: 1)
  - `size` (int, optional): Page size (default: 10, max: 100)

**Note:** Current endpoints only show user-specific or job-owner-specific proposals. Admin needs to see ALL proposals.

---

## ✅ EXISTING CRUD Endpoints (Admin Can Use)

### 7. Companies Management

#### Get All Companies
- **Endpoint:** `GET /api/v1/companies/`
- **Description:** Get all companies with optional search and pagination
- **Authentication:** Required
- **Query Parameters:**
  - `skip` (int, optional): Number of records to skip (default: 0)
  - `limit` (int, optional): Maximum number of records (default: 100, max: 100)
  - `search` (string, optional): Search by name
- **Response:** List of companies with:
  - id, name, icon, country
  - created_at, updated_at
  - is_deleted status

#### Get Company by ID
- **Endpoint:** `GET /api/v1/companies/{company_id}`
- **Description:** Get a specific company by ID
- **Authentication:** Required
- **Response:** Full company details

#### Create Company
- **Endpoint:** `POST /api/v1/companies/`
- **Description:** Create a new company
- **Authentication:** Required
- **Request Body:**
  - `name` (string, required): Company name
  - `icon` (string, optional): Icon URL
  - `country` (string, optional): Country name
- **Response:** Created company details

#### Update Company
- **Endpoint:** `PATCH /api/v1/companies/{company_id}`
- **Description:** Update an existing company
- **Authentication:** Required
- **Request Body:**
  - `name` (string, optional): Company name
  - `icon` (string, optional): Icon URL
  - `country` (string, optional): Country name
- **Response:** Updated company details

#### Delete Company
- **Endpoint:** `DELETE /api/v1/companies/{company_id}`
- **Description:** Delete a company (soft delete)
- **Authentication:** Required
- **Response:** Success message

---

### 8. Categories Management

#### Create Category (Main or Sub)
- **Endpoint:** `POST /api/v1/categories/`
- **Description:** Create a new category or subcategory
  - If `parent_id` is **not provided** or is **null**: Creates a **main category**
  - If `parent_id` is **provided**: Creates a **subcategory** under that parent
- **Authentication:** Required
- **Request Body:**
  - `name` (string, required): Category name
  - `description` (string, optional): Category description
  - `is_active` (bool, optional): Active status (default: true)
  - `parent_id` (int, optional): Parent category ID for subcategories
    - **Omit or set to null** for main categories
    - **Provide parent_id** for subcategories

#### Get All Categories
- **Endpoint:** `GET /api/v1/categories/`
- **Description:** Get all categories with optional filters
- **Query Parameters:**
  - `skip` (int, optional): Number of records to skip (default: 0)
  - `limit` (int, optional): Maximum number of records (default: 100, max: 1000)
  - `name` (string, optional): Search by category name (case-insensitive)
  - `is_main` (bool, optional): Filter main categories (true) or subcategories (false)
  - `is_active` (bool, optional): Filter by active status
- **Response:** List of categories

#### Get Main Categories Only
- **Endpoint:** `GET /api/v1/categories/main`
- **Description:** Get list of all main categories (categories with parent_id = null)
- **Query Parameters:**
  - `skip` (int, optional): Number of records to skip (default: 0)
  - `limit` (int, optional): Maximum number of records (default: 100, max: 1000)
  - `is_active` (bool, optional): Filter by active status
- **Response:** List of main categories

#### Get Subcategories by Parent ID
- **Endpoint:** `GET /api/v1/categories/subcategories/{parent_id}`
- **Description:** Get subcategories for a specific parent category
- **Path Parameters:**
  - `parent_id` (int, required): ID of the parent category
- **Query Parameters:**
  - `skip` (int, optional): Number of records to skip (default: 0)
  - `limit` (int, optional): Maximum number of records (default: 100, max: 1000)
  - `is_active` (bool, optional): Filter by active status
- **Response:** List of subcategories

#### Get Category by ID
- **Endpoint:** `GET /api/v1/categories/{category_id}`
- **Description:** Get detailed information about a specific category
- **Response:** Full category details

#### Update Category
- **Endpoint:** `PUT /api/v1/categories/{category_id}`
- **Description:** Update an existing category (main or sub)
- **Authentication:** Required
- **Request Body:**
  - `name` (string, optional): Category name
  - `description` (string, optional): Category description
  - `is_active` (bool, optional): Active status
  - `parent_id` (int, optional): Parent category ID (can change main to sub or vice versa)
- **Response:** Updated category details

#### Delete Category
- **Endpoint:** `DELETE /api/v1/categories/{category_id}`
- **Description:** Delete a category
  - If category has children (subcategories): Soft delete (marks as inactive)
  - If category has no children: Hard delete (removes from database)
- **Authentication:** Required
- **Response:** Success message

---

### 9. Skills Management

#### Get All Skills
- **Endpoint:** `GET /api/v1/skills/`
- **Description:** Get list of all skills
- **Authentication:** Required
- **Query Parameters:**
  - `name` (string, optional): Filter by name (partial match)
- **Response:** List of skills with:
  - id, name
  - created_at, updated_at
  - is_deleted status

#### Create Skill
- **Endpoint:** `POST /api/v1/skills/`
- **Description:** Create a new skill
- **Authentication:** Required
- **Request Body:**
  - `name` (string, required): Skill name
- **Response:** Created skill details

#### Update Skill
- **Endpoint:** `PATCH /api/v1/skills/{skill_id}`
- **Description:** Update a skill
- **Authentication:** Required
- **Request Body:**
  - `name` (string, optional): Skill name
- **Response:** Updated skill details

#### Delete Skill
- **Endpoint:** `DELETE /api/v1/skills/{skill_id}`
- **Description:** Delete a skill
- **Authentication:** Required
- **Response:** Success message

---

### 10. Locations Management

#### Get All Locations
- **Endpoint:** `GET /api/v1/locations/`
- **Description:** Get list of all locations
- **Authentication:** Required
- **Response:** List of locations with:
  - id, name, flag_image, code, phone_code
  - created_at, updated_at
  - is_deleted status

#### Get Location by ID
- **Endpoint:** `GET /api/v1/locations/{location_id}`
- **Description:** Get detailed information about a location
- **Authentication:** Required
- **Response:** Full location details

#### Create Location
- **Endpoint:** `POST /api/v1/locations/`
- **Description:** Create a new location
- **Authentication:** Required
- **Request Body (Form Data):**
  - `name` (string, required): Location name
  - `code` (string, required): Location code
  - `phone_code` (string, optional): Phone code
  - `flag_image` (file, optional): Flag image file
- **Response:** Created location details

#### Update Location
- **Endpoint:** `PATCH /api/v1/locations/{location_id}`
- **Description:** Update a location
- **Authentication:** Required
- **Request Body:**
  - `name` (string, optional): Location name
  - `code` (string, optional): Location code
  - `phone_code` (string, optional): Phone code
  - `flag_image` (string, optional): Flag image URL
- **Response:** Updated location details

#### Delete Location
- **Endpoint:** `DELETE /api/v1/locations/{location_id}`
- **Description:** Delete a location
- **Authentication:** Required
- **Response:** Success message

---

### 11. Certification Centers Management

#### Get All Certification Centers
- **Endpoint:** `GET /api/v1/certification-centers/`
- **Description:** Get all certification centers with optional search and pagination
- **Authentication:** Not required
- **Query Parameters:**
  - `skip` (int, optional): Number of records to skip (default: 0)
  - `limit` (int, optional): Maximum number of records (default: 100, max: 1000)
  - `search` (string, optional): Search by name
- **Response:** List of certification centers with:
  - id, name, icon
  - created_at, updated_at
  - is_deleted status

#### Get Certification Center by ID
- **Endpoint:** `GET /api/v1/certification-centers/{center_id}`
- **Description:** Get a specific certification center by ID
- **Authentication:** Not required
- **Response:** Full certification center details

#### Create Certification Center
- **Endpoint:** `POST /api/v1/certification-centers/`
- **Description:** Create a new certification center
- **Authentication:** Required
- **Request Body:**
  - `name` (string, required): Center name
  - `icon` (string, optional): Icon URL
- **Response:** Created certification center details

#### Update Certification Center
- **Endpoint:** `PUT /api/v1/certification-centers/{center_id}`
- **Description:** Update a certification center
- **Authentication:** Required
- **Request Body:**
  - `name` (string, optional): Center name
  - `icon` (string, optional): Icon URL
- **Response:** Updated certification center details

#### Delete Certification Center
- **Endpoint:** `DELETE /api/v1/certification-centers/{center_id}`
- **Description:** Delete a certification center (soft delete)
- **Authentication:** Required
- **Response:** Success message

---

### 12. Languages Management

#### Get All Languages
- **Endpoint:** `GET /api/v1/languages/`
- **Description:** Get list of all languages
- **Authentication:** Required
- **Response:** List of languages with:
  - id, name

#### Get Language by ID
- **Endpoint:** `GET /api/v1/languages/{language_id}`
- **Description:** Get detailed information about a language
- **Authentication:** Required
- **Response:** Full language details

#### Create Language
- **Endpoint:** `POST /api/v1/languages/`
- **Description:** Create a new language
- **Authentication:** Required
- **Request Body:**
  - `name` (string, required): Language name
- **Response:** Created language details

#### Update Language
- **Endpoint:** `PUT /api/v1/languages/{language_id}`
- **Description:** Update a language
- **Authentication:** Required
- **Request Body:**
  - `name` (string, optional): Language name
- **Response:** Updated language details

#### Delete Language
- **Endpoint:** `DELETE /api/v1/languages/{language_id}`
- **Description:** Delete a language
- **Authentication:** Not required (but should be added)
- **Response:** Success message

---

### 13. FAQ Management

#### Get All FAQs
- **Endpoint:** `GET /api/v1/faq/`
- **Description:** Get list of all FAQs
- **Authentication:** Not required
- **Response:** List of FAQs with:
  - id, question, answer
  - created_at, updated_at

#### Get FAQ by ID
- **Endpoint:** `GET /api/v1/faq/{faq_id}`
- **Description:** Get detailed information about an FAQ
- **Authentication:** Not required
- **Response:** Full FAQ details

#### Create FAQ
- **Endpoint:** `POST /api/v1/faq/`
- **Description:** Create a new FAQ
- **Authentication:** Not required (but should be added for admin)
- **Request Body:**
  - `question` (string, required): FAQ question
  - `answer` (string, required): FAQ answer
- **Response:** Created FAQ details

#### Update FAQ
- **Endpoint:** `PUT /api/v1/faq/{faq_id}`
- **Description:** Update an FAQ
- **Authentication:** Not required (but should be added for admin)
- **Request Body:**
  - `question` (string, optional): FAQ question
  - `answer` (string, optional): FAQ answer
- **Response:** Updated FAQ details

#### Delete FAQ
- **Endpoint:** `DELETE /api/v1/faq/{faq_id}`
- **Description:** Delete an FAQ
- **Authentication:** Not required (but should be added for admin)
- **Response:** Success message

---

### 14. Contact Us Management

#### Get All Contacts
- **Endpoint:** `GET /api/v1/contact-us/`
- **Description:** Get all contacts
- **Authentication:** Not required
- **Response:** List of contacts with:
  - id, name, email, subject, message
  - created_at, updated_at

#### Get Contact by ID
- **Endpoint:** `GET /api/v1/contact-us/{contact_id}`
- **Description:** Get contact by ID
- **Authentication:** Not required
- **Response:** Full contact details

#### Create Contact
- **Endpoint:** `POST /api/v1/contact-us/`
- **Description:** Create a new contact
- **Authentication:** Not required
- **Request Body:**
  - `name` (string, required): Contact name
  - `email` (string, required): Contact email
  - `subject` (string, required): Contact subject
  - `message` (string, required): Contact message
- **Response:** Created contact details

#### Update Contact
- **Endpoint:** `PUT /api/v1/contact-us/{contact_id}`
- **Description:** Update contact
- **Authentication:** Not required (but should be added for admin)
- **Request Body:**
  - `name` (string, optional): Contact name
  - `email` (string, optional): Contact email
  - `subject` (string, optional): Contact subject
  - `message` (string, optional): Contact message
- **Response:** Updated contact details

#### Delete Contact
- **Endpoint:** `DELETE /api/v1/contact-us/{contact_id}`
- **Description:** Delete contact
- **Authentication:** Not required (but should be added for admin)
- **Response:** Success message

---

### 15. Education Facilities Management

#### Get All Education Facilities
- **Endpoint:** `GET /api/v1/education-facilities`
- **Description:** Get all education facilities with optional search and filtering
- **Authentication:** Not required
- **Query Parameters:**
  - `skip` (int, optional): Number of records to skip (default: 0)
  - `limit` (int, optional): Maximum number of records (default: 100, max: 1000)
  - `search` (string, optional): Search by facility name
  - `country` (string, optional): Filter by country
- **Response:** List of education facilities with:
  - id, name, icon, country
  - created_at, updated_at
  - is_deleted status

#### Get Education Facility by ID
- **Endpoint:** `GET /api/v1/education-facilities/{facility_id}`
- **Description:** Get education facility by ID
- **Authentication:** Not required
- **Response:** Full education facility details

#### Create Education Facility
- **Endpoint:** `POST /api/v1/education-facilities`
- **Description:** Create a new education facility
- **Authentication:** Required
- **Query Parameters:**
  - `name` (string, required): Education facility name
  - `icon` (string, optional): Icon URL or path
  - `country` (string, optional): Country name
- **Response:** Created education facility details

#### Update Education Facility
- **Endpoint:** `PUT /api/v1/education-facilities/{facility_id}`
- **Description:** Update education facility
- **Authentication:** Required
- **Request Body:**
  - `name` (string, optional): Facility name
  - `icon` (string, optional): Icon URL
  - `country` (string, optional): Country name
- **Response:** Updated education facility details

#### Delete Education Facility
- **Endpoint:** `DELETE /api/v1/education-facilities/{facility_id}`
- **Description:** Delete education facility (soft delete)
- **Authentication:** Required
- **Response:** Success message

#### Search Education Facilities (Autocomplete)
- **Endpoint:** `GET /api/v1/education-facilities/search/autocomplete`
- **Description:** Search education facilities for autocomplete (returns only names)
- **Authentication:** Not required
- **Query Parameters:**
  - `q` (string, required): Search query (minimum 1 character)
  - `limit` (int, optional): Maximum results (default: 10, max: 50)
- **Response:** List of facility names



## Notes

1. **Authentication:** All endpoints require Bearer token authentication. Admin-specific endpoints require admin role check.

2. **Pagination:** Most list endpoints support pagination with `page`/`skip` and `limit`/`size` query parameters.

3. **Filtering:** Most endpoints support various filters to narrow down results.

4. **User Creation:** Admin **cannot create users** - users can only be viewed, blocked/unblocked, and verified.

5. **Soft Delete:** Most delete operations are soft deletes (setting `is_deleted` flag to true).

6. **Response Format:** All responses follow a consistent format:
   ```json
   {
     "status": "success",
     "msg": "Success message",
     "data": { ... }
   }
   ```

7. **Error Handling:** All endpoints return appropriate HTTP status codes and error messages.

8. **Permissions:** Admin has access to view all data and manage certain resources (Locations, Skills, Categories, etc.), but cannot create users.
