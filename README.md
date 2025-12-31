# Smart Job - FastAPI Backend

A comprehensive Job Board backend built with **FastAPI** and **Supabase**, featuring role-based authentication, job management, intelligent application tracking, and AI-powered candidate screening.

## 🚀 Features

### Authentication & User Management
- **Role-Based Authentication**: Secure signup/login for `job_seeker` and `recruiter` roles
- **Supabase Auth Integration**: JWT-based authentication via Supabase Auth
- **Auto-Profile Creation**: Automatic profile creation in role-specific tables during signup
- **File Upload During Registration**: 
  - Job Seekers: Required resume upload + optional profile picture
  - Recruiters: Optional profile picture
- **Password Recovery**: Forgot password functionality with email reset links
- **OAuth2 Compatible**: Full Swagger UI integration with Bearer token authentication

### Profile Management
- **View Profile**: Get comprehensive profile details based on role
- **Update Profile**: Role-specific profile updates:
  - **Job Seekers**: `bio`, `skills`, `headline`, `years_experience`, `phone_number`, `linkedin_url`, `portfolio_url`
  - **Recruiters**: `company`, `about_company`, `website_url`, `industry`, `company_size`, `location`
- **Password Management**: Secure password updates with old password verification
- **Avatar Management**: Upload/update profile pictures (stored in Supabase `avatars` bucket)
- **Resume Management**: Job seekers can upload/update their resume (PDF only, stored in `resumes` bucket)
- **Account Deletion**: Permanently delete account with all associated data and storage files

### Job Management
- **Create Jobs**: Recruiters can post jobs with rich attributes:
  - Basic: `title`, `description`, `deadline`, `location`, `job_type`
  - Advanced: `salary_min`, `salary_max`, `currency`, `is_remote`, `requirements[]`, `status`
- **List Jobs**: Public endpoint to browse all available jobs
- **View Job Details**: Detailed information for individual job postings
- **Update Jobs**: Recruiter-only, ownership-validated job updates
- **Delete Jobs**: Remove job postings (with cascade deletion of applications)
- **Application Viewing**: Recruiters can view all applications for their jobs
- **Deadline Enforcement**: Automatic blocking of applications after deadline

### Application System
- **Smart Application**: Job seekers can apply with:
  - Automatic resume linking from profile
  - Cover letter
  - Email capture for notifications
- **Duplicate Prevention**: System prevents multiple applications to the same job
- **Status Tracking**: Multi-stage application workflow (`pending` → `interviewing` → `hired`/`rejected`)
- **AI Scoring**: Support for AI-generated candidate scores and reasoning
- **Job Seeker Dashboard**: View all your applications with full job details
- **Recruiter Dashboard**: View and manage all applicants for your jobs
- **Background Notifications**: Email confirmations for application submissions

### AI & Automation
- **n8n Integration**: Automated screening workflows triggered on job creation
- **AI Scoring Fields**: Store AI-generated suitability scores (0-100) and reasoning
- **Execution Tracking**: Track n8n workflow execution IDs and completion timestamps

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth (JWT)
- **Storage**: Supabase Storage (Resumes, Avatars)
- **Validation**: Pydantic v2
- **Testing**: Pytest with async support
- **Email**: Background task queue for notifications
- **API Docs**: Auto-generated OpenAPI (Swagger UI + ReDoc)

## 📦 Setup

### 1. Prerequisites
- Python 3.10+
- A Supabase Project (free tier works)
- Supabase Storage buckets: `avatars` and `resumes`
- **(Optional) Google OAuth**: Google Cloud Console project with OAuth 2.0 credentials

### 2. Environment Variables
Create a `.env` file in the root directory:
```env
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-service-role-key"
# Note: Service Role Key is required for admin operations
```

### 3. Google OAuth Setup (Optional)

To enable "Sign in with Google" functionality:

**A. Google Cloud Console**:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure:
   - Application type: **Web application**
   - Authorized JavaScript origins: `http://localhost:3000` (frontend URL)
   - Authorized redirect URIs: `https://your-project.supabase.co/auth/v1/callback`
6. Copy **Client ID** and **Client Secret**

**B. Supabase Dashboard**:
1. Navigate to **Authentication** → **Providers** in your Supabase project
2. Enable **Google** provider
3. Paste **Client ID** and **Client Secret** from Google Cloud Console
4. Enable **Use PKCE flow** (recommended)
5. Save configuration

**C. Test OAuth**:
- Frontend must call `supabase.auth.signInWithOAuth({ provider: 'google' })`
- After successful OAuth, call `/api/v1/auth/oauth/complete-profile` to create role-specific profile



### 4. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd FastAPI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Database Schema
Run the following SQL in your Supabase SQL Editor to set up the tables:

```sql
-- 1. Job Seeker Table
CREATE TABLE public.job_seeker (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    full_name TEXT NOT NULL,
    resume_url TEXT,
    profile_picture_url TEXT,
    headline TEXT,
    bio TEXT,
    skills TEXT[],
    years_experience INT,
    phone_number TEXT,
    linked_in_url TEXT,
    portfolio_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Recruiters Table
CREATE TABLE public.recruiters (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    company TEXT NOT NULL,
    profile_picture_url TEXT,
    about_company TEXT,
    website_url TEXT,
    industry TEXT,
    company_size TEXT,
    location TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    legal_document_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Jobs Table
CREATE TABLE public.job (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    recruiter_id UUID REFERENCES public.recruiters(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    "desc" TEXT NOT NULL,
    deadline TIMESTAMPTZ,
    location TEXT,
    is_remote BOOLEAN DEFAULT FALSE,
    job_type TEXT,
    salary_min NUMERIC,
    salary_max NUMERIC,
    currency TEXT DEFAULT 'USD',
    requirements TEXT[],
    status TEXT DEFAULT 'open',
    n8n_execution_id TEXT,
    screening_completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Applications Table
CREATE TABLE public.application (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    job_id UUID REFERENCES public.job(id) ON DELETE CASCADE NOT NULL,
    job_seeker_id UUID REFERENCES public.job_seeker(id) ON DELETE CASCADE NOT NULL,
    resume_url TEXT NOT NULL,
    cover_letter TEXT,
    email TEXT,
    status TEXT DEFAULT 'pending',
    ai_score INT,
    ai_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id, job_seeker_id)
);

-- 5. Add indexes for performance
CREATE INDEX idx_job_recruiter ON public.job(recruiter_id);
CREATE INDEX idx_application_job ON public.application(job_id);
CREATE INDEX idx_application_seeker ON public.application(job_seeker_id);
CREATE INDEX idx_job_status ON public.job(status);
CREATE INDEX idx_application_status ON public.application(status);
```

### 5. Storage Buckets
Create the following buckets in your Supabase Storage:
- `avatars` (for profile pictures)
- `resumes` (for job seeker resumes)
- `documents` (for recruiter legal documents)

Configure them as **private** buckets with appropriate policies, or use signed URLs (current implementation uses signed URLs with 1-year expiry).

### 6. Running the App
```bash
# Development mode with auto-reload
fastapi dev app/main.py

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Visit http://127.0.0.1:8000/docs for the interactive Swagger UI documentation.

## 🔗 API Endpoints

### Authentication
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| POST | `/api/v1/auth/signup/job_seeker` | Register as job seeker (multipart: resume, profile_picture, full_name, email, password, skills, etc.) | ❌ |
| POST | `/api/v1/auth/signup/recruiter` | Register as recruiter (multipart: company_name, email, password, profile_picture, etc.) | ❌ |
| POST | `/api/v1/auth/login` | Login and receive JWT token | ❌ |
| POST | `/api/v1/auth/token` | OAuth2 compatible token endpoint (for Swagger UI) | ❌ |
| POST | `/api/v1/auth/forgot-password` | Send password reset email | ❌ |
| POST | `/api/v1/auth/oauth/complete-profile` | **Complete profile for OAuth users (Google, etc.)** | ✅ |

**Google OAuth Flow**:
1. Frontend initiates OAuth with Supabase client (`signInWithOAuth`)
2. User authenticates with Google
3. Supabase creates user and returns JWT
4. Frontend calls `/oauth/complete-profile` with role selection (`job_seeker` or `recruiter`)
5. Backend creates role-specific profile
6. User can access protected endpoints


### Profile Management
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| GET | `/api/v1/profile/me` | Get your profile details (role-specific) | ✅ |
| PUT | `/api/v1/profile/me` | Update profile information | ✅ |
| PUT | `/api/v1/profile/me/password` | Change password | ✅ |
| POST | `/api/v1/profile/me/avatar` | Upload/update profile picture | ✅ |
| POST | `/api/v1/profile/me/resume` | Upload/update resume (Job Seeker only) | ✅ |
| DELETE | `/api/v1/profile/me` | Delete account and all data | ✅ |

### Jobs
| Method | Endpoint | Description | Auth Required | Role |
| :--- | :--- | :--- | :---: | :--- |
| GET | `/api/v1/jobs` | List all available jobs with **search and filters** | ❌ | Public |
| GET | `/api/v1/jobs/{job_id}` | Get specific job details | ❌ | Public |
| POST | `/api/v1/jobs` | Create new job posting | ✅ | Recruiter |
| PUT | `/api/v1/jobs/{job_id}` | Update job (ownership validated) | ✅ | Recruiter (Owner) |
| DELETE | `/api/v1/jobs/{job_id}` | Delete job (ownership validated) | ✅ | Recruiter (Owner) |
| GET | `/api/v1/jobs/{job_id}/applications` | View applications for a job | ✅ | Recruiter (Owner) |

**Job Search Parameters** (for `GET /api/v1/jobs`):
- `q` - Search in job title and description (case-insensitive)
- `location` - Filter by location (partial match)
- `job_type` - Filter by exact job type
- `is_remote` - Filter for remote jobs (true/false)
- `salary_min` - Filter jobs with salary_max >= this value
- `salary_max` - Filter jobs with salary_min <= this value
- `requirements` - Comma-separated skills (job must have at least one)
- `status` - Filter by job status (default: "open")

### Applications
| Method | Endpoint | Description | Auth Required | Role |
| :--- | :--- | :--- | :---: | :--- |
| POST | `/api/v1/applications` | Apply to a job | ✅ | Job Seeker |
| GET | `/api/v1/applications/me` | **View my applications with search/filters** | ✅ | Job Seeker |
| GET | `/api/v1/applications/job/{job_id}` | **View applicants with search/filters** | ✅ | Recruiter (Owner) |
| PUT | `/api/v1/applications/{application_id}/status` | Update application status | ✅ | Recruiter (Owner) |

**Job Seeker Application Search** (for `GET /api/v1/applications/me`):
- `q` - Search by job title (case-insensitive)
- `status_filter` - Filter by application status
- `min_score` - Filter applications with ai_score >= value
- `max_score` - Filter applications with ai_score <= value

**Recruiter Application Search** (for `GET /api/v1/applications/job/{job_id}`):
- `q` - Search by applicant name (case-insensitive)
- `status_filter` - Filter by application status
- `min_score` - Filter applications with ai_score >= value
- `max_score` - Filter applications with ai_score <= value

## 🎯 Key Features Explained

### New: Job Seeker Application Dashboard
The `GET /api/v1/applications/me` endpoint allows job seekers to:
- View all their submitted applications in one place
- See complete job details for each application (title, company, salary, location, etc.)
- Track application status (pending, interviewing, hired, rejected)
- View AI scores and reasoning if available
- Applications are sorted by newest first

### Authorization Model
- **Job Seekers** can only see their own applications
- **Recruiters** can only see applications for jobs they posted
- All endpoints validate ownership before allowing access
- JWT tokens are verified on every protected request

### File Management
- Files are stored in Supabase Storage with user-specific naming (`{user_id}_avatar.{ext}`, `{user_id}_resume.pdf`)
- Signed URLs are generated with 1-year expiry for private bucket access
- Account deletion automatically removes all associated storage files

### AI Integration Ready
The system supports n8n workflows for automated candidate screening:
- Triggered on job creation
- Stores execution ID and completion timestamp
- Updates applications with AI scores and reasoning
- Status can be updated via API after screening completes

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_applications.py -v

# Run with coverage
pytest --cov=app tests/
```

## 📚 Documentation

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

## 🔒 Security Features

- JWT token-based authentication
- Password hashing via Supabase Auth
- Role-based access control (RBAC)
- Ownership validation on all update/delete operations
- Password verification for sensitive operations (password change, account deletion)
- CORS configuration for specific frontend origins

## 🚀 Development Workflow

1. **Make schema changes** in Pydantic models (`app/core/models.py`)
2. **Update database** via Supabase SQL Editor
3. **Implement endpoints** in appropriate route files (`app/api/v1/`)
4. **Write tests** in `tests/`
5. **Update README** with new endpoints

## 📝 Notes

- The application uses Supabase's Row Level Security (RLS) features for additional database-level security
- File uploads are handled via multipart/form-data
- All timestamps are stored in UTC with timezone awareness
- The API follows RESTful conventions with proper HTTP status codes

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is part of a capstone project for educational purposes.

---

**Built with ❤️ using FastAPI and Supabase**
