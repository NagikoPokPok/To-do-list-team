"""
Simple Email Service for OTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD") 
        self.from_email = os.getenv("EMAIL_FROM")
        self.from_name = "Todo List Team"

    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: str = None
    ) -> bool:
        """Send an email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # Send email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()

            print(f"✅ Email sent successfully to {to_email}")
            return True

        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_otp_email(self, to_email: str, otp_code: str, purpose: str) -> bool:
        """Send OTP verification email"""
        subject_map = {
            'registration': 'Xác thực tài khoản - Todo List',
            'password_reset': 'Đặt lại mật khẩu - Todo List'
        }
        
        subject = subject_map.get(purpose, 'Mã xác thực - Todo List')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{subject}</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0;">Todo List</h1>
            </div>
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #dee2e6;">
                <h2 style="color: #333; margin-top: 0;">Mã xác thực của bạn</h2>
                <p style="color: #666; font-size: 16px;">
                    {'Chào mừng bạn đến với Todo List! ' if purpose == 'registration' else 'Bạn đã yêu cầu đặt lại mật khẩu. '}
                    Vui lòng sử dụng mã xác thực dưới đây:
                </p>
                <div style="background-color: white; border: 2px solid #dc3545; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
                    <span style="font-size: 32px; font-weight: bold; color: #dc3545; letter-spacing: 5px;">{otp_code}</span>
                </div>
                <p style="color: #666; font-size: 14px;">
                    Mã này sẽ hết hạn sau 10 phút. Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email này.
                </p>
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    Email này được gửi tự động, vui lòng không trả lời.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Todo List - Mã xác thực
        
        Mã xác thực của bạn: {otp_code}
        
        Mã này sẽ hết hạn sau 10 phút.
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)

# Global email service instance
email_service = EmailService()