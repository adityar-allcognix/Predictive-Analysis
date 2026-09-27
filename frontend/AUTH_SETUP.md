# Authentication Setup Guide

## Overview
This application uses NextAuth.js for authentication with two methods:
1. **Google OAuth** - Sign in with Google
2. **Email/Password** - Traditional credentials-based authentication

## Quick Start (Demo Mode)

The application is pre-configured with demo credentials:
- **Email**: demo@allcognix.com
- **Password**: demo123

You can start the application and test authentication immediately without any additional setup.

## Environment Variables

The `.env.local` file has been created with the following variables:

```env
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key-change-this-in-production
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Required Setup:

1. **NEXTAUTH_SECRET**: Generate a secure random string
   ```bash
   openssl rand -base64 32
   ```
   Replace `your-secret-key-change-this-in-production` with the generated value.

2. **NEXTAUTH_URL**: 
   - Development: `http://localhost:3000`
   - Production: Your actual domain (e.g., `https://allcognix.com`)

## Google OAuth Setup (Optional)

To enable Google Sign-In, follow these steps:

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google+ API**

### 2. Configure OAuth Consent Screen

1. Navigate to **APIs & Services** → **OAuth consent screen**
2. Choose **External** user type (or Internal for Google Workspace)
3. Fill in the required information:
   - App name: **Allcognix**
   - User support email: Your email
   - Developer contact email: Your email
4. Add scopes (select the following):
   - `userinfo.email`
   - `userinfo.profile`
5. Add test users if using External type
6. Save and continue

### 3. Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth 2.0 Client ID**
3. Select **Web application**
4. Configure:
   - Name: **Allcognix Web Client**
   - Authorized JavaScript origins:
     - `http://localhost:3000`
     - `http://localhost:3001` (if using alternative port)
   - Authorized redirect URIs:
     - `http://localhost:3000/api/auth/callback/google`
     - For production: `https://yourdomain.com/api/auth/callback/google`
5. Click **Create**

### 4. Update Environment Variables

Copy the **Client ID** and **Client Secret** from the credentials page and update your `.env.local`:

```env
GOOGLE_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-actual-client-secret
```

### 5. Restart the Development Server

```bash
npm run dev
```

## Features

### Authentication Pages

- **Sign In**: `/auth/signin` - Login with Google or email/password
- **Sign Up**: `/auth/signup` - Create new account (currently demo mode)

### Protected Routes

The main dashboard (`/`) is protected and requires authentication. Unauthenticated users are automatically redirected to the sign-in page.

### User Menu

Once authenticated, users can:
- View their profile information
- Sign out from the application

## Production Considerations

### Database Integration

The current implementation uses mock credentials for demo purposes. For production:

1. **Set up a database** (PostgreSQL, MySQL, MongoDB, etc.)
2. **Install Prisma** (already in dependencies):
   ```bash
   npx prisma init
   ```
3. **Update the Prisma schema** (see `prisma/schema.prisma` example below)
4. **Update the credentials provider** in `/app/api/auth/[...nextauth]/route.ts` to query your database

### Example Prisma Schema

```prisma
model User {
  id            String    @id @default(cuid())
  name          String?
  email         String?   @unique
  emailVerified DateTime?
  image         String?
  password      String?
  accounts      Account[]
  sessions      Session[]
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
}

model Account {
  id                String  @id @default(cuid())
  userId            String
  type              String
  provider          String
  providerAccountId String
  refresh_token     String?
  access_token      String?
  expires_at        Int?
  token_type        String?
  scope             String?
  id_token          String?
  session_state     String?
  user              User    @relation(fields: [userId], references: [id], onDelete: Cascade)
  @@unique([provider, providerAccountId])
}

model Session {
  id           String   @id @default(cuid())
  sessionToken String   @unique
  userId       String
  expires      DateTime
  user         User     @relation(fields: [userId], references: [id], onDelete: Cascade)
}
```

### Security Best Practices

1. **Use strong NEXTAUTH_SECRET** - Never commit this to version control
2. **Enable HTTPS in production** - Required for secure cookies
3. **Implement rate limiting** - Prevent brute force attacks
4. **Add email verification** - Verify user email addresses
5. **Implement password reset** - Allow users to recover accounts
6. **Use secure password hashing** - bcrypt with sufficient rounds (already implemented)

## Troubleshooting

### Google OAuth Not Working

- Verify redirect URIs match exactly (including http/https)
- Check that Google+ API is enabled
- Ensure credentials are correctly set in `.env.local`
- Restart the development server after changing environment variables

### Session Not Persisting

- Clear browser cookies
- Check NEXTAUTH_SECRET is set
- Verify NEXTAUTH_URL matches your actual URL

### Demo Login Not Working

- Use exact credentials: `demo@allcognix.com` / `demo123`
- Check console for error messages
- Ensure bcryptjs is installed: `npm install bcryptjs`

## Support

For issues or questions, please refer to:
- [NextAuth.js Documentation](https://next-auth.js.org/)
- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
