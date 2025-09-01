// Main JavaScript functionality for Seedsowers Ministry platform

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    initializeFlashMessages();
    initializeProgressCircles();
    initializeFileUploads();
    initializeModals();
    initializeForms();
});

// Flash message handling
function initializeFlashMessages() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        // Auto-hide success messages after 5 seconds
        if (alert.classList.contains('alert-success')) {
            setTimeout(() => {
                hideAlert(alert);
            }, 5000);
        }
        
        // Auto-hide info messages after 7 seconds
        if (alert.classList.contains('alert-info')) {
            setTimeout(() => {
                hideAlert(alert);
            }, 7000);
        }
    });
}

function hideAlert(alert) {
    alert.style.transform = 'translateX(100%)';
    alert.style.opacity = '0';
    setTimeout(() => {
        if (alert.parentElement) {
            alert.parentElement.removeChild(alert);
        }
    }, 300);
}

// Progress circle animations
function initializeProgressCircles() {
    const progressCircles = document.querySelectorAll('.circle-progress');
    
    progressCircles.forEach(circle => {
        const percent = circle.dataset.percent || 0;
        const degree = (percent / 100) * 360;
        
        // Animate the progress circle
        setTimeout(() => {
            circle.style.background = `conic-gradient(var(--primary-color) ${degree}deg, var(--gray-200) ${degree}deg)`;
        }, 500);
    });
}

// File upload functionality
function initializeFileUploads() {
    const fileUploadAreas = document.querySelectorAll('.file-upload-area');
    
    fileUploadAreas.forEach(area => {
        const fileInput = area.querySelector('input[type="file"]');
        if (!fileInput) return;
        
        // Click to select file
        area.addEventListener('click', (e) => {
            if (e.target !== fileInput) {
                fileInput.click();
            }
        });
        
        // Drag and drop functionality
        area.addEventListener('dragover', (e) => {
            e.preventDefault();
            area.classList.add('drag-over');
        });
        
        area.addEventListener('dragleave', (e) => {
            e.preventDefault();
            area.classList.remove('drag-over');
        });
        
        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                updateFileDisplay(area, files[0]);
            }
        });
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                updateFileDisplay(area, e.target.files[0]);
            }
        });
    });
}

function updateFileDisplay(uploadArea, file) {
    const placeholder = uploadArea.querySelector('.upload-placeholder');
    if (!placeholder) return;
    
    const fileSize = (file.size / 1024 / 1024).toFixed(1);
    const fileIcon = getFileIcon(file.name);
    
    placeholder.innerHTML = `
        <i class="fas ${fileIcon}"></i>
        <p><strong>${file.name}</strong></p>
        <p class="upload-hint">${fileSize} MB</p>
    `;
}

function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    
    switch (extension) {
        case 'pdf':
            return 'fa-file-pdf';
        case 'doc':
        case 'docx':
            return 'fa-file-word';
        case 'txt':
            return 'fa-file-alt';
        case 'mp3':
        case 'wav':
        case 'ogg':
            return 'fa-file-audio';
        case 'mp4':
        case 'avi':
        case 'mov':
            return 'fa-file-video';
        default:
            return 'fa-file';
    }
}

// Modal functionality
function initializeModals() {
    const modals = document.querySelectorAll('.modal');
    const modalTriggers = document.querySelectorAll('[data-modal]');
    const modalCloses = document.querySelectorAll('.modal-close');
    
    // Modal triggers
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            const modalId = trigger.dataset.modal;
            openModal(modalId);
        });
    });
    
    // Modal close buttons
    modalCloses.forEach(closeBtn => {
        closeBtn.addEventListener('click', () => {
            const modal = closeBtn.closest('.modal');
            closeModal(modal.id);
        });
    });
    
    // Close modal when clicking outside
    modals.forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });
    
    // Close modal with escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal[style*="flex"]');
            if (openModal) {
                closeModal(openModal.id);
            }
        }
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Form handling
function initializeForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
}

function handleFormSubmit(e) {
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (submitBtn) {
        // Show loading state
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        submitBtn.disabled = true;
        
        // Reset button after 5 seconds if form hasn't completed
        setTimeout(() => {
            if (submitBtn.disabled) {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        }, 5000);
    }
}

// API helper functions
async function apiRequest(method, url, data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include'
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        return await response.text();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Progress tracking functions
async function markFileComplete(courseId, fileId) {
    try {
        await apiRequest('POST', '/api/mark-complete', {
            course_id: courseId,
            file_id: fileId
        });
        
        // Show success message
        showNotification('File marked as completed!', 'success');
        
        // Reload page to update progress
        setTimeout(() => {
            window.location.reload();
        }, 1000);
        
    } catch (error) {
        showNotification('Failed to mark file as complete. Please try again.', 'error');
    }
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.innerHTML = `
        <span class="alert-icon">
            ${type === 'success' ? '<i class="fas fa-check-circle"></i>' : 
              type === 'error' ? '<i class="fas fa-exclamation-triangle"></i>' : 
              '<i class="fas fa-info-circle"></i>'}
        </span>
        <span class="alert-message">${message}</span>
        <button class="alert-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add to flash messages container or create one
    let flashContainer = document.querySelector('.flash-messages');
    if (!flashContainer) {
        flashContainer = document.createElement('div');
        flashContainer.className = 'flash-messages';
        document.body.appendChild(flashContainer);
    }
    
    flashContainer.appendChild(notification);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideAlert(notification);
    }, 5000);
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Admin panel functionality
function initializeAdminPanel() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.dataset.tab;
            
            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update active tab content
            tabContents.forEach(content => content.classList.remove('active'));
            const targetContent = document.getElementById(tabId + '-tab');
            if (targetContent) {
                targetContent.classList.add('active');
            }
            
            // Load tab content
            loadTabContent(tabId);
        });
    });
}

function loadTabContent(tabId) {
    switch (tabId) {
        case 'courses':
            loadAdminCourses();
            break;
        case 'users':
            loadAdminUsers();
            break;
        case 'submissions':
            loadAdminSubmissions();
            break;
    }
}

async function loadAdminCourses() {
    const container = document.getElementById('coursesList');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading courses...</div>';
    
    try {
        const courses = await apiRequest('GET', '/api/admin/courses');
        displayAdminCourses(courses);
    } catch (error) {
        container.innerHTML = '<div class="error">Failed to load courses</div>';
    }
}

async function loadAdminUsers() {
    const container = document.getElementById('usersList');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading users...</div>';
    
    try {
        const users = await apiRequest('GET', '/api/admin/users');
        displayAdminUsers(users);
    } catch (error) {
        container.innerHTML = '<div class="error">Failed to load users</div>';
    }
}

async function loadAdminSubmissions() {
    const container = document.getElementById('submissionsList');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading submissions...</div>';
    
    try {
        const submissions = await apiRequest('GET', '/api/admin/submissions/pending');
        displayAdminSubmissions(submissions);
    } catch (error) {
        container.innerHTML = '<div class="error">Failed to load submissions</div>';
    }
}

function displayAdminCourses(courses) {
    const container = document.getElementById('coursesList');
    if (!container) return;
    
    if (courses.length === 0) {
        container.innerHTML = '<div class="empty-state">No courses found</div>';
        return;
    }
    
    const coursesHTML = courses.map(course => `
        <div class="admin-course-item">
            <h4>${course.title}</h4>
            <p>${course.description}</p>
            <div class="course-meta">
                <span>Order: ${course.order}</span>
                <span>Duration: ${course.duration}</span>
                <span>Status: ${course.is_active ? 'Active' : 'Inactive'}</span>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = coursesHTML;
}

function displayAdminUsers(users) {
    const container = document.getElementById('usersList');
    if (!container) return;
    
    if (users.length === 0) {
        container.innerHTML = '<div class="empty-state">No users found</div>';
        return;
    }
    
    const usersHTML = users.map(user => `
        <div class="admin-user-item">
            <div class="user-info">
                <h4>${user.first_name} ${user.last_name}</h4>
                <p>${user.email}</p>
                <span class="user-role">${user.role}</span>
            </div>
            <div class="user-actions">
                <button class="btn btn-sm ${user.is_active ? 'btn-outline' : 'btn-primary'}" 
                        onclick="toggleUserStatus('${user.id}', ${!user.is_active})">
                    ${user.is_active ? 'Deactivate' : 'Activate'}
                </button>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = usersHTML;
}

function displayAdminSubmissions(submissions) {
    const container = document.getElementById('submissionsList');
    if (!container) return;
    
    if (submissions.length === 0) {
        container.innerHTML = '<div class="empty-state">No pending submissions</div>';
        return;
    }
    
    const submissionsHTML = submissions.map(submission => `
        <div class="admin-submission-item">
            <h4>${submission.file_name}</h4>
            <p>Course: ${submission.course_title || 'Unknown'}</p>
            <p>Student: ${submission.student_name || 'Unknown'}</p>
            <p>Submitted: ${formatDate(submission.submitted_at)}</p>
            <div class="submission-actions">
                <button class="btn btn-primary btn-sm" onclick="reviewSubmission('${submission.id}', 'approved')">
                    Approve
                </button>
                <button class="btn btn-outline btn-sm" onclick="reviewSubmission('${submission.id}', 'rejected')">
                    Reject
                </button>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = submissionsHTML;
}

async function toggleUserStatus(userId, isActive) {
    try {
        await apiRequest('PUT', `/api/admin/users/${userId}/status`, { is_active: isActive });
        showNotification(`User ${isActive ? 'activated' : 'deactivated'} successfully`, 'success');
        loadAdminUsers(); // Reload the users list
    } catch (error) {
        showNotification('Failed to update user status', 'error');
    }
}

async function reviewSubmission(submissionId, status) {
    const comments = prompt(`${status === 'approved' ? 'Approve' : 'Reject'} this submission. Add comments (optional):`);
    
    try {
        await apiRequest('PUT', `/api/admin/submissions/${submissionId}/review`, {
            status: status,
            review_comments: comments || ''
        });
        
        showNotification(`Submission ${status} successfully`, 'success');
        loadAdminSubmissions(); // Reload the submissions list
    } catch (error) {
        showNotification('Failed to review submission', 'error');
    }
}

// Initialize admin panel if on admin page
if (window.location.pathname.includes('/admin')) {
    document.addEventListener('DOMContentLoaded', initializeAdminPanel);
}

// Global functions for HTML onclick handlers
window.markFileComplete = markFileComplete;
window.openModal = openModal;
window.closeModal = closeModal;
window.toggleUserStatus = toggleUserStatus;
window.reviewSubmission = reviewSubmission;