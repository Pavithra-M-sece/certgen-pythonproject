from django.db import models
from mongoengine import Document, StringField, DateTimeField, ReferenceField, ImageField, IntField, FileField
from django.contrib.auth.models import User
import datetime
import os
from django.conf import settings

class UserProfile(Document):
    user = StringField(required=True, unique=True)
    full_name = StringField(required=True)
    email = StringField(required=True)
    profile_photo = ImageField()
    bio = StringField(max_length=500)
    created_at = DateTimeField(default=datetime.datetime.now)
    
    meta = {'collection': 'user_profiles'}

class Certificate(Document):
    user = StringField(required=True)
    certificate_type = StringField(required=True)
    recipient_name = StringField(required=True)
    course_name = StringField()
    event_name = StringField()  # For participation certificates
    achievement_title = StringField()  # For achievement certificates
    achievement_description = StringField()  # For achievement certificates
    hours_completed = StringField()
    start_date = DateTimeField()
    completion_date = DateTimeField()
    template_style = StringField(required=True)
    signature = FileField()
    created_at = DateTimeField(default=datetime.datetime.now)
    pdf_file = FileField()  # To store the PDF directly in MongoDB
    
    meta = {'collection': 'certificates'}
    
    def get_pdf_path(self):
        """Get the path where the PDF file should be stored"""
        return os.path.join(settings.MEDIA_ROOT, 'certificates', f'certificate_{self.id}.pdf')
    
    def save_pdf(self, pdf_data):
        """Save the PDF data to both filesystem and MongoDB"""
        # Save to MongoDB
        self.pdf_file.put(pdf_data, content_type='application/pdf')
        self.save()
        
        # Save to filesystem
        pdf_path = self.get_pdf_path()
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        with open(pdf_path, 'wb') as f:
            f.write(pdf_data)

class UserActivity(Document):
    user = StringField(required=True)
    activity_type = StringField(required=True)  # login, logout, create_certificate
    timestamp = DateTimeField(default=datetime.datetime.now)
    
    meta = {'collection': 'user_activities'}
