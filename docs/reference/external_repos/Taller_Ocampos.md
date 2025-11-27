# Taller_Ocampos

**Description:** 
**URL:** https://github.com/Ai-Whisperers/Taller_Ocampos
**Visibility:** PUBLIC

---

# Taller Mecánico - Auto Repair Shop Management System
Doc-Type: Project Overview · Version 1.0 · Updated 2025-11-10 · Production Ready

Complete management system for auto repair shops with real-time updates, inventory tracking, and client management.

---

## 🚀 Quick Deploy to Vercel (5 Minutes)

**Frontend is ready for immediate deployment!**

### **Step 1: Import to Vercel**
1. Go to [vercel.com/new](https://vercel.com/new)
2. Import this GitHub repository
3. Vercel will auto-detect Next.js

### **Step 2: Configure Settings**
In Vercel project settings:
- **Root Directory:** `frontend`
- **Framework Preset:** Next.js (auto-detected)
- **Build Command:** Auto-detected from package.json
- **Output Directory:** Auto-detected (.next)

### **Step 3: Add Environment Variables**
In Settings → Environment Variables, add:
```env
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com/api
NEXT_PUBLIC_SOCKET_URL=https://your-backend.onrender.com
NEXT_PUBLIC_APP_NAME=Taller Mecánico
```

**Note:** For demo/testing, you can use placeholder backend URL. Backend deployment guide is in `changelog/DEPLOYMENT_MVP_VERCEL.md`

### **Step 4: Deploy**
Click "Deploy" - Your frontend will be live in ~2 minutes!

---

## 📦 What's Included

### **Frontend (Next.js 14 + React 18)**
- 🎨 Modern UI with Tailwind CSS + Radix UI
- 📱 Responsive design (desktop, tablet, mobile)
- 🔐 JWT authentication
- 📊 Real-time dashboard with WebSocket updates
- 🚗 Client & vehicle management
- 📝 Work order tracking
- 💰 Invoicing & payment system
- 📦 Inventory management
- 🧪 Full test coverage (Jest + Playwright)

### **Backend (Express + TypeScript)**
- 🔒 Secure REST API with JWT
- 🔌 Real-time updates via Socket.IO
- 🗄️ PostgreSQL database with Prisma ORM
- 📤 File upload support
- 🛡️ Security headers, rate limiting, CORS
- ✅ Input validation with Zod
- 🧪 Unit & integration tests

### **Deployment Options**
- ✅ Vercel (Frontend) - **Ready Now**
- ✅ Render/Railway (Backend)
- ✅ Neon.tech (Database)
- ✅ Docker + Kubernetes (On-premise)

---

## 🎯 Project Structure

```
Taller_Ocampos/
├── frontend/                    ← Deploy to Vercel (Set as Root Directory)
│   ├── src/                    ← Application code
│   │   ├── app/               ← Next.js 14 App Router
│   │   ├── components/        ← React components
│   │   ├── lib/               ← Utilities & API client
│   │   └── hooks/             ← Custom React hooks
│   ├── vercel.json            ← Vercel configuration
│   ├── package.json           ← Dependencies & scripts
│   └── next.config.js         ← Next.js configuration
│
├── backend/                     ← Deploy to Render/Railway
│   ├── src/                    ← TypeScript source
│   │   ├── controllers/       ← Business logic
│   │   ├── routes/            ← API endpoints
│   │   ├── middleware/        ← Auth, validation, errors
│   │   └── utils/             ← Helpers & logger
│   ├── prisma/                ← Database schema & migrations
│   └── package.json           ← Dependencies & scripts
│
├── BOOTSTRAP_CONTRACTS.md      ← Technical integration spec
├── .env.vercel.example         ← Environment variable template
└── .vercelignore               ← Files excluded from deployment
```

---

## 🔧 Technology Stack

### **Frontend**
- **Framework:** Next.js 14.2.33 (App Router)
- **UI Library:** React 18.2.0
- **Styling:** Tailwind CSS 3.3.6
- **Components:** Radix UI, Lucide Icons
- **State Management:** Zustand, React Query
- **Forms:** React Hook Form + Zod validation
- **Real-time:** Socket.IO Client
- **HTTP Client:** Axios
- **Testing:** Jest, Testing Library, Playwright

### **Backend**
- **Runtime:** Node.js 18+ with TypeScript 5.3.3
- **Framework:** Express 4.18.2
- **Database:** PostgreSQL with Prisma ORM 5.7.0
- **Authentication:** JWT (jsonwebtoken)
- **Real-time:** Socket.IO 4.6.0
- **Security:** Helmet, CORS, Rate Limiting
- **Validation:** Zod 3.22.4
- **Logging:** Winston
- **Testing:** Jest, Supertest

### **Infrastructure**
- **Frontend Hosting:** Vercel (Serverless)
- **Backend Hosting:** Render/Railway (Node.js)
- **Database:** Neon.tech (PostgreSQL)
- **Containerization:** Docker (optional)
- **Orchestration:** Kubernetes (optional)

---

## 🌐 Live Demo

Once deployed to Vercel, your application will be available at:
```
https://your-project-name.vercel.app
```

**Default Login (After Backend Setup):**
- Email: `admin@taller.com`
- Password: Create via registration

---

## 📚 Documentation

### **For Deployment**
- **Frontend (Vercel):** See "Quick Deploy to Vercel" section above
- **Backend (Render):** `changelog/DEPLOYMENT_MVP_VERCEL.md`
- **Docker:** `changelog/DEPLOYMENT_DOCKER.md`
- **Kubernetes:** `changelog/DEPLOYMENT_KUBERNETES.md`

### **For Development**
- **Getting Started:** `changelog/QUICK_START.md`
- **Bootstrap Contracts:** `BOOTSTRAP_CONTRACTS.md`
- **Environment Variables:** `.env.vercel.example`

### **For Production**
- **Storage Upgrade:** `changelog/TODO_PRODUCTION_STORAGE.md`
- **Security:** See `BOOTSTRAP_CONTRACTS.md`

---

## 🔐 Environment Variables

### **Frontend (Vercel Dashboard)**
```env
# Required
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com/api
NEXT_PUBLIC_SOCKET_URL=https://your-backend.onrender.com
NEXT_PUBLIC_APP_NAME=Taller Mecánico

# Optional
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
```

### **Backend (Render/Railway Dashboard)**
```env
# Required
NODE_ENV=production
PORT=3001
DATABASE_URL=postgresql://user:pass@host.neon.tech/db
JWT_SECRET=your-super-secret-jwt-key-32-chars-minimum
JWT_EXPIRES_IN=7d
FRONTEND_URL=https://your-app.vercel.app

# Optional
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads
```

**See `.env.vercel.example` for complete details.**

---

## 🚦 Deployment Status

| Component | Platform | Status | Notes |
|:----------|:---------|:-------|:------|
| **Frontend** | Vercel | ✅ **Ready** | Classical Next.js deployment |
| **Backend** | Render/Railway | ⚠️ Needs Setup | See deployment guide |
| **Database** | Neon.tech | ⚠️ Needs Setup | Free tier available |

**Frontend can be deployed independently for demo purposes!**

---

## 🧪 Testing

### **Frontend**
```bash
cd frontend
npm test              # Unit tests (Jest)
npm run test:e2e      # E2E tests (Playwright)
npm run test:coverage # Coverage report
```

### **Backend**
```bash
cd backend
npm test              # Unit & integration tests
npm run test:coverage # Coverage report
```

---

## 💰 Cost Analysis (Free Tier)

| Service | Cost | Limitations |
|:--------|:-----|:------------|
| **Vercel** | $0/month | 100GB bandwidth, hobby projects |
| **Render** | $0/month | 750hrs/month, sleeps after 15min |
| **Neon** | $0/month | 0.5GB storage, 1 database |
| **Total** | **$0/month** | Perfect for MVP and demos |

**For production:** ~$46/month (always-on backend, larger database)

---

## 🛠️ Local Development

### **Prerequisites**
- Node.js 18+ and npm 9+
- PostgreSQL 14+ (or use Neon.tech)
- Git

### **Setup**
```bash
# Clone repository
git clone https://github.com/Ai-Whisperers/Taller_Ocampos.git
cd Taller_Ocampos

# Setup Frontend
cd frontend
cp .env.example .env.local
npm install
npm run dev         # http://localhost:3000

# Setup Backend (separate terminal)
cd ../backend
cp .env.example .env
npm install
npm run prisma:migrate
npm run dev         # http://localhost:3001
```

---

## 🔒 Security Features

- ✅ JWT authentication with secure token handling
- ✅ Password hashing with bcrypt
- ✅ CORS protection
- ✅ Rate limiting
- ✅ Helmet security headers
- ✅ XSS protection
- ✅ CSRF protection
- ✅ SQL injection prevention (Prisma ORM)
- ✅ Input validation (Zod)

---

## 📱 Features

### **Dashboard**
- Real-time statistics
- Recent work orders
- Revenue charts
- Inventory alerts
- Active vehicles count

### **Client Management**
- Client profiles with contact info
- Vehicle history
- Work order tracking
- Payment history

### **Vehicle Management**
- Vehicle profiles linked to clients
- Maintenance history
- Service reminders
- Part replacement tracking

### **Work Orders**
- Create and manage work orders
- Assign mechanics
- Track progress
- Add parts and labor
- Generate invoices

### **Inventory**
- Parts catalog
- Stock tracking
- Low stock alerts
- Purchase orders
- Supplier management

### **Invoicing**
- Automatic invoice generation
- Payment tracking
- Multiple payment methods
- PDF export (future)

---

## 🤝 Support

**For Deployment Issues:**
- Check `BOOTSTRAP_CONTRACTS.md` for integration details
- Review `changelog/DEPLOYMENT_MVP_VERCEL.md` for step-by-step guide
- Verify environment variables are set correctly

**For Development:**
- Check `changelog/QUICK_START.md`
- Review test files for usage examples
- Check logs for error details

---

## 📄 License

Proprietary - Taller Mecánico Auto Repair Shop Management System

---

## 🎉 Ready to Deploy!

The frontend is **production-ready** and can be deployed to Vercel immediately:

1. **Import repository to Vercel**
2. **Set Root Directory to `frontend`**
3. **Add environment variables**
4. **Deploy!**

Your client can see the frontend live in less than 5 minutes! 🚀

---

**Version:** 1.0
**Last Updated:** 2025-11-10
**Status:** ✅ Production Ready (Frontend)
**Deployment Time:** ~5 minutes (Frontend only)
