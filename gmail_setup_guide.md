# Gmail Setup Guide for Server

## Step 1: Enable 2-Factor Authentication on Gmail

1. Go to your Google Account settings
2. Click on "Security"
3. Enable "2-Step Verification"

## Step 2: Generate App Password

1. Go to your Google Account settings
2. Click on "Security"
3. Click on "App passwords" (under 2-Step Verification)
4. Select "Mail" and "Other (Custom name)"
5. Enter a name like "Phix HRMS Server"
6. Click "Generate"
7. Copy the 16-character password (it looks like: xxxx xxxx xxxx xxxx)

## Step 3: Update Your .env File

On your server, edit your `.env` file:

```bash
# SSH into your server
ssh root@your-server-ip

# Edit the .env file
nano .env

# Update these lines:
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-gmail@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # Your App Password (16 characters)
```

## Step 4: Test Gmail Connection

Run this test to see if Gmail works:

```bash
python3 test_gmail_connection.py
```

## Step 5: If Still Blocked

If your cloud provider is still blocking SMTP, you have these options:

1. **Contact your cloud provider** to unblock ports 587/465
2. **Use a different cloud provider** that allows SMTP
3. **Use a VPS provider** that doesn't block SMTP
4. **Use a transactional email service** (SendGrid, Mailgun, etc.)

## Common Issues:

- **"Invalid credentials"**: Make sure you're using App Password, not regular password
- **"Network unreachable"**: Your cloud provider is blocking SMTP ports
- **"Authentication failed"**: Check your App Password is correct 