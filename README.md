# WhatsApp Platform API

A comprehensive WhatsApp automation and messaging platform built with FastAPI, supporting multi-tier user management and credit distribution.

## Features

### User Management
- **Multi-tier Architecture**: Admin → Reseller → Business Owner
- **Role-based Access Control**: Different permissions for each user type
- **Complete User Profiles**: Business info, addresses, bank details
- **WhatsApp Integration**: Support for official and unofficial modes

### Credit System
- **Hierarchical Credit Distribution**: Resellers distribute credits to business owners
- **Real-time Credit Tracking**: Automatic balance updates
- **Comprehensive Statistics**: Usage reports and analytics
- **Audit Trail**: Complete history of all credit transactions

### Technical Features
- **FastAPI**: Modern, fast web framework with automatic docs
- **SQLAlchemy**: Powerful ORM with database migrations
- **Pydantic**: Data validation and serialization
- **JWT Authentication**: Secure token-based authentication
- **Background Tasks**: Celery for async operations
- **Redis**: Caching and session management

## Project Structure

```
whatsapp_api_project/
├── core/                   # Core configuration and security
│   ├── config.py           # Application settings
│   └── security.py         # JWT and password handling
├── db/                    # Database configuration
│   └── database.py         # SQLAlchemy setup
├── models/                 # Database models
│   ├── user.py            # User model (Admin, Reseller, Business Owner)
│   └── credit_distribution.py  # Credit distribution tracking
├── schemas/               # Pydantic schemas
│   ├── user.py            # User request/response schemas
│   └── credit_distribution.py  # Credit distribution schemas
├── services/             # Business logic
│   ├── user_service.py    # User operations
│   └── credit_distribution_service.py  # Credit operations
├── middleware/           # Custom middleware
│   └── auth.py          # Authentication middleware
├── utils/               # Utility functions
│   └── helpers.py        # Common helper functions
├── tasks/               # Background tasks
│   └── credit_tasks.py   # Celery tasks for credits
├── migrations/          # Database migrations
├── api/               # API routes (future)
├── tests/             # Test files
├── main.py            # Application entry point
├── requirements.txt   # Python dependencies
├── .env.example      # Environment variables template
└── README.md         # This file
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd whatsapp_api_project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python create_sample_user.py
   python create_sample_business_owner.py
   python create_sample_credit_distribution.py
   ```

## Running the Application

### Development Server
```bash
python main.py
```

### Production with Uvicorn
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### With Background Tasks (Redis + Celery)
```bash
# Start Redis
redis-server

# Start Celery worker
celery -A tasks.credit_tasks worker --loglevel=info

# Start Celery beat scheduler
celery -A tasks.credit_tasks beat --loglevel=info

# Start FastAPI server
python main.py
```

## API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Endpoints

### User Management
- `POST /users/` - Create new user
- `GET /users/` - List all users
- `GET /users/{user_id}` - Get specific user
- `POST /users/login` - User authentication

### Business Owners
- `POST /resellers/{reseller_id}/business-owners/` - Create business owner
- `GET /resellers/{reseller_id}/business-owners/` - List business owners

### Credit Distribution
- `POST /credit-distributions/` - Distribute credits
- `GET /credit-distributions/` - List all distributions
- `GET /credit-distributions/{distribution_id}` - Get specific distribution
- `GET /resellers/{reseller_id}/credit-distributions/` - Reseller's distributions
- `GET /business-owners/{business_user_id}/credit-distributions/` - Business owner's distributions
- `GET /resellers/{reseller_id}/credit-stats/` - Reseller credit statistics
- `GET /business-owners/{business_user_id}/credit-stats/` - Business owner credit statistics
- `GET /credit-distributions/summary/` - Platform-wide summary

## Sample Data

The application includes sample data creation scripts:

### Sample Users
- **Reseller**: Mayur Khalate (`mayur_admin` / `admin123`)
- **Business Owner**: Amit Sharma (`amit_store` / `business123`)

### Credit Distribution
- 5,000 credits distributed from reseller to business owner

## Configuration

### Environment Variables
Key environment variables in `.env`:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key
- `WHATSAPP_API_URL`: WhatsApp API endpoint
- `REDIS_URL`: Redis connection for caching

### Database Support
- **SQLite** (default): `sqlite:///./whatsapp_platform.db`
- **PostgreSQL**: `postgresql://user:pass@localhost/dbname`
- **MySQL**: `mysql://user:pass@localhost/dbname`

## Security Features

- **Password Hashing**: bcrypt for secure password storage
- **JWT Authentication**: Token-based authentication with expiration
- **Role-based Access**: Different permissions for different user types
- **Input Validation**: Comprehensive data validation with Pydantic
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection

## Development

### Adding New Models
1. Create model in `models/` directory
2. Create corresponding schemas in `schemas/`
3. Implement service layer in `services/`
4. Add API endpoints in `main.py`

### Running Tests
```bash
pytest tests/
```

### Database Migrations
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Production Deployment

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Considerations
- Use PostgreSQL/MySQL for production
- Set strong `SECRET_KEY`
- Configure Redis for caching
- Set up proper CORS origins
- Enable HTTPS in production

## Contributing

1. Fork the repository
2. Create feature branch
3. Make your changes
4. Add tests if applicable
5. Submit pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the repository.
