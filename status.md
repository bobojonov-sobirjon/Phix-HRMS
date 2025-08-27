# Phix HRMS API Status Documentation

Bu hujjat Phix HRMS API da qanday status va xatoliklar qaytarilishini tushuntiradi.

## Umumiy Response Strukturasi

### 1. Success Response (Muvaffaqiyatli)

```json
{
  "status": "success",
  "msg": "Ma'lumot muvaffaqiyatli saqlandi",
  "data": {
    // Ma'lumotlar bu yerda
  }
}
```

### 2. Error Response (Xatolik)

```json
{
  "status": "error",
  "msg": "Xatolik xabari"
}
```

### 3. Paginated Response (Sahifalangan ma'lumot)

```json
{
  "status": "success",
  "msg": "Data retrieved successfully",
  "data": [
    // Ma'lumotlar ro'yxati
  ],
  "total": 100,
  "page": 1,
  "per_page": 10,
  "total_pages": 10
}
```

## HTTP Status Kodlari

### 2xx - Muvaffaqiyatli

- **200 OK** - Ma'lumot muvaffaqiyatli qaytarildi
- **201 Created** - Yangi ma'lumot yaratildi
- **204 No Content** - Ma'lumot o'chirildi (response body yo'q)

### 4xx - Client Xatoliklari

- **400 Bad Request** - Noto'g'ri so'rov
- **401 Unauthorized** - Avtorizatsiya talab qilinadi
- **403 Forbidden** - Ruxsat yo'q
- **404 Not Found** - Ma'lumot topilmadi
- **422 Unprocessable Entity** - Ma'lumot validatsiyadan o'tmadi

### 5xx - Server Xatoliklari

- **500 Internal Server Error** - Ichki server xatoligi

## API Endpoint Response Namunalari

### Authentication (Avtorizatsiya)

#### POST /api/v1/auth/register
```json
// Success
{
  "status": "success",
  "msg": "OTP email ga yuborildi"
}

// Error
{
  "status": "error",
  "msg": "Bu email bilan foydalanuvchi mavjud"
}
```

#### POST /api/v1/auth/login
```json
// Success
{
  "status": "success",
  "msg": "Muvaffaqiyatli kirish",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "Foydalanuvchi Ismi"
    }
  }
}

// Error
{
  "status": "error",
  "msg": "Noto'g'ri email yoki parol"
}
```

### Gig Jobs (Ishlar)

#### GET /api/v1/gig-jobs/
```json
// Success
{
  "status": "success",
  "msg": "Data retrieved successfully",
  "data": [
    {
      "id": 1,
      "title": "Web Developer",
      "description": "Frontend va backend dasturlash",
      "min_salary": 1000,
      "max_salary": 3000,
      "location": "Tashkent",
      "status": "active"
    }
  ],
  "total": 25,
  "page": 1,
  "per_page": 10,
  "total_pages": 3
}
```

#### POST /api/v1/gig-jobs/gig-job
```json
// Success (201 Created)
{
  "id": 1,
  "title": "Web Developer",
  "description": "Frontend va backend dasturlash",
  "min_salary": 1000,
  "max_salary": 3000,
  "location": "Tashkent",
  "status": "active",
  "author_id": 1,
  "created_at": "2024-01-15T10:30:00Z"
}

// Error (400 Bad Request)
{
  "status": "error",
  "msg": "Minimum salary must be less than maximum salary"
}
```

#### PUT /api/v1/gig-jobs/{id}
```json
// Success
{
  "id": 1,
  "title": "Updated Web Developer",
  "description": "Yangilangan tavsif",
  "min_salary": 1200,
  "max_salary": 3500,
  "location": "Tashkent",
  "status": "active"
}

// Error (404 Not Found)
{
  "status": "error",
  "msg": "Gig job not found or you don't have permission to update it"
}
```

#### DELETE /api/v1/gig-jobs/{id}
```json
// Success (204 No Content)
// Response body yo'q

// Error (404 Not Found)
{
  "status": "error",
  "msg": "Gig job not found or you don't have permission to delete it"
}
```

### Profile (Profil)

#### GET /api/v1/profile/me
```json
// Success
{
  "status": "success",
  "msg": "Profile retrieved successfully",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Foydalanuvchi Ismi",
    "phone": "+998901234567",
    "avatar": "/static/avatars/1_avatar.jpg",
    "bio": "Dasturchi",
    "location": "Tashkent",
    "skills": ["Python", "FastAPI", "React"],
    "education": [...],
    "experience": [...]
  }
}

// Error (401 Unauthorized)
{
  "status": "error",
  "msg": "Authorization header required"
}
```

## Xatolik Xabarlari

### Umumiy Xatoliklar

| Xatolik | HTTP Status | Xabar |
|---------|-------------|-------|
| Avtorizatsiya yo'q | 401 | "Authorization header required" |
| Noto'g'ri token | 401 | "Invalid token" |
| Foydalanuvchi topilmadi | 401 | "User not found" |
| Ma'lumot topilmadi | 404 | "Not found" |
| Ruxsat yo'q | 403 | "Forbidden" |
| Noto'g'ri ma'lumot | 400 | "Bad request" |
| Validatsiya xatosi | 422 | "Validation error" |

### Authentication Xatoliklari

| Xatolik | HTTP Status | Xabar |
|---------|-------------|-------|
| Email mavjud | 400 | "User with this email already exists" |
| Telefon mavjud | 400 | "User with this phone number already exists" |
| Noto'g'ri parol | 400 | "Invalid password" |
| OTP noto'g'ri | 400 | "Invalid OTP" |
| OTP muddati tugagan | 400 | "OTP expired" |

### Gig Jobs Xatoliklari

| Xatolik | HTTP Status | Xabar |
|---------|-------------|-------|
| Ish topilmadi | 404 | "Gig job not found" |
| Ruxsat yo'q | 404 | "You don't have permission" |
| Noto'g'ri maosh | 400 | "Minimum salary must be less than maximum salary" |
| Majburiy maydonlar | 422 | "Field required" |

## Response Headers

### Umumiy Headers

```
Content-Type: application/json
Content-Length: 1234
```

### Authentication Headers

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Pagination (Sahifalash)

### Query Parameters

- `page` - Sahifa raqami (default: 1)
- `size` - Sahifadagi elementlar soni (default: 10, max: 100)

### Pagination Response

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10,
  "has_next": true,
  "has_previous": false
}
```

## Ma'lumot Validatsiyasi

### Required Fields (Majburiy maydonlar)

```json
{
  "status": "error",
  "msg": "Field required",
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "Field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Field Validation (Maydon validatsiyasi)

```json
{
  "status": "error",
  "msg": "Validation error",
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

## Testing (Sinab ko'rish)

### cURL orqali test qilish

```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Gig jobs olish
curl -X GET "http://localhost:8000/api/v1/gig-jobs/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Yangi gig job yaratish
curl -X POST "http://localhost:8000/api/v1/gig-jobs/gig-job" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Job",
    "description": "Test description",
    "min_salary": 1000,
    "max_salary": 2000,
    "location": "Tashkent"
  }'
```

## Xatoliklarni Qayta Ishlash

### Frontend da xatoliklarni ushlash

```javascript
try {
  const response = await fetch('/api/v1/gig-jobs/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  if (data.status === 'success') {
    // Muvaffaqiyatli
    console.log(data.data);
  } else {
    // Xatolik
    console.error(data.msg);
  }
} catch (error) {
  console.error('Network error:', error);
}
```

### Error Handling (Xatoliklarni ushlash)

```javascript
const handleApiError = (error) => {
  if (error.status === 'error') {
    // API xatoligi
    showErrorMessage(error.msg);
  } else if (error.status === 401) {
    // Avtorizatsiya xatoligi
    redirectToLogin();
  } else if (error.status === 404) {
    // Ma'lumot topilmadi
    showNotFoundMessage();
  } else {
    // Boshqa xatoliklar
    showGenericErrorMessage();
  }
};
```

## Eslatmalar

1. **Barcha API endpoint lar** `/api/v1/` prefiksiga ega
2. **Authentication** uchun `Authorization: Bearer TOKEN` header talab qilinadi
3. **Success response** da har doim `status: "success"` bo'ladi
4. **Error response** da har doim `status: "error"` bo'ladi
5. **Pagination** barcha ro'yxat endpoint larida mavjud
6. **File upload** uchun `multipart/form-data` ishlatiladi
7. **Date format** ISO 8601 standartida (`2024-01-15T10:30:00Z`)
