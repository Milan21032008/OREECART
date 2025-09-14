import os
import uuid
from flask import render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, GeneratedFile
from forms import LoginForm, RegistrationForm, TextToSpeechForm, TextToVideoForm
from utils import generate_audio, generate_video
import logging

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's recent files
    recent_files = GeneratedFile.query.filter_by(user_id=current_user.id).order_by(
        GeneratedFile.created_at.desc()
    ).limit(10).all()
    
    # Get statistics
    total_files = GeneratedFile.query.filter_by(user_id=current_user.id).count()
    audio_files = GeneratedFile.query.filter_by(user_id=current_user.id, file_type='audio').count()
    video_files = GeneratedFile.query.filter_by(user_id=current_user.id, file_type='video').count()
    
    stats = {
        'total_files': total_files,
        'audio_files': audio_files,
        'video_files': video_files
    }
    
    return render_template('dashboard.html', recent_files=recent_files, stats=stats)

@app.route('/text-to-speech', methods=['GET', 'POST'])
@login_required
def text_to_speech():
    form = TextToSpeechForm()
    if form.validate_on_submit():
        try:
            # Generate unique filename
            filename = f"audio_{uuid.uuid4().hex[:8]}.wav"
            file_path = os.path.join(current_app.config['GENERATED_FOLDER'], filename)
            
            # Generate audio file (gTTS does not support speech rate)
            success = generate_audio(form.text.data, file_path)
            
            if success:
                # Get file size
                file_size = os.path.getsize(file_path)
                
                # Save to database
                generated_file = GeneratedFile(
                    user_id=current_user.id,
                    filename=filename,
                    file_type='audio',
                    original_text=form.text.data,
                    file_path=file_path,
                    file_size=file_size
                )
                db.session.add(generated_file)
                db.session.commit()
                
                flash('Audio generated successfully!', 'success')
                return redirect(url_for('download_file', file_id=generated_file.id))
            else:
                flash('Error generating audio. Please try again.', 'error')
                
        except Exception as e:
            logging.error(f"Error in text-to-speech: {str(e)}")
            flash('An error occurred while generating audio.', 'error')
    
    return render_template('text_to_speech.html', form=form)

@app.route('/text-to-video', methods=['GET', 'POST'])
@login_required
def text_to_video():
    form = TextToVideoForm()
    if form.validate_on_submit():
        try:
            # Generate unique filename
            filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
            file_path = os.path.join(current_app.config['GENERATED_FOLDER'], filename)
            
            # Generate video file
            success = generate_video(
                form.text.data,
                file_path,
                form.background_color.data,
                form.text_color.data,
                int(form.duration.data)
            )
            
            if success:
                # Get file size
                file_size = os.path.getsize(file_path)
                
                # Save to database
                generated_file = GeneratedFile(
                    user_id=current_user.id,
                    filename=filename,
                    file_type='video',
                    original_text=form.text.data,
                    file_path=file_path,
                    file_size=file_size
                )
                db.session.add(generated_file)
                db.session.commit()
                
                flash('Video generated successfully!', 'success')
                return redirect(url_for('download_file', file_id=generated_file.id))
            else:
                flash('Error generating video. Please try again.', 'error')
                
        except Exception as e:
            logging.error(f"Error in text-to-video: {str(e)}")
            flash('An error occurred while generating video.', 'error')
    
    return render_template('text_to_video.html', form=form)

@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    generated_file = GeneratedFile.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not generated_file:
        flash('File not found.', 'error')
        return redirect(url_for('dashboard'))
    
    if not os.path.exists(generated_file.file_path):
        flash('File no longer exists on disk.', 'error')
        return redirect(url_for('dashboard'))
    
    return send_file(generated_file.file_path, as_attachment=True, download_name=generated_file.filename)

@app.route('/delete/<int:file_id>')
@login_required
def delete_file(file_id):
    generated_file = GeneratedFile.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not generated_file:
        flash('File not found.', 'error')
        return redirect(url_for('dashboard'))
    
    # Delete file from disk
    if os.path.exists(generated_file.file_path):
        try:
            os.remove(generated_file.file_path)
        except Exception as e:
            logging.error(f"Error deleting file: {str(e)}")
    
    # Delete from database
    db.session.delete(generated_file)
    db.session.commit()
    
    flash('File deleted successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
