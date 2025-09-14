# StratagemForge Web Application

Next.js web application for the StratagemForge CS:GO demo analysis platform.

## Features

- **Modern React Framework**: Built with Next.js 14 and App Router
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Real-time Updates**: SWR for data fetching and caching
- **Service Integration**: Communicates exclusively with BFF service
- **Component Library**: Reusable UI components with Headless UI
- **Toast Notifications**: User feedback with react-hot-toast

## Technology Stack

- **Framework**: Next.js 14 (React 18)
- **Styling**: Tailwind CSS with custom components
- **TypeScript**: Full type safety
- **Data Fetching**: SWR for caching and revalidation
- **UI Components**: Headless UI + Heroicons
- **Notifications**: React Hot Toast

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BFF_SERVICE_URL` | `http://localhost:3000` | BFF service endpoint |
| `NEXT_PUBLIC_APP_NAME` | `StratagemForge` | Application name |
| `NEXT_PUBLIC_APP_VERSION` | `1.0.0` | Application version |

## Development

### Prerequisites

- Node.js 18+ 
- npm or yarn package manager

### Local Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open browser
open http://localhost:3000
```

### Building for Production

```bash
# Build the application
npm run build

# Start production server
npm start
```

### Code Quality

```bash
# Run linting
npm run lint

# Fix linting issues
npm run lint:fix

# Type checking
npm run type-check

# Run tests
npm test
```

## Project Structure

```
src/
├── app/                  # Next.js App Router
│   ├── layout.tsx       # Root layout
│   ├── page.tsx         # Home page
│   ├── globals.css      # Global styles
│   ├── demos/           # Demo management pages
│   └── analysis/        # Analysis pages
├── components/          # Reusable components
│   ├── ui/             # Base UI components
│   ├── forms/          # Form components
│   └── layout/         # Layout components
├── lib/                # Utilities and API
│   ├── api.ts          # API client
│   ├── utils.ts        # Helper functions
│   └── types.ts        # TypeScript types
└── hooks/              # Custom React hooks
    ├── useApi.ts       # API data fetching
    └── useToast.ts     # Toast notifications
```

## Pages and Features

### Home Page (`/`)
- System overview and status
- Service health monitoring
- Quick action buttons
- Feature showcase

### Demo Management (`/demos`)
- Upload CS:GO demo files
- View uploaded demos
- Demo file management
- Processing status

### Analysis Dashboard (`/analysis`)
- View analysis results
- Interactive charts and graphs
- Performance metrics
- Strategy insights

## API Integration

### BFF Service Communication
All API calls go through the BFF service:

```typescript
// Example API call
const response = await fetch('/api/demos');
const demos = await response.json();
```

### Proxy Configuration
Next.js automatically proxies `/api/*` requests to the BFF service via rewrites in `next.config.js`.

### Error Handling
- Network error handling with retry logic
- User-friendly error messages
- Fallback UI for service unavailability

## Styling and Components

### Tailwind CSS
- Utility-first CSS framework
- Custom component classes in `globals.css`
- Responsive design patterns
- Dark mode support (planned)

### Component Design System
```typescript
// Button variants
<button className="btn btn-primary">Primary Action</button>
<button className="btn btn-secondary">Secondary Action</button>

// Card layouts
<div className="card">
  <div className="card-header">
    <h3>Card Title</h3>
  </div>
  <div className="card-body">
    Card content
  </div>
</div>
```

## Container Deployment

### Building the Image

```bash
# Build Docker image
podman build -t web-app .
```

### Running with Podman

```bash
# Run container
podman run -p 3000:3000 \
  -e BFF_SERVICE_URL="http://bff:3000" \
  web-app
```

### Development with podman-compose

```bash
# Start all services including web app
podman-compose up

# Web app available at http://localhost:3000
```

## Performance Considerations

### Optimization Features
- **Static Generation**: Pre-rendered pages where possible
- **Image Optimization**: Next.js automatic image optimization
- **Code Splitting**: Automatic route-based code splitting
- **Caching**: SWR for client-side caching

### Build Output
- Standalone output for container deployment
- Optimized bundle sizes
- Tree shaking for unused code elimination

## Security

### Content Security Policy
- Configured via Helmet in Next.js config
- CORS handling for API communication
- XSS protection with React's built-in sanitization

### Environment Variables
- No sensitive data in client-side code
- Environment-specific configuration
- Build-time vs runtime variable handling

## Integration with StratagemForge

This web application is the primary user interface for the StratagemForge platform:

- **Single Page Application**: React-based SPA with Next.js routing
- **BFF Communication**: All backend communication through BFF service
- **Service Discovery**: Environment variable based service discovery
- **Responsive Design**: Works on desktop, tablet, and mobile devices

For complete system architecture, see the main project ARCHITECTURE.md.