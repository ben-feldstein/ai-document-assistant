# AI Document Assistant - Modern UI

A beautiful, responsive React-based user interface for the AI Document Assistant. This modern UI provides an intuitive way to interact with your documents using AI-powered chat and voice interfaces.

## ✨ Features

- **🎨 Beautiful Design**: Modern, responsive interface with Tailwind CSS
- **🔐 Authentication**: Secure login/signup with JWT tokens
- **📚 Document Management**: Upload and organize your private documents
- **💬 AI Chat**: Intelligent document queries with context-aware responses
- **🎤 Voice Interface**: Real-time voice interaction with your documents
- **📊 Dashboard**: System overview and analytics
- **📱 Responsive**: Works perfectly on all devices
- **⚡ Fast**: Built with Vite for lightning-fast development

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Backend API running on port 8000
- Grafana running on port 3000

### Installation

1. **Navigate to the UI directory**:
   ```bash
   cd modern-ui
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser**:
   Navigate to [http://localhost:3001](http://localhost:3001)

## 🏗️ Project Structure

```
modern-ui/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── ui/            # Basic UI components (buttons, inputs, etc.)
│   │   └── Layout.tsx     # Main application layout
│   ├── contexts/          # React contexts (auth, etc.)
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # Utility libraries (API client, etc.)
│   ├── pages/             # Page components
│   │   ├── Login.tsx      # Authentication page
│   │   ├── Signup.tsx     # User registration
│   │   ├── Dashboard.tsx  # Main dashboard
│   │   ├── Documents.tsx  # Document management
│   │   ├── Chat.tsx       # AI chat interface
│   │   ├── Voice.tsx      # Voice interaction
│   │   └── Settings.tsx   # User settings
│   ├── App.tsx            # Main application component
│   ├── main.tsx           # Application entry point
│   └── index.css          # Global styles
├── public/                 # Static assets
├── package.json            # Dependencies and scripts
├── vite.config.ts          # Vite configuration
├── tailwind.config.js      # Tailwind CSS configuration
└── README.md               # This file
```

## 🎨 Tech Stack

- **React 18** - Modern React with hooks and context
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router v6** - Client-side routing
- **React Query** - Server state management
- **Axios** - HTTP client for API calls
- **Lucide React** - Beautiful icons
- **Framer Motion** - Smooth animations
- **React Hook Form** - Form handling
- **Zod** - Schema validation
- **React Hot Toast** - Toast notifications
- **Recharts** - Data visualization

## 🔧 Configuration

### API Endpoints

The UI is configured to proxy API calls to your backend:

- **API Proxy**: `/api/*` → `http://localhost:8000/*`
- **WebSocket Proxy**: `/ws/*` → `ws://localhost:8000/*`

### Port Configuration

- **UI Port**: 3001 (to avoid conflict with Grafana on 3000)
- **Backend Port**: 8000
- **Grafana Port**: 3000

## 📱 Pages

### Public Pages
- **Login** (`/login`) - User authentication
- **Signup** (`/signup`) - User registration

### Protected Pages
- **Dashboard** (`/dashboard`) - System overview and quick actions
- **Documents** (`/documents`) - Document upload and management
- **Chat** (`/chat`) - AI-powered document queries
- **Voice** (`/voice`) - Voice interaction interface
- **Settings** (`/settings`) - User preferences and configuration

## 🎯 Key Features

### Authentication
- JWT-based authentication
- Automatic token refresh
- Protected route handling
- User session management

### Document Management
- Drag-and-drop file uploads
- Document organization
- Search and filtering
- Privacy and security

### AI Interaction
- Context-aware responses
- Document-based queries
- Voice and text interfaces
- Conversation history

### Responsive Design
- Mobile-first approach
- Adaptive layouts
- Touch-friendly interactions
- Cross-device compatibility

## 🚀 Development

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
```

### Development Workflow

1. **Make changes** to components or pages
2. **Hot reload** automatically updates the browser
3. **Type checking** ensures code quality
4. **Linting** maintains code style
5. **Build** creates optimized production files

## 🔒 Security

- **JWT Authentication**: Secure token-based auth
- **Protected Routes**: Automatic redirect for unauthenticated users
- **API Security**: All requests include authentication headers
- **Privacy**: User data stays within their organization

## 📊 Monitoring

The UI integrates with your backend monitoring stack:

- **Health Checks**: Automatic service status monitoring
- **Error Handling**: Graceful error display and recovery
- **Performance**: Optimized rendering and data fetching
- **Analytics**: User interaction tracking (if enabled)

## 🐛 Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 3001 and 8000 are available
2. **API Connection**: Verify backend is running on port 8000
3. **Dependencies**: Run `npm install` if you see module errors
4. **Build Issues**: Clear `node_modules` and reinstall if needed

### Debug Mode

Enable debug logging in the browser console:

```javascript
localStorage.setItem('debug', 'true')
```

## 🤝 Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Test on multiple devices and browsers
4. Update documentation for new features

## 📄 License

This project is licensed under the MIT License.

---

**Built with ❤️ for intelligent document interaction**
