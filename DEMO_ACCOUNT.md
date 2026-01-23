# Demo Account Setup

Bu demo account test uchun mo'ljallangan. Barcha credentials va OTP kodlar o'zgarmas.

## 🚀 Setup

Demo accountni yaratish uchun quyidagi commandni ishga tushiring:

```bash
python setup_demo_account.py
```

Yoki to'g'ridan-to'g'ri module sifatida:

```bash
python -m app.utils.demo_account_setup
```

## 🔑 Demo Account Credentials

### User Credentials
- **Email**: `cheker@test.com`
- **Password**: `12345678@#hello_phix`

### Permanent OTP Code
- **OTP**: `12345` (5 xonali)
- **Expires**: Hech qachon (10 yil)
- **Types**: 
  - `password_reset` - Parolni tiklash uchun
  - `email_verification` - Email tasdiqlash uchun
  - `corporate_profile` - Corporate profile ochish uchun

## 📋 Qanday Ishlatish

### 1. Login (Token Olish)

**Swagger UI**da `/api/v1/auth/login` endpoint orqali:

```json
{
  "email": "cheker@test.com",
  "password": "12345678@#hello_phix"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### 2. Forgot Password

**Step 1**: `/api/v1/auth/forgot-password` - OTP so'rash
```json
{
  "email": "cheker@test.com"
}
```

**Step 2**: `/api/v1/auth/verify-otp` - OTP tasdiqlash
```json
{
  "email": "cheker@test.com",
  "otp_code": "12345"
}
```

**Step 3**: `/api/v1/auth/reset-password` - Yangi parol o'rnatish
```json
{
  "email": "cheker@test.com",
  "otp_code": "12345",
  "new_password": "yangi_parol"
}
```

### 3. Corporate Profile Ochish

Agar corporate profile ochishda OTP kerak bo'lsa:

```json
{
  "email": "cheker@test.com",
  "otp_code": "12345",
  "company_name": "Test Company",
  ...
}
```

## ✅ Verify Setup

Demo account to'g'ri yaratilganini tekshirish uchun:

```python
from app.utils.demo_account_setup import verify_demo_account

if verify_demo_account():
    print("✅ Demo account ready!")
else:
    print("❌ Demo account not found!")
```

## 🔄 Re-setup

Agar demo account buzilgan bo'lsa yoki qayta yaratish kerak bo'lsa, shunchaki qayta ishga tushiring:

```bash
python setup_demo_account.py
```

Script:
- Mavjud demo user'ni topadi va yangilamaydi
- Barcha OTP kodlarni o'chiradi va qayta yaratadi
- Hamma narsa fresh holda bo'ladi

## 🎯 Testing Checklist

- [ ] Login qilish (`cheker@test.com`)
- [ ] Token olish va saqlash
- [ ] Forgot password flow test qilish
- [ ] OTP `12345` ishlashini tekshirish
- [ ] Corporate profile ochishda OTP ishlatish
- [ ] Email verification test qilish

## ⚠️ Important Notes

1. **Bu faqat test uchun!** Production'da ishlatmang.
2. **OTP hech qachon expire bo'lmaydi** - 10 yil muddatli.
3. **Har doim bir xil OTP** - `12345`.
4. **Email haqiqiy emas** - real emailga hech narsa bormaydi.
5. **Clean code** - barcha funksiyalar document qilingan.

## 📁 Files

- `setup_demo_account.py` - Root papkada, CMD dan ishga tushirish uchun
- `app/utils/demo_account_setup.py` - Asosiy setup module
- `DEMO_ACCOUNT.md` - Bu hujjat

## 🛠️ Troubleshooting

**Agar xatolik chiqsa:**

1. Database ulanishini tekshiring
2. Migrations to'g'ri qo'llanganini tekshiring:
   ```bash
   alembic upgrade head
   ```
3. `.env` faylda settings to'g'ri bo'lishini tekshiring
4. Script'ni qayta ishga tushiring

**Error: "Demo user already exists"**
- Bu normal - user allaqachon yaratilgan
- Script avtomatik existing user'ni ishlatadi

**Error: "OTP creation failed"**
- Eski OTP'larni o'chirish kerak bo'lishi mumkin
- Script avtomatik o'chiradi va qayta yaratadi
