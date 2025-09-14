from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=64, message='Username must be between 3 and 64 characters.')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please choose a different one.')

class TextToSpeechForm(FlaskForm):
    text = TextAreaField('Text to Convert', validators=[
        DataRequired(),
        Length(min=1, max=5000, message='Text must be between 1 and 5000 characters.')
    ], render_kw={"placeholder": "Enter the text you want to convert to speech...", "rows": 6})
    submit = SubmitField('Generate Audio')

class TextToVideoForm(FlaskForm):
    text = TextAreaField('Text for Video', validators=[
        DataRequired(),
        Length(min=1, max=1000, message='Text must be between 1 and 1000 characters.')
    ], render_kw={"placeholder": "Enter the text to display in the video...", "rows": 4})
    background_color = SelectField('Background Color', choices=[
        ('#000000', 'Black'),
        ('#FFFFFF', 'White'),
        ('#FF0000', 'Red'),
        ('#00FF00', 'Green'),
        ('#0000FF', 'Blue'),
        ('#FFFF00', 'Yellow'),
        ('#FF00FF', 'Magenta'),
        ('#00FFFF', 'Cyan')
    ], default='#000000')
    text_color = SelectField('Text Color', choices=[
        ('#FFFFFF', 'White'),
        ('#000000', 'Black'),
        ('#FF0000', 'Red'),
        ('#00FF00', 'Green'),
        ('#0000FF', 'Blue'),
        ('#FFFF00', 'Yellow'),
        ('#FF00FF', 'Magenta'),
        ('#00FFFF', 'Cyan')
    ], default='#FFFFFF')
    duration = SelectField('Video Duration (seconds)', choices=[
        ('5', '5 seconds'),
        ('10', '10 seconds'),
        ('15', '15 seconds'),
        ('30', '30 seconds')
    ], default='10')
    submit = SubmitField('Generate Video')
