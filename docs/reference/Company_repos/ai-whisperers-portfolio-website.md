# ai-whisperers-portfolio-website

**Description:** AI Whisperers company portfolio website.
**URL:** https://github.com/Ai-Whisperers/ai-whisperers-portfolio-website
**Visibility:** PRIVATE

---

# AI Whisperers Portfolio Website

[![Next.js](https://img.shields.io/badge/Next.js-14.2-black?logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?logo=typescript)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwind-css)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-All%20Rights%20Reserved-red)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/Ai-Whisperers/ai-whisperers-portfolio-website)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](docs/contributing.md)

> Enterprise-grade portfolio and showcase website for AI Whisperers, built with Next.js 14 and modern web technologies.

[Live Demo](https://www.ai-whisperers.org) • [Documentation](../../../docs) • [Report Bug](https://github.com/Ai-Whisperers/ai-whisperers-portfolio-website/issues) • [Request Feature](https://github.com/Ai-Whisperers/ai-whisperers-portfolio-website/issues)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development](#development)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## Overview

AI Whisperers Portfolio Website is a modern, responsive, and SEO-optimized platform showcasing our enterprise AI solutions, projects, and client success stories. Built with Next.js 14 App Router and designed with a clean enterprise aesthetic featuring subtle web3 elements.

### Key Highlights

- **Performance First**: 146KB bundle size, Lighthouse score >90
- **Fully Responsive**: Mobile, tablet, and desktop optimized
- **Dark Mode**: System-aware theme with manual toggle
- **SEO Optimized**: Comprehensive metadata, sitemap, robots.txt
- **Accessible**: WCAG AA compliant with reduced-motion support
- **Production Ready**: Complete with contact API, analytics-ready, and monitoring hooks

## Features

### Core Features

- **Landing Page Sections**
  - Hero with gradient background and CTA
  - Projects showcase with external links
  - B2B value proposition and metrics
  - Client testimonials
  - Course previews with LMS integration
  - Contact form with API validation

- **UI/UX**
  - Light/Dark theme with system detection
  - Smooth scroll animations (Framer Motion)
  - Glassmorphism effects on key components
  - Hover interactions and micro-animations
  - Mobile-first responsive design

- **Developer Experience**
  - TypeScript for type safety
  - ESLint + Prettier for code quality
  - Hot reload development server
  - Component-based architecture
  - Comprehensive documentation

### Technical Features

- Static Site Generation (SSG) with Next.js export
- Formspree integration for contact form
- Environment-based configuration
- SEO metadata and OpenGraph tags
- Sitemap and robots.txt generation
- PWA manifest support
- Email service integration ready (Resend/SendGrid)
- Error tracking ready (Sentry)

## Tech Stack

### Frontend

| Technology                                                | Version | Purpose                         |
| --------------------------------------------------------- | ------- | ------------------------------- |
| [Next.js](https://nextjs.org/)                            | 14.2    | React framework with App Router |
| [React](https://reactjs.org/)                             | 18.3    | UI library                      |
| [TypeScript](https://www.typescriptlang.org/)             | 5.0     | Type safety                     |
| [TailwindCSS](https://tailwindcss.com/)                   | 3.4     | Utility-first CSS               |
| [Framer Motion](https://www.framer.com/motion/)           | 12.x    | Animation library               |
| [next-themes](https://github.com/pacocoursey/next-themes) | 0.4     | Theme management                |
| [Lucide React](https://lucide.dev/)                       | Latest  | Icon library                    |

### Development Tools

- **Linting**: ESLint with Next.js config
- **Formatting**: Prettier with Tailwind plugin
- **Type Checking**: TypeScript strict mode
- **Build Tool**: Next.js compiler (Turbopack-ready)

### Infrastructure

- **Hosting**: GitHub Pages (static export)
- **CI/CD**: GitHub Actions
- **Forms**: Formspree
- **Monitoring**: Sentry-ready
- **Analytics**: Google Analytics-ready

## Getting Started

### Prerequisites

- Node.js 18.x or higher
- npm 9.x or higher (or yarn/pnpm)
- Git

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/Ai-Whisperers/ai-whisperers-portfolio-website.git
cd ai-whisperers-portfolio-website
```

2. **Install dependencies**

```bash
npm install
```

3. **Set up environment variables**

```bash
cp .env.example .env.development
```

Edit `.env.development` with your local configuration.

4. **Run the development server**

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Available Scripts

| Command              | Description                           |
| -------------------- | ------------------------------------- |
| `npm run dev`        | Start development server on port 3000 |
| `npm run build`      | Build for production                  |
| `npm start`          | Start production server               |
| `npm run lint`       | Run ESLint                            |
| `npm run format`     | Format code with Prettier             |
| `npm run type-check` | Run TypeScript type checking          |
| `npm run clean`      | Clean build artifacts                 |

## Project Structure

```
ai-whisperers-portfolio-website/
├── app/                      # Next.js 14 App Router
│   ├── layout.tsx           # Root layout with metadata
│   ├── page.tsx             # Landing page
│   ├── globals.css          # Global styles
│   ├── robots.ts            # Robots.txt generation
│   └── sitemap.ts           # Sitemap generation
├── components/              # React components
│   ├── ui/                  # Base UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── textarea.tsx
│   ├── sections/            # Landing page sections
│   ├── navbar.tsx
│   ├── hero.tsx
│   ├── footer.tsx
│   ├── contact-form.tsx
│   ├── theme-provider.tsx
│   ├── theme-toggle.tsx
│   └── animated-section.tsx
├── lib/                     # Utility functions
│   ├── utils.ts             # CN helper and utilities
│   └── animations.ts        # Framer Motion variants
├── public/                  # Static assets
│   ├── favicon.svg
│   ├── favicon.png
│   ├── og-image.png
│   └── site.webmanifest
├── docs/                    # Documentation
├── .env.example             # Environment variables template
├── .env.development         # Development environment
├── tailwind.config.ts       # Tailwind configuration
├── next.config.js           # Next.js configuration
├── tsconfig.json            # TypeScript configuration
├── CLAUDE.md                # AI development guidelines
└── README.md                # This file
```

## Development

### Design System

The project follows a comprehensive design system with consistent tokens:

- **Colors**: Defined light/dark themes with cyan-to-violet gradients
- **Typography**: Inter font family with responsive scales
- **Spacing**: 4px base unit following 8-point grid
- **Animations**: 200-400ms duration with ease-out timing

See [docs/design-system.md](../../../docs/design-system.md) for complete details.

### Code Style

- **No Emojis**: Professional codebase without emoji usage
- **TypeScript**: Strict mode enabled, all components typed
- **Component Structure**: Functional components with hooks
- **Naming**: PascalCase for components, camelCase for functions
- **Imports**: Absolute imports using `@/` alias

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

### Adding New Components

1. Create component in `components/` or `components/ui/`
2. Use TypeScript for props and types
3. Apply design tokens from Tailwind config
4. Add animations using Framer Motion if needed
5. Ensure dark mode support with `dark:` variants
6. Test responsiveness on all breakpoints

### Environment Variables

| Variable                  | Description           | Required |
| ------------------------- | --------------------- | -------- |
| `NEXT_PUBLIC_SITE_URL`    | Production URL        | Yes      |
| `NEXT_PUBLIC_COURSES_URL` | LMS platform URL      | Yes      |
| `EMAIL_SERVICE_API_KEY`   | Email service API key | Optional |
| `SENTRY_DSN`              | Sentry error tracking | Optional |

See [.env.example](.env.example) for complete list.

## Deployment

### Deploy to GitHub Pages

The website is automatically deployed to GitHub Pages on every push to the main branch.

1. **Automatic Deployment**
   - GitHub Actions workflow builds and deploys automatically
   - Static export is generated to `out/` directory
   - Deployed to: https://www.ai-whisperers.org

2. **Manual Deployment**

   ```bash
   npm run build    # Build static export
   npm run deploy   # Deploy to gh-pages branch
   ```

3. **Configuration**
   - Contact form uses Formspree (configured)
   - Custom domain: www.ai-whisperers.org
   - CNAME file automatically generated during build

For detailed setup instructions including:

- GitHub Pages configuration
- Custom domain setup
- Form service configuration
- Build optimization

### Build Optimization

- **Bundle Size**: 146KB (optimized)
- **Routes**: 7 total (5 static, 1 dynamic API)
- **Lighthouse Score**: >90 on all metrics
- **Core Web Vitals**: All in green zone

## Documentation

- **[Deployment Guide](../../../docs/deployment.md)**: Complete deployment instructions
- **[Design System](../../../docs/design-system.md)**: Design tokens and guidelines
- **[Architecture](../../../docs/architecture.md)**: Technical architecture overview
- **[Contributing Guide](../../../docs/contributing.md)**: How to contribute
- **[API Documentation](../../../docs/api.md)**: API routes documentation

## Security

This project follows security best practices for dependency management:

### Dependency Security

- **Automated Auditing**: `npm audit` runs during CI/CD pipeline
- **Vulnerability Patching**: Transitive dependencies are pinned to secure versions via npm overrides
- **Regular Updates**: Dependencies are regularly reviewed and updated

### Current Security Measures

| Package | Version  | Mitigation                                |
| ------- | -------- | ----------------------------------------- |
| glob    | >=10.5.0 | Patched command injection vulnerability   |
| js-yaml | >=4.1.1  | Patched prototype pollution vulnerability |

### Reporting Security Issues

If you discover a security vulnerability, please report it by:

1. Opening a private security advisory on GitHub
2. Contacting us through our [website](https://www.ai-whisperers.org)

Do not disclose security vulnerabilities publicly until they have been addressed.

## Resources

### Company

- [GitHub Organization](https://github.com/Ai-Whisperers)
- [Agentic Schemas](https://ai-whisperers.github.io/agentic-schemas/)
- [AI Courses Platform](https://aiwhisperers-courses.onrender.com/)

### Documentation

- [Next.js Documentation](https://nextjs.org/docs)
- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Formspree Documentation](https://help.formspree.io/)

## Contributing

We welcome contributions! Please see our [Contributing Guide](../../../docs/contributing.md) for details.

### Quick Start

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code of Conduct

Please read our [Code of Conduct](../../../docs/code-of-conduct.md) before contributing.

## License

Copyright © 2024 AI Whisperers. All rights reserved.

This project is proprietary and confidential. Unauthorized copying, distribution, or use of this software is strictly prohibited.

## Support

- **Documentation**: Check [docs/](../../../docs) folder
- **Issues**: [GitHub Issues](https://github.com/Ai-Whisperers/ai-whisperers-portfolio-website/issues)
- **Email**: Contact us through our [website](https://www.ai-whisperers.org)

---

**Built with** Next.js 14 • TypeScript • TailwindCSS • Framer Motion

**Deployed on** GitHub Pages

**Maintained by** [AI Whisperers](https://github.com/Ai-Whisperers)
