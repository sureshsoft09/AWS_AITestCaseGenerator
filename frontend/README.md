# MedAssureAI Frontend

A comprehensive React application for AI-powered healthcare test case management and compliance validation.

## 🚀 Features

### Core Functionality
- **Dashboard**: Project overview with real-time statistics and activity tracking
- **AI Test Case Generation**: Upload healthcare documents and generate comprehensive test cases using AI
- **Test Case Enhancement**: Analyze and improve existing test cases with AI-powered suggestions
- **Migration Tools**: Import and migrate test cases from external systems (Jira, TestLink, qTest, etc.)
- **Analytics & Reporting**: Comprehensive insights and compliance reporting

### Healthcare Compliance
- **FDA 21 CFR Part 820** compliance validation
- **IEC 62304** medical device software standards
- **ISO 13485** quality management requirements
- **HIPAA** healthcare data protection
- **IEC 62366** usability engineering standards
- **ISO 14155** clinical investigation requirements

### AI-Powered Features
- Intelligent test case generation from requirements documents
- Automated test enhancement suggestions
- Smart field mapping for data migration
- Compliance gap analysis
- Risk assessment automation

## 🛠️ Technology Stack

- **React 18+** - Modern React with hooks and functional components
- **Material-UI v6** - Enterprise-grade UI components with custom theming
- **React Router** - Client-side routing and navigation
- **Recharts** - Interactive charts and data visualization
- **Axios** - HTTP client for API communication
- **Tailwind CSS** - Utility-first styling (supplemental)

### 🏠 Dashboard
- Project overview and statistics
- Real-time metrics and progress tracking
- Recent activity monitoring
- Quick access to all projects

### 🚀 AI Test Case Generation
- Upload healthcare documents (PDF, DOC, DOCX, TXT)
- AI-powered test case generation from requirements
- Compliance standards integration
- Multiple test type support (functional, usability, performance, security)
- Interactive AI chat assistant

### 🔧 Test Case Enhancement
- AI-powered analysis of existing test cases
- Security, performance, and accessibility improvements
- Compliance gap identification
- Bulk enhancement operations

### 📤 Migration & Import
- Support for multiple formats (Excel, Jira, TestLink, qTest, TestRail, Azure DevOps, HP ALM)
- Intelligent field mapping
- Data validation and preview
- Batch migration with progress tracking

### 📊 Analytics & Reporting
- Comprehensive project analytics
- Test coverage and compliance metrics
- Risk assessment visualization
- Trend analysis and reporting
- Exportable reports (PDF)

## Technology Stack

- **React 18+** - Modern React with hooks and functional components
- **Material UI v6** - Enterprise-grade UI components with custom theming
- **React Router 6** - Client-side routing
- **Recharts** - Data visualization and charts
- **Axios** - HTTP client for API communication
- **Inter Font** - Modern typography

## Project Structure

```
Frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   └── layout/
│   │       ├── Layout.js
│   │       ├── TopNavBar.js
│   │       └── Sidebar.js
│   ├── contexts/
│   │   └── NotificationContext.js
│   ├── pages/
│   │   ├── Dashboard.js
│   │   ├── TestCaseGeneration.js
│   │   ├── EnhanceTestCases.js
│   │   ├── MigrationTestCases.js
│   │   └── AnalyticsReport.js
│   ├── services/
│   │   └── api.js
│   ├── App.js
│   ├── index.js
│   └── index.css
├── package.json
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API server running (see Backend documentation)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "MedAssure AI/Frontend"
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   Create a `.env` file in the root directory:
   ```env
   REACT_APP_API_BASE_URL=http://localhost:8000
   REACT_APP_MCP_SERVER_URL=http://localhost:3001
   ```

4. **Start the development server**
   ```bash
   npm start
   ```

5. **Open your browser**
   Navigate to `http://localhost:3000`

## Key Features Detail

### AI-Powered Test Generation
- **Document Processing**: Upload requirements documents in various formats
- **Intelligent Parsing**: AI extracts key information and generates comprehensive test cases
- **Compliance Integration**: Automatic validation against healthcare standards
- **Interactive Enhancement**: Chat with AI to refine and improve test cases

### Healthcare Compliance
- **FDA 21 CFR Part 820**: Medical device quality system regulation
- **IEC 62304**: Medical device software lifecycle processes
- **ISO 13485**: Medical devices quality management systems
- **HIPAA**: Health Insurance Portability and Accountability Act
- **IEC 62366**: Medical devices usability engineering
- **ISO 14155**: Clinical investigation of medical devices

### Project Hierarchy
```
Project
├── Epic (High-level business objectives)
│   ├── Feature (Specific functionality)
│   │   ├── Use Case (User scenarios)
│   │   │   └── Test Case (Detailed test procedures)
```

### Test Case Management
- **Comprehensive Tracking**: From creation to execution
- **Risk Assessment**: Critical, High, Medium, Low risk categorization
- **Multiple Test Types**: Functional, Usability, Performance, Security, Integration
- **Version Control**: Track changes and improvements
- **Compliance Mapping**: Link test cases to specific regulations

## API Integration

The frontend integrates with:

1. **Backend FastAPI Server** - Main application API
2. **MCP Firestore Server** - Test case data management
3. **AI Services** - Test generation and enhancement

### API Endpoints Used

- `GET /projects` - Retrieve projects
- `POST /generate-test-cases` - AI test case generation
- `POST /enhance-test-case` - Test case enhancement
- `POST /migration/parse` - Parse uploaded files
- `GET /analytics/overview` - Analytics data
- `POST /chat/test-generation` - AI chat interactions

## Styling & Theming

### Design System
- **Primary Colors**: Gradient from #667eea to #764ba2
- **Typography**: Inter font family for modern readability
- **Components**: Custom Material UI theme with gradient styling
- **Responsive**: Mobile-first design approach

### Color Palette
```css
Primary: #667eea (Blue)
Secondary: #764ba2 (Purple)
Success: #4caf50 (Green)
Warning: #ff9800 (Orange)
Error: #f44336 (Red)
Background: #f8faff (Light Blue)
```

## Development Guidelines

### Component Structure
- Use functional components with hooks
- Implement proper error boundaries
- Follow Material UI design patterns
- Maintain consistent spacing and typography

### State Management
- React Context for global state (notifications)
- Local state for component-specific data
- API calls through centralized service layer

### Code Quality
- ESLint configuration for code quality
- Prettier for code formatting
- Component documentation
- Type checking with PropTypes (optional)

## Performance Optimization

- **Lazy Loading**: Route-based code splitting
- **Memoization**: React.memo for expensive components
- **Virtualization**: For large data lists
- **Image Optimization**: Proper image formats and sizing
- **Bundle Analysis**: Regular bundle size monitoring

## Security Considerations

- **API Security**: Proper authentication headers
- **Data Validation**: Input sanitization
- **HTTPS**: Secure communication
- **Content Security Policy**: XSS protection
- **Healthcare Compliance**: HIPAA-compliant data handling

## Testing Strategy

### Unit Testing
- Component testing with React Testing Library
- Service layer testing
- Utility function testing

### Integration Testing
- API integration tests
- User workflow testing
- Cross-browser compatibility

### E2E Testing
- Critical user paths
- Accessibility testing
- Performance testing

## Deployment

### Production Build
```bash
npm run build
```

### Deployment Options
- **Static Hosting**: Netlify, Vercel, AWS S3
- **Container Deployment**: Docker with nginx
- **CDN Integration**: CloudFront, CloudFlare

### Environment Configuration
- Development: `npm start`
- Production: `npm run build && serve -s build`
- Testing: `npm test`

## Healthcare Compliance Notes

This application handles healthcare-related data and must comply with:

1. **HIPAA**: Ensure PHI protection
2. **FDA Guidelines**: Medical device software validation
3. **ISO Standards**: Quality management systems
4. **Data Security**: Encryption at rest and in transit

## Contributing

1. Follow the established code style
2. Write comprehensive tests
3. Update documentation
4. Ensure accessibility compliance
5. Test across supported browsers

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

This project is proprietary software for healthcare test case management.

## Support

For technical support or questions about healthcare compliance features, please contact the development team.
