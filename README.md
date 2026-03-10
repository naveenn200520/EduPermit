# TJS Engineering College - College Management System

A comprehensive web-based college management system for handling student permissions, bonafide certificates, attendance, and notifications.

## Features

- **Student Portal**: Apply for permissions, view bonafide certificates, check attendance
- **Staff Portal**: Approve/reject student permissions, manage department students
- **HOD Portal**: Review forwarded permissions, approve bonafide certificates
- **Admin Portal**: Manage users, departments, generate reports
- **Gate Pass System**: QR code-based gate pass generation and verification

## Demo Credentials

- **Student**: 22CS001 / student123
- **Staff**: staff@college.edu / staff123  
- **HOD**: hod@college.edu / hod123
- **Admin**: admin@college.edu / admin123

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL (Production) / SQLite (Development)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Other**: QR Code generation, Image processing

## Deployment Instructions

### Heroku Deployment

1. **Install Heroku CLI** and login:
   ```bash
   heroku login
   ```

2. **Create a new Heroku app**:
   ```bash
   heroku create your-app-name
   ```

3. **Add PostgreSQL addon**:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

4. **Set environment variables**:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key-here
   ```

5. **Initialize Git and deploy**:
   ```bash
   git init
   git add .
   git commit -m "Initial deployment"
   heroku git:remote -a your-app-name
   git push heroku main
   ```

6. **Initialize the database**:
   ```bash
   heroku run python database.py
   ```

### Environment Variables

- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: PostgreSQL connection URL (automatically set by Heroku)
- `PORT`: Application port (automatically set by Heroku)

## Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd smart2
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**:
   ```bash
   python database.py
   ```

5. **Run the application**:
   ```bash
   python app.py
   ```

## Project Structure

```
smart2/
├── app.py              # Main Flask application
├── models.py           # Database models
├── database.py         # Database seeding script
├── gate_pass.py        # QR code generation
├── requirements.txt    # Python dependencies
├── Procfile           # Heroku process definition
├── runtime.txt        # Python version specification
├── static/            # Static assets (CSS, JS, images)
├── templates/         # HTML templates
└── instance/          # Database files (SQLite)
```

## License

This project is proprietary to TJS Engineering College.
