# 🔥 Firebase Authentication Test Guide

## ✅ O'zgartirilgan Fayllar

### 1. `app/utils/social_auth.py`
- Firebase Admin SDK integratsiyasi qo'shildi
- `verify_social_token()` endi Firebase ID token'ni verify qiladi
- Barcha provider'lar (Google, Facebook, Apple) Firebase orqali ishlaydi

## 🚀 Qanday Ishlatish

### Frontend (Flutter/React Native/Web)

```javascript
// Firebase Authentication orqali login
import { signInWithPopup, GoogleAuthProvider } from 'firebase/auth';

const provider = new GoogleAuthProvider();
const result = await signInWithPopup(auth, provider);

// ✅ Firebase ID Token olish
const firebaseIdToken = await result.user.getIdToken();

// ✅ Backend'ga yuborish
const response = await fetch('http://127.0.0.1:8000/api/v1/auth/social-login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    provider: 'google',  // yoki 'facebook', 'apple'
    access_token: firebaseIdToken  // ✅ Bu Firebase ID token
  })
});

const data = await response.json();
console.log('✅ Login successful:', data);
```

### Backend (FastAPI)

```python
# POST /api/v1/auth/social-login
{
  "provider": "google",
  "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6..." # Firebase ID Token
}

# ✅ Response:
{
  "status": "success",
  "msg": "Social login successful",
  "data": {
    "token": {
      "access_token": "eyJhbGc...",
      "expires_in": 31536000
    },
    "refresh_token": "eyJhbGc..."
  }
}
```

## 🧪 Test Qilish

### 1. Server'ni Restart Qiling

```bash
# Stop old server (Ctrl+C)
# Start new server
python run_server.py
# yoki
uvicorn app.main:app --reload
```

### 2. Console'da Loglarni Kuzating

Server start bo'lganda ko'rishingiz kerak:
```
✅ Firebase Admin SDK initialized successfully
```

### 3. Frontend'dan Login Qiling

Firebase Authentication orqali Google sign-in qiling va console'da:
```
✅ Firebase token verified successfully for user: user@gmail.com
```

### 4. Agar Xato Bo'lsa

```
❌ Invalid Firebase ID token
❌ Expired Firebase ID token
❌ Firebase Admin SDK initialization failed
```

## 🔧 Troubleshooting

### Error: "Firebase Admin SDK initialization failed"

**Sabab:** `.env` faylda Firebase credentials noto'g'ri

**Yechim:**
1. `.env` faylni tekshiring:
   - `PROJECT_ID` to'g'ri bo'lishi kerak
   - `PRIVATE_KEY` to'g'ri format bo'lishi kerak
   - `CLIENT_EMAIL` to'g'ri bo'lishi kerak

2. PRIVATE_KEY formatini tekshiring:
```bash
PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n"
```

### Error: "Invalid Firebase ID token"

**Sabab:** Frontend noto'g'ri token yuborayapti

**Yechim:**
1. Frontend'da `getIdToken()` ishlatilganini tekshiring (access token emas!)
2. Token fresh bo'lishini tekshiring (expired bo'lmasin)
3. Firebase project ID frontend va backend'da bir xil bo'lishi kerak

### Error: "Module 'firebase_admin' not found"

**Sabab:** Package install qilinmagan

**Yechim:**
```bash
pip install firebase-admin==6.5.0
```

## 📝 Environment Variables

`.env` faylda bo'lishi kerak:

```bash
# Firebase Admin SDK
TYPE=service_account
PROJECT_ID=phix-864d2
PRIVATE_KEY_ID=1f428184f0a04963ed4371446ef828d49976ed93
PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n"
CLIENT_EMAIL=firebase-adminsdk-fbsvc@phix-864d2.iam.gserviceaccount.com
CLIENT_ID=109798791403642197401
AUTH_URI=https://accounts.google.com/o/oauth2/auth
TOKEN_URI=https://oauth2.googleapis.com/token
AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
CLIENT_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40phix-864d2.iam.gserviceaccount.com
UNIVERSE_DOMAIN=googleapis.com
```

## 🎯 Provider'lar

### Google Sign-In (Firebase Auth)
```javascript
const provider = new GoogleAuthProvider();
const result = await signInWithPopup(auth, provider);
const token = await result.user.getIdToken();
// provider: "google"
```

### Facebook Login (Firebase Auth)
```javascript
const provider = new FacebookAuthProvider();
const result = await signInWithPopup(auth, provider);
const token = await result.user.getIdToken();
// provider: "facebook"
```

### Apple Sign-In (Firebase Auth)
```javascript
const provider = new OAuthProvider('apple.com');
const result = await signInWithPopup(auth, provider);
const token = await result.user.getIdToken();
// provider: "apple"
```

## ✅ Advantages

1. **Xavfsizlik**: Firebase Admin SDK server-side token verification
2. **Yagona System**: Barcha provider'lar bir xil flow
3. **Token Management**: Firebase token expiry va refresh
4. **User Info**: Email, name, picture avtomatik
5. **Multi-Provider**: Google, Facebook, Apple - barchasi Firebase orqali

## 🔄 Flow Diagrammasi

```
User
 ↓
Frontend (Firebase Auth)
 ↓
Google/Facebook/Apple OAuth
 ↓
Firebase Authentication
 ↓
Firebase ID Token
 ↓
Backend API (/social-login)
 ↓
Firebase Admin SDK (verify_id_token)
 ↓
User Info Extracted
 ↓
Create/Update User in DB
 ↓
Generate JWT Access Token
 ↓
Return to Frontend
 ↓
User Logged In ✅
```

## 📞 Support

Agar muammo bo'lsa:
1. Console loglarni tekshiring
2. `.env` faylni to'g'rilang
3. Firebase project settings'ni tekshiring
4. Server'ni restart qiling

---

**Status**: ✅ Ready to test!
**Updated**: 2026-01-23
