# 🔥 Firebase Authentication Setup (Without SDK)

## ✅ O'zgartirilgan Fayllar

1. **`app/core/config.py`** - Firebase credentials loader qo'shildi
2. **`app/utils/social_auth.py`** - Manual JWT verification (SDK kerak emas!)
3. **`requirements.txt`** - PyJWT dependency qo'shildi

## 🎯 Nima Qildik?

### ❌ Eski Usul (Firebase Admin SDK)
```python
# Firebase Admin SDK kerak edi (800KB+ library)
import firebase_admin
decoded = auth.verify_id_token(token)
```

### ✅ Yangi Usul (Manual JWT Verification)
```python
# Faqat PyJWT va requests (yengil!)
import jwt
decoded = jwt.decode(token, public_key, algorithms=['RS256'])
```

## 📦 Installation

### 1. Install Dependencies

```bash
pip install PyJWT==2.8.0 cryptography==45.0.5
```

Yoki:
```bash
pip install -r requirements.txt
```

### 2. Firebase Credentials Setup

#### Variant A: JSON File (Tavsiya qilinadi)

1. **Firebase Console'dan JSON download qiling:**
   - https://console.firebase.google.com/
   - Project Settings → Service Accounts
   - Generate New Private Key → Download JSON

2. **JSON faylni project root'ga qo'ying:**
   ```
   D:\Projects\Mobile Backend APPS\Phix-Hrms\firebase-credentials.json
   ```

3. **`.env` faylga qo'shing:**
   ```bash
   # Firebase Configuration (JSON File)
   FIREBASE_CREDENTIALS_JSON=firebase-credentials.json
   PROJECT_ID=phix-864d2
   ```

#### Variant B: Environment Variables (Hozirgi)

Hozirgi `.env` faylingiz allaqachon to'g'ri:
```bash
TYPE=service_account
PROJECT_ID=phix-864d2
PRIVATE_KEY_ID=1f428184f0a04963ed4371446ef828d49976ed93
PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n..."
CLIENT_EMAIL=firebase-adminsdk-fbsvc@phix-864d2.iam.gserviceaccount.com
CLIENT_ID=109798791403642197401
...
```

## 🚀 Qanday Ishlaydi?

### 1. Frontend → Firebase ID Token Oladi

```javascript
// Firebase Authentication
import { signInWithPopup, GoogleAuthProvider } from 'firebase/auth';

const provider = new GoogleAuthProvider();
const result = await signInWithPopup(auth, provider);

// ✅ Firebase ID Token (JWT format)
const firebaseIdToken = await result.user.getIdToken();

console.log('Token:', firebaseIdToken);
// Example: eyJhbGciOiJSUzI1NiIsImtpZCI6ImY3NTh...
```

### 2. Backend → Token'ni Verify Qiladi (SDK siz!)

```python
# app/utils/social_auth.py

# 1. Google'dan public keys oladi
public_keys = requests.get(
    "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
).json()

# 2. Token header'dan kid (key ID) oladi
header = jwt.get_unverified_header(id_token)
kid = header['kid']

# 3. To'g'ri public key bilan verify qiladi
decoded = jwt.decode(
    id_token,
    public_keys[kid],
    algorithms=['RS256'],
    audience='phix-864d2',  # Your project ID
    issuer='https://securetoken.google.com/phix-864d2'
)

# 4. User info extract qiladi
user_info = {
    "id": decoded["user_id"],
    "email": decoded["email"],
    "name": decoded["name"],
    "picture": decoded["picture"]
}
```

## 🧪 Test Qilish

### 1. Server'ni Ishga Tushiring

```bash
python run_server.py
```

Console'da:
```
✅ Firebase credentials loaded from environment variables
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Swagger'da Test Qiling

1. http://127.0.0.1:8000/docs ga o'ting
2. `/api/v1/auth/social-login` endpoint'ni oching
3. Execute tugmasini bosing

**Request Body:**
```json
{
  "provider": "google",
  "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImY3NThlNTYzYzBiNjRhNzVmN2UzZGFlNDk0ZDM5NTk1YzE0MGVmOTMiLCJ0eXAiOiJKV1QifQ..."
}
```

**Response (Success):**
```json
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

### 3. Console Loglar

**Success:**
```
✅ Firebase token verified successfully for user: harrystone578@gmail.com
```

**Error:**
```
❌ Firebase token has expired
❌ Invalid Firebase token: Signature verification failed
❌ Public key not found for kid: abc123
```

## 🔧 Troubleshooting

### Error: "Invalid Firebase token"

**Sabab 1:** Token expired (1 soatdan oshgan)

**Yechim:** Frontend'dan fresh token oling:
```javascript
const token = await user.getIdToken(true); // force refresh
```

**Sabab 2:** Project ID noto'g'ri

**Yechim:** `.env` faylda `PROJECT_ID` to'g'riligini tekshiring:
```bash
PROJECT_ID=phix-864d2  # Must match Firebase console
```

**Sabab 3:** Token format noto'g'ri

**Yechim:** `getIdToken()` ishlatilganini tekshiring (access token emas!)

### Error: "Public key not found"

**Sabab:** Google'ning public keys'i refresh bo'lmagan

**Yechim:** Server restart qiling yoki 1-2 daqiqa kuting

### Error: "Module 'jwt' has no attribute 'decode'"

**Sabab:** PyJWT install qilinmagan

**Yechim:**
```bash
pip install PyJWT==2.8.0 cryptography==45.0.5
```

## 📊 Token Decode Example

Your token:
```
eyJhbGciOiJSUzI1NiIsImtpZCI6ImY3NThlNTYzYzBiNjRhNzVmN2UzZGFlNDk0ZDM5NTk1YzE0MGVmOTMiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiSGFycnkgU3RvbmUiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSWFFamdmaU02aWdDdzNCVjBub0lHOUljdmwxRG8yNi1fc2tnYWlTaTVFellGTWFRPXM5Ni1jIiwiaXNzIjoiaHR0cHM6Ly9zZWN1cmV0b2tlbi5nb29nbGUuY29tL3BoaXgtODY0ZDIiLCJhdWQiOiJwaGl4LTg2NGQyIiwiYXV0aF90aW1lIjoxNzcwNDAzNzQ1LCJ1c2VyX2lkIjoiMGVXVkRUR09vWWFQOHlqVUNXSmxsa1dqU2JvMSIsInN1YiI6IjBlV1ZEVEdPb1lhUDh5alVDV0psbGtXalNibzEiLCJpYXQiOjE3NzA0MDM3NDYsImV4cCI6MTc3MDQwNzM0NiwiZW1haWwiOiJoYXJyeXN0b25lNTc4QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7Imdvb2dsZS5jb20iOlsiMTEyMDg0MDMyMjQ4OTcwMzcyNTg3Il0sImVtYWlsIjpbImhhcnJ5c3RvbmU1NzhAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.wCC-RJqAFN-YiG52YVF4Z25cYV8wdUDfqtG7KHpeXapxxPRM4XHj6aiXtwyZKvZtnz0b9ts8kutmKESh0wurb3ahLZarK8aHg3bha15b4VNvdw0S7U59QMbt4hQHiFz985p9CxJERhntcVaov-33qdQEakON9ndaKfj0cqZn7ZKZpy5FZzHJdKQn32OODszGk9Juk8UAiUFQd0mzHUQgq4FDhf-bRIn-6w73l2jWuXzldyCcqyTKnRRkyRjvrimHjoe9eIJpNZGanrRuf-uXVq9WkpWj7pU_fXAvjVNAgDFnDLjrLjIlivwWOJcTAXmg0oP4oQ6wmkkHIMDoU_wU9w
```

Decoded payload:
```json
{
  "name": "Harry Stone",
  "picture": "https://lh3.googleusercontent.com/a/ACg8ocIaEjgfiM6igCw3BV0noIG9Icvl1Do26-_skgaiSi5EzYFMaQ=s96-c",
  "iss": "https://securetoken.google.com/phix-864d2",
  "aud": "phix-864d2",
  "auth_time": 1770403745,
  "user_id": "0eWVDTGOoYaP8yjUCWJllkWjSbo1",
  "sub": "0eWVDTGOoYaP8yjUCWJllkWjSbo1",
  "iat": 1770403746,
  "exp": 1770407346,
  "email": "harrystone578@gmail.com",
  "email_verified": true,
  "firebase": {
    "identities": {
      "google.com": ["112084032248970372587"],
      "email": ["harrystone578@gmail.com"]
    },
    "sign_in_provider": "google.com"
  }
}
```

Backend extracts:
- `user_id`: `0eWVDTGOoYaP8yjUCWJllkWjSbo1`
- `email`: `harrystone578@gmail.com`
- `name`: `Harry Stone`
- `picture`: `https://lh3.googleusercontent.com/...`
- `provider`: `google.com`

## ✅ Advantages

1. **No SDK Required**: Faqat PyJWT va requests
2. **Lightweight**: 800KB SDK o'rniga 100KB
3. **Fast**: Direct JWT verification
4. **Flexible**: JSON file yoki environment variables
5. **Secure**: Google's public keys bilan signature verification

## 🎯 Flow

```
Frontend
   ↓
Firebase Auth (Google/Facebook/Apple)
   ↓
Firebase ID Token (JWT)
   ↓
Backend API
   ↓
Fetch Google Public Keys
   ↓
Verify JWT Signature
   ↓
Extract User Info
   ↓
Create/Update User in DB
   ↓
Generate JWT Access Token
   ↓
Return to Frontend
   ↓
Login Success ✅
```

## 📝 Notes

- Token expires in 1 hour (3600 seconds)
- Frontend should refresh token automatically
- Public keys cache bo'ladi (performance uchun)
- All providers (Google, Facebook, Apple) bir xil flow

---

**Status**: ✅ Ready to use!
**Updated**: 2026-01-23
**Tested**: ✅ Working without Firebase Admin SDK
