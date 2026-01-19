from flask import jsonify, current_app
from flask_jwt_extended import create_access_token
import pyotp
import datetime
import MySQLdb
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random

# DB config (match api.py)
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "passwd": os.environ.get("DB_PASSWORD", ""),
    "db": os.environ.get("DB_NAME", "chatbotdb"),
    "charset": "utf8mb4"
}

def get_db_connection():
    try:
        return MySQLdb.connect(**DB_CONFIG)
    except MySQLdb.Error as e:
        current_app.logger.error(f"Database connection failed: {e}")
        raise

def generate_otp(email):
    """Generate and store a 6-digit OTP for a user"""
    db = get_db_connection()
    cursor = db.cursor()

    # Clean up ALL old OTPs for this email (expired or not)
    # This prevents confusion when user requests multiple OTPs
    cursor.execute("DELETE FROM otp_tokens WHERE email = %s", (email,))
    db.commit()
    current_app.logger.info(f"Deleted old OTPs for {email}")

    # Generate a simple 6-digit OTP
    otp_code = str(random.randint(100000, 999999))

    # Store OTP - use local time to match MySQL NOW()
    expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
    cursor.execute(
        "INSERT INTO otp_tokens (email, otp_code, expires_at, created_at) VALUES (%s, %s, %s, NOW())",
        (email, otp_code, expires_at)
    )
    db.commit()
    cursor.close()
    db.close()

    # Send OTP via email
    send_otp_email(email, otp_code)

    return otp_code

def send_otp_email(email, otp_code):
    """
    Send OTP code to user's email address
    
    Args:
        email (str): Recipient's email address
        otp_code (str): The OTP code to send
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get email configuration from app config or environment variables
        smtp_server = current_app.config.get('MAIL_SERVER', os.environ.get('MAIL_SERVER', 'smtp.gmail.com'))
        smtp_port = current_app.config.get('MAIL_PORT', int(os.environ.get('MAIL_PORT', 587)))
        mail_username = current_app.config.get('MAIL_USERNAME') or os.environ.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD') or os.environ.get('MAIL_PASSWORD')
        mail_default_sender = current_app.config.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_DEFAULT_SENDER') or mail_username
        
        # Validate email configuration
        if not mail_username or not mail_password:
            current_app.logger.error("Email credentials not configured. Set MAIL_USERNAME and MAIL_PASSWORD in environment.")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Your OTP Code for AI ChatBot"
        msg['From'] = mail_default_sender
        msg['To'] = email
        
        # Create HTML content
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .otp-code {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #6366f1;
                    text-align: center;
                    margin: 20px 0;
                    padding: 10px;
                    background-color: #f0f0f0;
                    border-radius: 5px;
                }}
                .footer {{
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>AI ChatBot Verification Code</h2>
                <p>Hello,</p>
                <p>Your One-Time Password (OTP) for verification is:</p>
                <div class="otp-code">{otp_code}</div>
                <p>This code will expire in 5 minutes. Please do not share this code with anyone.</p>
                <p>If you didn't request this code, please ignore this email.</p>
                <div class="footer">
                    <p>Best regards,<br>AI ChatBot Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create plain text content
        text = f"""
        AI ChatBot Verification Code
        
        Hello,
        
        Your One-Time Password (OTP) for verification is: {otp_code}
        
        This code will expire in 5 minutes. Please do not share this code with anyone.
        
        If you didn't request this code, please ignore this email.
        
        Best regards,
        AI ChatBot Team
        """
        
        # Attach both HTML and plain text versions
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(mail_username, mail_password)
            server.send_message(msg)
        
        current_app.logger.info(f"OTP email sent to {email}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send OTP email to {email}: {str(e)}")
        return False

def verify_otp(email, otp_code):
    """Verify OTP code for a user"""
    db = get_db_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute(
        "SELECT * FROM otp_tokens WHERE email = %s AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1",
        (email,)
    )
    otp_token = cursor.fetchone()

    if otp_token and otp_token['otp_code'] == otp_code:
        cursor.execute("DELETE FROM otp_tokens WHERE id = %s", (otp_token['id'],))
        db.commit()
        cursor.close()
        db.close()
        return True

    cursor.close()
    db.close()
    return False

def create_user(email, password, full_name, date_of_birth=None):
    """Create a new user"""
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        db.close()
        return None, "User already exists"

    hashed_password = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (email, password_hash, full_name, date_of_birth) VALUES (%s, %s, %s, %s)",
        (email, hashed_password, full_name, date_of_birth)
    )
    db.commit()
    user_id = cursor.lastrowid
    cursor.close()
    db.close()

    return {'user_id': user_id, 'email': email, 'full_name': full_name}, None

def authenticate_user(email, password):
    """Authenticate a user"""
    db = get_db_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT id, email, full_name, password_hash FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if user and check_password_hash(user['password_hash'], password):
        user['user_id'] = user['id']
        return user, None
    return None, "Invalid credentials"

def generate_token(user):
    """Generate JWT token for a user"""
    return create_access_token(identity={
        'user_id': user['user_id'],
        'email': user['email'],
        'full_name': user['full_name']
    })