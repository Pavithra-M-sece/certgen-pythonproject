# Certificate Generator

A Django web application for generating and managing certificates with customizable templates and MongoDB integration.

## Features

- User Registration and Authentication
- Dashboard with Quick Actions
- Create Different Types of Certificates
  - Course Completion Certificates
  - Achievement Certificates
  - Participation Certificates
- Customizable Certificate Templates
- PDF Generation with Signature Support
- Certificate Management and History
- User Profile Management
- Activity Tracking

## Prerequisites

- Python 3.8 or higher
- MongoDB 4.4 or higher
- Virtual Environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd certificate-generator
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Make sure MongoDB is running on your system (default: localhost:27017)

5. Create necessary directories:
```bash
mkdir media
mkdir media/certificates
mkdir static
```

6. Run migrations:
```bash
python manage.py migrate
```

7. Create a superuser (admin):
```bash
python manage.py createsuperuser
```

8. Run the development server:
```bash
python manage.py runserver
```

The application will be available at http://127.0.0.1:8000/

## Usage

1. Register a new account or login with existing credentials
2. Navigate to the dashboard
3. Create a new certificate by clicking "Create Certificate"
4. Fill in the certificate details and upload a signature
5. Generate and download the certificate as PDF
6. View all your certificates in the "My Certificates" section
7. Update your profile information as needed

## Project Structure

```
certificate_generator/
├── certificates/           # Main application
│   ├── templates/         # HTML templates
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── forms.py          # Form definitions
│   └── urls.py           # URL configurations
├── static/               # Static files
├── media/               # User uploaded files
├── requirements.txt     # Project dependencies
└── manage.py           # Django management script
```

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License. 