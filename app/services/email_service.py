"""
Email Service - Gửi email OTP và thông báo
Sử dụng SMTP để gửi email xác thực 2FA
"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from ..config import settings


class EmailService:
    """Service để gửi email"""
    
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.username = settings.smtp_username
        self.password = settings.smtp_password
        self.from_email = settings.email_from
    
    async def send_email(
        self, 
        to_emails: List[str], 
        subject: str, 
        body: str, 
        is_html: bool = False
    ) -> bool:
        """
        Gửi email
        
        Args:
            to_emails: Danh sách email người nhận
            subject: Tiêu đề email
            body: Nội dung email
            is_html: True nếu nội dung là HTML
            
        Returns:
            bool: True nếu gửi thành công
        """
        try:
            # Tạo message
            message = MIMEMultipart()
            message["From"] = self.from_email
            message["To"] = ", ".join(to_emails)
            message["Subject"] = subject
            
            # Thêm nội dung
            if is_html:
                message.attach(MIMEText(body, "html"))
            else:
                message.attach(MIMEText(body, "plain"))
            
            # Gửi email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_server,
                port=self.smtp_port,
                start_tls=True,
                username=self.username,
                password=self.password,
            )
            
            return True
            
        except Exception as e:
            print(f"Lỗi gửi email: {e}")
            return False
    
    async def send_otp_email(self, email: str, otp: str, username: str) -> bool:
        """
        Gửi email chứa OTP xác thực
        
        Args:
            email: Email người nhận
            otp: Mã OTP 6 số
            username: Tên người dùng
            
        Returns:
            bool: True nếu gửi thành công
        """
        subject = f"[{settings.app_name}] Mã xác thực đăng nhập"
        
        body = f"""
        Chào {username},
        
        Mã xác thực đăng nhập của bạn là: {otp}
        
        Mã này có hiệu lực trong 5 phút.
        
        Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email này.
        
        Trân trọng,
        Đội ngũ {settings.app_name}
        """
        
        return await self.send_email([email], subject, body.strip())
    
    async def send_welcome_email(self, email: str, username: str) -> bool:
        """
        Gửi email chào mừng user mới
        
        Args:
            email: Email người nhận
            username: Tên người dùng
            
        Returns:
            bool: True nếu gửi thành công
        """
        subject = f"Chào mừng bạn đến với {settings.app_name}!"
        
        body = f"""
        Chào {username},
        
        Chào mừng bạn đến với {settings.app_name}!
        
        Tài khoản của bạn đã được tạo thành công. Bạn có thể bắt đầu sử dụng ứng dụng để:
        - Tạo và quản lý các công việc (tasks)
        - Tham gia các nhóm làm việc
        - Theo dõi tiến độ công việc
        
        Để tăng cường bảo mật, chúng tôi khuyến khích bạn bật xác thực 2 yếu tố (2FA) 
        trong phần cài đặt tài khoản.
        
        Nếu có bất kỳ câu hỏi nào, đừng ngần ngại liên hệ với chúng tôi.
        
        Trân trọng,
        Đội ngũ {settings.app_name}
        """
        
        return await self.send_email([email], subject, body.strip())
    
    async def send_task_assignment_email(
        self, 
        assignee_email: str, 
        assignee_name: str,
        task_title: str,
        assigner_name: str,
        due_date: Optional[str] = None
    ) -> bool:
        """
        Gửi email thông báo được gán task mới
        
        Args:
            assignee_email: Email người được gán task
            assignee_name: Tên người được gán task
            task_title: Tiêu đề task
            assigner_name: Tên người gán task
            due_date: Hạn hoàn thành (optional)
            
        Returns:
            bool: True nếu gửi thành công
        """
        subject = f"[{settings.app_name}] Bạn được gán công việc mới: {task_title}"
        
        body = f"""
        Chào {assignee_name},
        
        Bạn vừa được {assigner_name} gán một công việc mới:
        
        Tiêu đề: {task_title}
        """
        
        if due_date:
            body += f"Hạn hoàn thành: {due_date}\n"
        
        body += f"""
        
        Vui lòng đăng nhập vào {settings.app_name} để xem chi tiết và cập nhật tiến độ.
        
        Trân trọng,
        Đội ngũ {settings.app_name}
        """
        
        return await self.send_email([assignee_email], subject, body.strip())
    
    async def send_notification_email(
        self,
        email: str,
        username: str,
        title: str,
        message: str,
        action_url: Optional[str] = None
    ) -> bool:
        """
        Gửi email thông báo chung
        
        Args:
            email: Email người nhận
            username: Tên người dùng
            title: Tiêu đề thông báo
            message: Nội dung thông báo
            action_url: URL hành động (optional)
            
        Returns:
            bool: True nếu gửi thành công
        """
        subject = f"[{settings.app_name}] {title}"
        
        body = f"""
        Chào {username},
        
        {message}
        """
        
        if action_url:
            body += f"""
        
        Để xem chi tiết, vui lòng truy cập: {action_url}
        """
        
        body += f"""
        
        Trân trọng,
        Đội ngũ {settings.app_name}
        """
        
        return await self.send_email([email], subject, body.strip())
    
    async def send_team_invite_email(
        self,
        email: str,
        team_name: str,
        manager_name: str,
        invite_link: str
    ) -> bool:
        """
        Gửi email mời tham gia team
        
        Args:
            email: Email người được mời
            team_name: Tên team
            manager_name: Tên manager team
            invite_link: Link mời tham gia
            
        Returns:
            bool: True nếu gửi thành công
        """
        subject = f"[{settings.app_name}] Lời mời tham gia team '{team_name}'"
        
        body = f"""
        Xin chào,
        
        {manager_name} đã mời bạn tham gia team '{team_name}' trên {settings.app_name}.
        
        Để tham gia team, vui lòng:
        1. Truy cập link sau: {invite_link}
        2. Đăng nhập vào tài khoản của bạn
        3. Xác nhận tham gia team
        
        Nếu bạn chưa có tài khoản, vui lòng đăng ký tại: {settings.app_url}/register
        
        Trân trọng,
        Đội ngũ {settings.app_name}
        """
        
        return await self.send_email([email], subject, body.strip())


# Tạo instance global
email_service = EmailService()