// Todo List Application - Main JavaScript
// Quản lý authentication, API calls và UI interactions

class TodoApp {
    async removeFromTeam(teamId, memberId) {
        try {
            const response = await this.apiCall(`/teams/${teamId}/members/${memberId}`, 'DELETE');
            this.showToast('Xóa thành viên thành công!', 'success');
            document.body.classList.remove('modal-open');
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            return response;
        } catch (error) {
            console.error('Remove from team error:', error);
            this.showToast(error.message, 'error');
            throw error;
        }
    }
    // === Invitation Notification ===
    async getMyInvitations() {
        if (!this.token) return [];
        try {
            return await this.apiCall('/invitations/my');
        } catch (e) {
            return [];
        }
    }

    async acceptInvitation(token) {
        try {
            return await this.apiCall(`/invitations/accept/${token}`, 'GET');
        } catch (e) {
            throw e;
        }
    }
    

    constructor() {
        this.baseURL = '/api/v1';
        this.token = localStorage.getItem('access_token');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
        
        this.init();
    }
    
    init() {
        // Khởi tạo ứng dụng
        this.setupEventListeners();
        this.checkAuthStatus();
        this.updateNavigation();
    }
    
    // === Authentication Methods ===
    
    async login(email, password, totpCode = null, emailOtp = null) {
        try {
            this.showLoading();
            
            const response = await fetch(`${this.baseURL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    totp_code: totpCode,
                    email_otp: emailOtp
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                if (response.status === 202) {
                    // Cần OTP email
                    this.showToast('Mã OTP đã được gửi qua email', 'info');
                    return { needsOTP: true };
                }
                throw new Error(data.detail || 'Đăng nhập thất bại');
            }
            
            // Lưu token và thông tin user
            this.token = data.access_token;
            localStorage.setItem('access_token', this.token);
            
            // Lấy thông tin user
            await this.getCurrentUser();
            
            this.showToast('Đăng nhập thành công!', 'success');
            
            // Redirect về dashboard
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);
            
            return { success: true };
            
        } catch (error) {
            console.error('Login error:', error);
            this.showToast(error.message, 'error');
            return { success: false, error: error.message };
        } finally {
            this.hideLoading();
        }
    }
    
    async register(userData) {
        try {
            this.showLoading();
            
            const response = await fetch(`${this.baseURL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Đăng ký thất bại');
            }
            
            this.showToast('Đăng ký thành công! Vui lòng đăng nhập.', 'success');
            
            // Redirect về login page
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
            
            return { success: true };
            
        } catch (error) {
            console.error('Register error:', error);
            this.showToast(error.message, 'error');
            return { success: false, error: error.message };
        } finally {
            this.hideLoading();
        }
    }
    
    async getCurrentUser() {
        try {
            const response = await this.apiCall('/auth/me', 'GET');
            this.user = response;
            localStorage.setItem('user', JSON.stringify(this.user));
            return this.user;
        } catch (error) {
            console.error('Get current user error:', error);
            this.logout();
            return null;
        }
    }
    
    logout() {
        // Xóa token và user info
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        this.token = null;
        this.user = null;
        
        this.showToast('Đã đăng xuất thành công', 'info');
        
        // Redirect về trang chủ
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
    }
    
    // === API Methods ===
    
    async apiCall(endpoint, method = 'GET', body = null) {
        const config = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        // Thêm authorization header nếu có token
        if (this.token) {
            config.headers.Authorization = `Bearer ${this.token}`;
        }
        
        // Thêm body nếu có
        if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            config.body = JSON.stringify(body);
        }
        
        const response = await fetch(`${this.baseURL}${endpoint}`, config);
        
        if (response.status === 401) {
            // Token hết hạn hoặc không hợp lệ
            this.logout();
            throw new Error('Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại.');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || `HTTP error! status: ${response.status}`);
        }
        
        return data;
    }
    
    // === Task Methods ===
    
    async getTasks(filters = {}) {
        try {
            const queryParams = new URLSearchParams();
            
            Object.keys(filters).forEach(key => {
                if (filters[key] !== null && filters[key] !== '') {
                    queryParams.append(key, filters[key]);
                }
            });
            
            const endpoint = `/tasks?${queryParams.toString()}`;
            return await this.apiCall(endpoint, 'GET');
        } catch (error) {
            console.error('Get tasks error:', error);
            this.showToast(error.message, 'error');
            return [];
        }
    }
    
    async createTask(taskData) {
        try {
            const response = await this.apiCall('/tasks/', 'POST', taskData);
            this.showToast('Tạo công việc thành công!', 'success');
            return response;
        } catch (error) {
            console.error('Create task error:', error);
            this.showToast(error.message, 'error');
            throw error;
        }
    }
    
    async updateTask(taskId, taskData) {
        try {
            const response = await this.apiCall(`/tasks/${taskId}`, 'PUT', taskData);
            this.showToast('Cập nhật công việc thành công!', 'success');
            return response;
        } catch (error) {
            console.error('Update task error:', error);
            this.showToast(error.message, 'error');
            throw error;
        }
    }
    
    async deleteTask(taskId) {
        try {
            await this.apiCall(`/tasks/${taskId}`, 'DELETE');
            this.showToast('Xóa công việc thành công!', 'success');
            return true;
        } catch (error) {
            console.error('Delete task error:', error);
            this.showToast(error.message, 'error');
            return false;
        }
    }
    
    // === Team Methods ===
    
    async getTeams() {
        try {
            return await this.apiCall('/teams/', 'GET');
        } catch (error) {
            console.error('Get teams error:', error);
            this.showToast(error.message, 'error');
            return [];
        }
    }
    
    async createTeam(teamData) {
        try {
            const response = await this.apiCall('/teams/', 'POST', teamData);
            this.showToast('Tạo nhóm thành công!', 'success');
            return response;
        } catch (error) {
            console.error('Create team error:', error);
            this.showToast(error.message, 'error');
            throw error;
        }
    }

    async updateTeam(teamId, teamData) {
        try {
            const response = await this.apiCall(`/teams/${teamId}`, 'PUT', teamData);
            this.showToast('Cập nhật nhóm thành công!', 'success');
            return response;
        } catch (error) {
            console.error('Update team error:', error);
            this.showToast(error.message, 'error');
            throw error;
        }
    }

    async deleteTeam(teamId) {
        try {
            const response = await this.apiCall(`/teams/${teamId}`, 'DELETE');
            this.showToast('Xóa nhóm thành công!', 'success');
            return response;
        } catch (error) {
            console.error('Delete team error:', error);
            this.showToast(error.message, 'error');
            throw error;
        }
    }

    async getTeamMembers(teamId) {
        try {
            const members = await this.apiCall(`/teams/${teamId}/members`);
            console.log('Team members for team', teamId, members);
            if (!Array.isArray(members)) {
                throw new Error('Dữ liệu thành viên nhóm trả về không phải mảng!');
            }
            return members;
        } catch (error) {
            console.error('Get team members error:', error);
            this.showToast('Không thể tải danh sách thành viên', 'error');
            throw error;
        }
    }
    
    async getUsers() {
        try {
            return await this.apiCall('/auth/users');
        } catch (error) {
            console.error('Get users error:', error);
            this.showToast('Không thể tải danh sách người dùng', 'error');
            throw error;
        }
    }

    async inviteToTeam(teamId, inviteData) {
        try {
            const response = await this.apiCall(`/invitations/invite`, 'POST', { ...inviteData, team_id: teamId });
            this.showToast('Gửi lời mời thành công!', 'success');
            return response;
        } catch (error) {
            console.error('Invite to team error:', error);
            this.showToast(error.message, 'error');
            throw error;
        }
    }

    // Đã loại bỏ chức năng xóa thành viên khỏi nhóm

    async leaveTeam(teamId) {
        try {
            const response = await this.apiCall(`/teams/${teamId}/leave`, 'POST');
            this.showToast('Rời nhóm thành công!', 'success');
            return response;
        } catch (error) {
            console.error('Leave team error:', error);
            this.showToast(error.message, 'error');
            throw error;
        }
    }

    async getPendingInvitations(teamId) {
        try {
            const allInvitations = await this.apiCall('/invitations/my');
            console.log('All invitations:', allInvitations);
            if (!Array.isArray(allInvitations)) {
                throw new Error('Dữ liệu lời mời trả về không phải mảng!');
            }
            const filtered = allInvitations.filter(invite => invite.team_id == teamId);
            console.log('Filtered invitations for team', teamId, filtered);
            return filtered;
        } catch (error) {
            console.error('Get pending invitations error:', error);
            return [];
        }
    }

    async cancelInvitation(invitationId) {
        try {
            const response = await this.apiCall(`/invitations/${invitationId}`, 'DELETE');
            this.showToast('Hủy lời mời thành công!', 'success');
            return response;
        } catch (error) {
            console.error('Cancel invitation error:', error);
            this.showToast(error.message, 'error');
            throw error;
        }
    }
    
    // === 2FA Methods ===
    
    async enable2FA() {
        try {
            const response = await this.apiCall('/auth/enable-2fa', 'POST');
            return response;
        } catch (error) {
            console.error('Enable 2FA error:', error);
            this.showToast(error.message, 'error');
            throw error;
        }
    }
    
    async verify2FA(totpCode) {
        try {
            const response = await this.apiCall('/auth/verify-2fa', 'POST', {
                totp_code: totpCode
            });
            this.showToast('2FA đã được bật thành công!', 'success');
            return response;
        } catch (error) {
            console.error('Verify 2FA error:', error);
            this.showToast(error.message, 'error');
            throw error;
        }
    }
    
    async disable2FA(totpCode) {
        try {
            const response = await this.apiCall('/auth/disable-2fa', 'POST', {
                totp_code: totpCode
            });
            this.showToast('2FA đã được tắt!', 'info');
            return response;
        } catch (error) {
            console.error('Disable 2FA error:', error);
            this.showToast(error.message, 'error');
            throw error;
        }
    }
    
    // === UI Helper Methods ===
    
    checkAuthStatus() {
        // Kiểm tra xem user đã đăng nhập chưa
        const currentPath = window.location.pathname;
        const publicPaths = ['/', '/login', '/register'];
        
        if (!this.token && !publicPaths.includes(currentPath)) {
            // Chưa đăng nhập và đang ở trang cần authentication
            window.location.href = '/login';
        }
        
        if (this.token && (currentPath === '/login' || currentPath === '/register')) {
            // Đã đăng nhập nhưng đang ở trang login/register
            window.location.href = '/dashboard';
        }
    }
    
    updateNavigation() {
        const userDropdown = document.getElementById('userDropdown');
        const loginLink = document.getElementById('loginLink');
        const userName = document.getElementById('userName');
        
        if (this.user && userDropdown && loginLink && userName) {
            // Hiển thị thông tin user
            userName.textContent = this.user.full_name || this.user.email.split('@')[0];
            userDropdown.style.display = 'block';
            loginLink.style.display = 'none';
        } else if (userDropdown && loginLink) {
            // Hiển thị link đăng nhập
            userDropdown.style.display = 'none';
            loginLink.style.display = 'block';
        }
    }
    
    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastBody = toast.querySelector('.toast-body');
        const toastHeader = toast.querySelector('.toast-header');
        
        // Đặt nội dung
        toastBody.textContent = message;
        
        // Đặt màu theo loại
        toast.className = 'toast';
        switch (type) {
            case 'success':
                toast.classList.add('border-success');
                toastHeader.className = 'toast-header bg-success text-white';
                break;
            case 'error':
                toast.classList.add('border-danger');
                toastHeader.className = 'toast-header bg-danger text-white';
                break;
            case 'warning':
                toast.classList.add('border-warning');
                toastHeader.className = 'toast-header bg-warning text-dark';
                break;
            default:
                toast.classList.add('border-info');
                toastHeader.className = 'toast-header bg-info text-white';
        }
        
        // Hiển thị toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
    
    showLoading() {
        const loadingModal = document.getElementById('loadingModal');
        if (loadingModal) {
            const modal = new bootstrap.Modal(loadingModal);
            modal.show();
        }
    }
    
    hideLoading() {
        const loadingModal = document.getElementById('loadingModal');
        if (loadingModal) {
            const modal = bootstrap.Modal.getInstance(loadingModal);
            if (modal) {
                modal.hide();
            }
        }
    }
    
    formatDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        return date.toLocaleDateString('vi-VN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    getStatusBadgeClass(status) {
        const statusClasses = {
            'pending': 'badge-pending',
            'in_progress': 'badge-in-progress',
            'completed': 'badge-completed',
            'cancelled': 'badge-cancelled'
        };
        return statusClasses[status] || 'bg-secondary';
    }
    
    getPriorityBadgeClass(priority) {
        const priorityClasses = {
            'low': 'badge-low',
            'medium': 'badge-medium',
            'high': 'badge-high',
            'urgent': 'badge-urgent'
        };
        return priorityClasses[priority] || 'bg-secondary';
    }
    
    // === Event Listeners ===
    
    setupEventListeners() {
        // Global logout function
        window.logout = () => this.logout();
        
        // Form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.id === 'loginForm') {
                e.preventDefault();
                this.handleLoginForm(e.target);
            } else if (e.target.id === 'registerForm') {
                e.preventDefault();
                this.handleRegisterForm(e.target);
            }
        });
    }
    
    handleLoginForm(form) {
        const formData = new FormData(form);
        const email = formData.get('email');
        const password = formData.get('password');
        const totpCode = formData.get('totp_code');
        const emailOtp = formData.get('email_otp');
        
        this.login(email, password, totpCode, emailOtp);
    }
    
    handleRegisterForm(form) {
        const formData = new FormData(form);
        const userData = {
            email: formData.get('email'),
            password: formData.get('password'),
            full_name: formData.get('full_name'),
            phone_number: formData.get('phone_number')
        };
        
        // Kiểm tra password confirmation
        const confirmPassword = formData.get('confirm_password');
        if (userData.password !== confirmPassword) {
            this.showToast('Mật khẩu xác nhận không khớp', 'error');
            return;
        }
        
        this.register(userData);
    }
}

// Notification Bell logic
document.addEventListener('DOMContentLoaded', async function() {
    if (window.todoApp && todoApp.token) {
        await updateNotificationBell();
    }
});

async function updateNotificationBell() {
    const bell = document.getElementById('notificationBell');
    const countSpan = document.getElementById('notificationCount');
    const listDiv = document.getElementById('notificationList');
    if (!window.todoApp || !todoApp.token) {
        bell.style.display = 'none';
        return;
    }
    const invitations = await todoApp.getMyInvitations();
    if (invitations.length > 0) {
        bell.style.display = 'block';
        countSpan.style.display = 'inline-block';
        countSpan.textContent = invitations.length;
        listDiv.innerHTML = invitations.map(inv => `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <div><b>Lời mời vào nhóm</b></div>
                    <div class="small text-muted">${inv.email} - ${inv.created_at ? new Date(inv.created_at).toLocaleString() : ''}</div>
                </div>
                <button class="btn btn-sm btn-success ms-2" onclick="acceptInvitationFromBell('${inv.token}')">Tham gia</button>
            </div>
        `).join('');
    } else {
        bell.style.display = 'block';
        countSpan.style.display = 'none';
        listDiv.innerHTML = '<div class="text-center text-muted py-3">Không có thông báo nào.</div>';
    }
}

function toggleNotificationPopup(e) {
    e.preventDefault();
    const popup = document.getElementById('notificationPopup');
    popup.style.display = (popup.style.display === 'none' || !popup.style.display) ? 'block' : 'none';
}

function closeNotificationPopup() {
    document.getElementById('notificationPopup').style.display = 'none';
}

async function acceptInvitationFromBell(token) {
    try {
        await todoApp.acceptInvitation(token);
        closeNotificationPopup();
        await updateNotificationBell();
        todoApp.showToast('Bạn đã tham gia nhóm thành công!', 'success');
        // Reload lại trang để hiển thị team mới
        setTimeout(() => window.location.reload(), 800);
    } catch (e) {
        todoApp.showToast('Không thể tham gia nhóm: ' + (e.message || ''), 'error');
    }
}

// Khởi tạo ứng dụng khi DOM loaded
document.addEventListener('DOMContentLoaded', async () => {
    window.todoApp = new TodoApp();
    if (window.todoApp && window.todoApp.token) {
        await updateNotificationBell();
    }
});

// Export utility functions
window.formatDate = (dateString) => window.todoApp.formatDate(dateString);
window.getStatusBadgeClass = (status) => window.todoApp.getStatusBadgeClass(status);
window.getPriorityBadgeClass = (priority) => window.todoApp.getPriorityBadgeClass(priority);