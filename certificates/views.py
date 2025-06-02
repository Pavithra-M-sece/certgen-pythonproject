from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponseRedirect
from .forms import UserRegistrationForm, CertificateForm, UserProfileUpdateForm
from .models import UserProfile, Certificate, UserActivity
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import os
from datetime import datetime
from django.conf import settings
import traceback
from io import BytesIO
from django.urls import reverse

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile(
                user=user.username,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email']
            ).save()
            login(request, user)
            UserActivity(user=user.username, activity_type='register').save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'certificates/register.html', {'form': form})

@login_required
def dashboard(request):
    certificates = Certificate.objects(user=request.user.username)
    return render(request, 'certificates/dashboard.html', {'certificates': certificates})

@login_required
def profile(request):
    user_profile = UserProfile.objects(user=request.user.username).first()
    
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            user_profile.full_name = form.cleaned_data['full_name']
            user_profile.email = form.cleaned_data['email']
            user_profile.bio = form.cleaned_data['bio']
            
            if 'profile_photo' in request.FILES:
                # Delete old photo if it exists
                if user_profile.profile_photo:
                    user_profile.profile_photo.delete()
                # Save new photo
                photo_file = request.FILES['profile_photo']
                user_profile.profile_photo.put(photo_file, content_type=photo_file.content_type)
            
            user_profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        initial_data = {
            'full_name': user_profile.full_name,
            'email': user_profile.email,
            'bio': user_profile.bio if hasattr(user_profile, 'bio') else ''
        }
        form = UserProfileUpdateForm(initial=initial_data)
    
    return render(request, 'certificates/profile.html', {
        'form': form,
        'user_profile': user_profile
    })

@login_required
def create_certificate(request):
    if request.method == 'POST':
        form = CertificateForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create certificate directory if it doesn't exist
                certificates_dir = os.path.join(settings.MEDIA_ROOT, 'certificates')
                os.makedirs(certificates_dir, exist_ok=True)

                # Get the certificate type and basic fields
                certificate_type = form.cleaned_data['certificate_type']
                certificate_data = {
                    'user': request.user.username,
                    'certificate_type': certificate_type,
                    'recipient_name': form.cleaned_data['recipient_name'],
                    'template_style': form.cleaned_data['template_style']
                }

                # Add type-specific fields
                if certificate_type == 'course_completion':
                    certificate_data.update({
                        'course_name': form.cleaned_data.get('course_name'),
                        'hours_completed': form.cleaned_data.get('hours_completed'),
                        'start_date': form.cleaned_data.get('start_date'),
                        'completion_date': form.cleaned_data.get('completion_date')
                    })
                elif certificate_type == 'achievement':
                    certificate_data.update({
                        'achievement_title': form.cleaned_data.get('achievement_title'),
                        'achievement_description': form.cleaned_data.get('achievement_description'),
                        'completion_date': form.cleaned_data.get('completion_date')
                    })
                elif certificate_type == 'participation':
                    certificate_data.update({
                        'event_name': form.cleaned_data.get('event_name'),
                        'completion_date': form.cleaned_data.get('completion_date')
                    })

                # Create and save the certificate
                try:
                    # Check if signature file is present
                    if 'signature' not in request.FILES:
                        messages.error(request, 'Please upload a signature file.')
                        return render(request, 'certificates/create_certificate.html', {'form': form})

                    # Create certificate instance
                    certificate = Certificate(**certificate_data)
                    
                    # Handle signature upload first
                    signature_file = request.FILES['signature']
                    certificate.signature.put(signature_file, content_type=signature_file.content_type)
                    
                    # Save certificate with signature
                    certificate.save()

                    try:
                        # Generate PDF certificate
                        generate_certificate_pdf(certificate)
                        
                        # Log activity
                        UserActivity(
                            user=request.user.username,
                            activity_type='create_certificate'
                        ).save()

                        messages.success(request, 'Certificate created successfully!')
                        return redirect('dashboard')
                    except Exception as e:
                        print(f"PDF Generation Error: {str(e)}")
                        print(traceback.format_exc())
                        if certificate.id:
                            certificate.delete()
                        messages.error(request, 'Error generating PDF certificate. Please try again.')
                        return render(request, 'certificates/create_certificate.html', {'form': form})

                except Exception as e:
                    print(f"Certificate Save Error: {str(e)}")
                    print(traceback.format_exc())
                    messages.error(request, f'Error saving certificate: {str(e)}')
                    return render(request, 'certificates/create_certificate.html', {'form': form})

            except Exception as e:
                print(f"Certificate Creation Error: {str(e)}")
                print(traceback.format_exc())
                messages.error(request, f'Error creating certificate: {str(e)}')
                return render(request, 'certificates/create_certificate.html', {'form': form})
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return render(request, 'certificates/create_certificate.html', {'form': form})
    else:
        form = CertificateForm()
    
    return render(request, 'certificates/create_certificate.html', {'form': form})

@login_required
def view_certificates(request):
    certificates = Certificate.objects(user=request.user.username)
    return render(request, 'certificates/view_certificates.html', {'certificates': certificates})

def generate_certificate_pdf(certificate):
    try:
        # Create directory for certificates if it doesn't exist
        certificates_dir = os.path.join(settings.MEDIA_ROOT, 'certificates')
        os.makedirs(certificates_dir, exist_ok=True)
        
        # Create PDF in memory first
        buffer = BytesIO()
        
        # Create PDF with ReportLab
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Set background color and style based on template style
        if certificate.template_style == 'modern':
            c.setFillColorRGB(0.95, 0.95, 1)  # Light blue background
            text_color = (0.2, 0.4, 0.8)  # Blue text
            border_color = (0.1, 0.3, 0.7)  # Darker blue for border
            accent_color = (0.3, 0.5, 0.9)  # Accent color
        elif certificate.template_style == 'classic':
            c.setFillColorRGB(1, 0.95, 0.9)  # Light cream background
            text_color = (0.6, 0.1, 0.1)  # Dark red text
            border_color = (0.5, 0.1, 0.1)  # Darker red for border
            accent_color = (0.7, 0.2, 0.2)  # Accent color
        else:  # minimal
            c.setFillColorRGB(1, 1, 1)  # White background
            text_color = (0.2, 0.2, 0.2)  # Dark gray text
            border_color = (0.4, 0.4, 0.4)  # Medium gray for border
            accent_color = (0.6, 0.6, 0.6)  # Light gray accent
            
        # Draw background
        c.rect(0, 0, width, height, fill=True)
        
        # Add decorative border with rounded corners
        c.setStrokeColorRGB(*border_color)
        c.setLineWidth(3)
        c.roundRect(30, 30, width-60, height-60, 20)
        
        # Add inner decorative border
        c.setLineWidth(1)
        c.roundRect(45, 45, width-90, height-90, 15)
        
        # Set text color
        c.setFillColorRGB(*text_color)
        
        # Add certificate header with shadow effect
        header_text = "Certificate of " + certificate.certificate_type.replace('_', ' ').title()
        c.setFont("Helvetica-Bold", 40)
        c.drawCentredString(width/2 + 2, height-150, header_text)  # Shadow
        c.setFillColorRGB(*text_color)
        c.drawCentredString(width/2, height-148, header_text)  # Main text
        
        # Add decorative line under header
        c.setStrokeColorRGB(*accent_color)
        c.setLineWidth(2)
        c.line(width/4, height-170, width*3/4, height-170)
        
        # Add "This is to certify that" text
        c.setFont("Helvetica", 24)
        c.drawCentredString(width/2, height-220, "This is to certify that")
        
        # Add recipient name with larger font and decorative underline (in CAPITALS)
        recipient_name = certificate.recipient_name.upper()
        c.setFont("Helvetica-Bold", 36)
        name_y = height-280
        c.drawCentredString(width/2, name_y, recipient_name)
        c.setStrokeColorRGB(*accent_color)
        c.setLineWidth(1)
        name_width = c.stringWidth(recipient_name, "Helvetica-Bold", 36)
        c.line(width/2 - name_width/2, name_y-5, width/2 + name_width/2, name_y-5)
        
        # Initialize y_position for dynamic content
        y_position = height-340
        
        # Display certificate type specific information
        if certificate.certificate_type == 'course_completion':
            # Course completion specific details
            c.setFont("Helvetica", 24)
            c.drawCentredString(width/2, y_position, "has successfully completed")
            y_position -= 40
            
            c.setFont("Helvetica-Bold", 30)
            c.drawCentredString(width/2, y_position, certificate.course_name)
            y_position -= 50
            
            if certificate.hours_completed:
                c.setFont("Helvetica", 24)
                hours_text = f"Duration: {certificate.hours_completed} hours"
                c.drawCentredString(width/2, y_position, hours_text)
                y_position -= 40
            
            if certificate.start_date and certificate.completion_date:
                c.setFont("Helvetica", 22)
                start_date = certificate.start_date.strftime("%B %d, %Y")
                end_date = certificate.completion_date.strftime("%B %d, %Y")
                c.drawCentredString(width/2, y_position, f"Start Date: {start_date}")
                y_position -= 35
                c.drawCentredString(width/2, y_position, f"Completion Date: {end_date}")
                y_position -= 40
                
        elif certificate.certificate_type == 'achievement':
            # Achievement specific details
            c.setFont("Helvetica", 24)
            c.drawCentredString(width/2, y_position, "has achieved")
            y_position -= 40
            
            c.setFont("Helvetica-Bold", 30)
            c.drawCentredString(width/2, y_position, certificate.achievement_title)
            y_position -= 50
            
            if certificate.achievement_description:
                c.setFont("Helvetica", 20)
                # Split description into multiple lines if needed
                description_lines = [certificate.achievement_description[i:i+60] 
                                  for i in range(0, len(certificate.achievement_description), 60)]
                for line in description_lines:
                    c.drawCentredString(width/2, y_position, line)
                    y_position -= 30
            
            if certificate.completion_date:
                c.setFont("Helvetica", 22)
                completion_date = certificate.completion_date.strftime("%B %d, %Y")
                y_position -= 10  # Add extra space
                c.drawCentredString(width/2, y_position, f"Awarded on: {completion_date}")
                y_position -= 40
                
        elif certificate.certificate_type == 'participation':
            # Participation specific details
            c.setFont("Helvetica", 24)
            c.drawCentredString(width/2, y_position, "has participated in")
            y_position -= 40
            
            c.setFont("Helvetica-Bold", 30)
            # Split event name into multiple lines if needed
            event_name_lines = [certificate.event_name[i:i+40] 
                              for i in range(0, len(certificate.event_name), 40)]
            for line in event_name_lines:
                c.drawCentredString(width/2, y_position, line)
                y_position -= 40
            
            if certificate.completion_date:
                c.setFont("Helvetica", 22)
                completion_date = certificate.completion_date.strftime("%B %d, %Y")
                y_position -= 10  # Add extra space
                c.drawCentredString(width/2, y_position, f"Event Date: {completion_date}")
                y_position -= 40
        
        # Add signature with improved placement and styling
        if hasattr(certificate, 'signature') and certificate.signature:
            try:
                # Reset the file pointer to the beginning
                certificate.signature.seek(0)
                signature_data = certificate.signature.read()
                sig_img = ImageReader(BytesIO(signature_data))
                
                # Draw signature with proper scaling
                sig_width = 200
                sig_height = 100
                sig_x = width/2 - sig_width/2
                sig_y = 150  # Position from bottom
                c.drawImage(sig_img, sig_x, sig_y, width=sig_width, height=sig_height, preserveAspectRatio=True)
                
                # Add signature line and title
                c.setStrokeColorRGB(*text_color)
                c.setLineWidth(1)
                c.line(width/2 - 100, sig_y-10, width/2 + 100, sig_y-10)
                c.setFont("Helvetica", 14)
                c.drawCentredString(width/2, sig_y-30, "Authorized Signature")
            except Exception as e:
                print(f"Signature Error: {str(e)}")
                print(traceback.format_exc())
        
        # Add date of issue and certificate ID in a more concise format
        c.setFont("Helvetica", 12)  # Smaller font for the ID
        c.setFillColorRGB(*text_color)
        issue_date = datetime.now().strftime("%B %d, %Y")
        
        # Create a shorter certificate ID (first 8 characters)
        short_id = str(certificate.id)[:8]
        
        # Draw issue date and certificate ID
        c.drawString(50, 50, f"Issued: {issue_date}")
        c.drawRightString(width-50, 50, f"ID: {short_id}")
        
        c.save()
        
        # Get PDF data from buffer
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Save PDF to both MongoDB and filesystem
        certificate.save_pdf(pdf_data)
        
        return certificate.get_pdf_path()
        
    except Exception as e:
        print(f"PDF Generation Error: {str(e)}")
        print(traceback.format_exc())
        raise

@login_required
def delete_certificate(request, certificate_id):
    try:
        certificate = Certificate.objects(id=certificate_id, user=request.user.username).first()
        if certificate:
            # Delete the PDF file if it exists
            pdf_path = os.path.join(settings.MEDIA_ROOT, 'certificates', f'certificate_{certificate_id}.pdf')
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            
            # Delete the certificate from database
            certificate.delete()
            
            UserActivity(
                user=request.user.username,
                activity_type='delete_certificate'
            ).save()
            
            messages.success(request, 'Certificate deleted successfully!')
        else:
            messages.error(request, 'Certificate not found.')
    except Exception as e:
        print(f"Delete Error: {str(e)}")
        messages.error(request, 'Error deleting certificate.')
    
    return redirect('view_certificates')

@login_required
def view_certificate(request, certificate_id):
    try:
        certificate = Certificate.objects(id=certificate_id, user=request.user.username).first()
        if not certificate:
            messages.error(request, 'Certificate not found.')
            return redirect('view_certificates')
        
        # Get or generate PDF
        pdf_path = certificate.get_pdf_path()
        if not os.path.exists(pdf_path) and certificate.pdf_file:
            # If file exists in MongoDB but not in filesystem, restore it
            with open(pdf_path, 'wb') as f:
                f.write(certificate.pdf_file.read())
        elif not os.path.exists(pdf_path):
            # If no PDF exists anywhere, generate it
            try:
                generate_certificate_pdf(certificate)
            except Exception as e:
                print(f"PDF Generation Error: {str(e)}")
                print(traceback.format_exc())
                messages.error(request, 'Error generating certificate PDF. Please try again.')
                return redirect('view_certificates')
        
        # Verify the file exists
        if not os.path.exists(pdf_path):
            messages.error(request, 'Certificate PDF file not found.')
            return redirect('view_certificates')
        
        try:
            # Open the file and create response without using 'with' block
            pdf_file = open(pdf_path, 'rb')
            response = FileResponse(pdf_file)
            response['Content-Type'] = 'application/pdf'
            response['Content-Disposition'] = f'inline; filename="{certificate.recipient_name}_certificate.pdf"'
            
            # Log the activity
            UserActivity(
                user=request.user.username,
                activity_type='view_certificate'
            ).save()
            
            return response
                
        except IOError as e:
            print(f"File Read Error: {str(e)}")
            print(traceback.format_exc())
            
            # Try serving from MongoDB as fallback
            if certificate.pdf_file:
                response = FileResponse(certificate.pdf_file, content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{certificate.recipient_name}_certificate.pdf"'
                return response
            
            messages.error(request, 'Error reading the certificate file. Please try again.')
            return redirect('view_certificates')
            
    except Exception as e:
        print(f"View Certificate Error: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, 'Error viewing certificate.')
        return redirect('view_certificates')

@login_required
def download_certificate(request, certificate_id):
    try:
        # Get the certificate and verify ownership
        certificate = Certificate.objects(id=certificate_id, user=request.user.username).first()
        if not certificate:
            messages.error(request, 'Certificate not found.')
            return redirect('view_certificates')
        
        # Get or generate PDF
        pdf_path = certificate.get_pdf_path()
        if not os.path.exists(pdf_path) and certificate.pdf_file:
            # If file exists in MongoDB but not in filesystem, restore it
            with open(pdf_path, 'wb') as f:
                f.write(certificate.pdf_file.read())
        elif not os.path.exists(pdf_path):
            # If no PDF exists anywhere, generate it
            try:
                generate_certificate_pdf(certificate)
            except Exception as e:
                print(f"PDF Generation Error: {str(e)}")
                print(traceback.format_exc())
                messages.error(request, 'Error generating certificate PDF. Please try again.')
                return redirect('view_certificates')
        
        # Verify the file exists
        if not os.path.exists(pdf_path):
            messages.error(request, 'Certificate PDF file not found.')
            return redirect('view_certificates')
        
        try:
            # Generate a clean filename
            safe_filename = "".join(c for c in certificate.recipient_name if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{safe_filename}_{certificate.certificate_type}_certificate.pdf"
            
            # Open the file and create response without using 'with' block
            pdf_file = open(pdf_path, 'rb')
            response = FileResponse(pdf_file)
            response['Content-Type'] = 'application/pdf'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Log the activity
            UserActivity(
                user=request.user.username,
                activity_type='download_certificate'
            ).save()
            
            return response
                
        except IOError as e:
            print(f"File Read Error: {str(e)}")
            print(traceback.format_exc())
            
            # Try serving from MongoDB as fallback
            if certificate.pdf_file:
                response = FileResponse(certificate.pdf_file, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            
            messages.error(request, 'Error reading the certificate file. Please try again.')
            return redirect('view_certificates')
            
    except Exception as e:
        print(f"Download Error: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, 'Error downloading certificate. Please try again.')
        return redirect('view_certificates')

@login_required
def delete_profile(request):
    if request.method == 'POST':
        try:
            # Get user profile
            user_profile = UserProfile.objects(user=request.user.username).first()
            
            # Delete profile photo if exists
            if user_profile and user_profile.profile_photo:
                user_profile.profile_photo.delete()
            
            # Delete all user's certificates
            certificates = Certificate.objects(user=request.user.username)
            for cert in certificates:
                # Delete certificate PDF if exists
                pdf_path = os.path.join(settings.MEDIA_ROOT, 'certificates', f'certificate_{cert.id}.pdf')
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                cert.delete()
            
            # Delete user activities
            UserActivity.objects(user=request.user.username).delete()
            
            # Delete user profile
            user_profile.delete()
            
            # Delete Django user
            request.user.delete()
            
            messages.success(request, 'Your account has been successfully deleted.')
            return redirect('login')
            
        except Exception as e:
            print(f"Profile Deletion Error: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, 'Error deleting profile. Please try again.')
            return redirect('profile')
    
    return redirect('profile')

@login_required
def view_profile_photo(request):
    try:
        user_profile = UserProfile.objects(user=request.user.username).first()
        if user_profile and user_profile.profile_photo:
            return FileResponse(user_profile.profile_photo, content_type='image/jpeg')
        else:
            raise Http404("Profile photo not found")
    except Exception as e:
        print(f"Profile Photo View Error: {str(e)}")
        raise Http404("Error retrieving profile photo")
