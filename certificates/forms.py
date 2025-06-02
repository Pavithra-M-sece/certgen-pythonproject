from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=100)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'password1', 'password2']

class UserProfileUpdateForm(forms.Form):
    full_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    profile_photo = forms.ImageField(required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)

class CertificateForm(forms.Form):
    CERTIFICATE_TYPES = [
        ('course_completion', 'Course Completion'),
        ('achievement', 'Achievement'),
        ('participation', 'Participation'),
    ]
    
    TEMPLATE_STYLES = [
        ('classic', 'Classic'),
        ('modern', 'Modern'),
        ('minimal', 'Minimal'),
    ]
    
    certificate_type = forms.ChoiceField(
        choices=CERTIFICATE_TYPES,
        required=True,
        label='Certificate Type',
        help_text='Select the type of certificate you want to create'
    )
    
    template_style = forms.ChoiceField(
        choices=TEMPLATE_STYLES,
        required=True,
        label='Template Style',
        help_text='Choose the visual style for your certificate'
    )
    
    recipient_name = forms.CharField(
        max_length=100,
        required=True,
        label='Recipient Name',
        help_text='Enter the full name of the certificate recipient'
    )
    
    # Course Completion Fields
    course_name = forms.CharField(
        max_length=200,
        required=False,
        label='Course Name',
        help_text='Enter the full name of the completed course'
    )
    
    hours_completed = forms.CharField(
        max_length=50,
        required=False,
        label='Hours Completed',
        help_text='Enter the total hours completed (e.g., "40")'
    )
    
    # Event Fields
    event_name = forms.CharField(
        max_length=200, 
        required=False,
        label='Event Name',
        help_text='Enter the full name of the event you participated in'
    )
    
    # Achievement Fields
    achievement_title = forms.CharField(
        max_length=200,
        required=False,
        label='Achievement Title',
        help_text='Enter the specific achievement or award'
    )
    
    achievement_description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Achievement Description',
        help_text='Briefly describe the achievement or reason for recognition'
    )
    
    # Date Fields
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Start Date',
        help_text='Select the start date (for course completion certificates)'
    )
    
    completion_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Completion Date',
        help_text='Select the completion or award date'
    )
    
    signature = forms.ImageField(
        required=True,
        label='Signature',
        help_text='Upload your signature as an image file (PNG, JPG)'
    )

    def clean(self):
        cleaned_data = super().clean()
        certificate_type = cleaned_data.get('certificate_type')

        if certificate_type == 'course_completion':
            if not cleaned_data.get('course_name'):
                self.add_error('course_name', 'Course name is required for course completion certificates.')
        elif certificate_type == 'participation':
            if not cleaned_data.get('event_name'):
                self.add_error('event_name', 'Event name is required for participation certificates.')
        elif certificate_type == 'achievement':
            if not cleaned_data.get('achievement_title'):
                self.add_error('achievement_title', 'Achievement title is required for achievement certificates.')
            if not cleaned_data.get('achievement_description'):
                self.add_error('achievement_description', 'Achievement description is required for achievement certificates.')

        return cleaned_data 