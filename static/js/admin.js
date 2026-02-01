// static/js/admin.js
// Admin Dashboard Management for Entekhablock MVP

class AdminDashboard {
    constructor() {
        this.polls = [];
        this.stats = null;
        this.currentPage = 1;
        this.pollsPerPage = 10;
    }

    // Initialize admin dashboard
    init() {
        this.loadDashboardStats();
        this.loadPolls();
        this.setupEventListeners();
        this.setupUploadCSV();
        this.animateStatCards();
    }

    // Load dashboard statistics
    async loadDashboardStats() {
        try {
            const response = await fetch('/api/admin/stats');

            if (!response.ok) {
                throw new Error('خطا در دریافت آمار');
            }

            const data = await response.json();

            if (data.success) {
                this.stats = data.stats;
                this.renderStats();
            }
        } catch (error) {
            console.error('Error loading stats:', error);
            this.showNotification('خطا در بارگذاری آمار', 'error');
        }
    }

    // Load polls list
    async loadPolls() {
        this.showLoading(true);

        try {
            const response = await fetch('/api/admin/polls');

            if (!response.ok) {
                throw new Error('خطا در دریافت نظرسنجی‌ها');
            }

            const data = await response.json();

            if (data.success) {
                this.polls = data.polls;
                this.renderPolls();
            }
        } catch (error) {
            console.error('Error loading polls:', error);
            this.showNotification('خطا در بارگذاری نظرسنجی‌ها', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // Render statistics cards
    renderStats() {
        if (!this.stats) return;

        // Total polls
        const totalPollsElement = document.getElementById('stat-total-polls');
        if (totalPollsElement) {
            this.animateCounter(totalPollsElement, this.stats.total_polls);
        }

        // Active polls
        const activePollsElement = document.getElementById('stat-active-polls');
        if (activePollsElement) {
            this.animateCounter(activePollsElement, this.stats.active_polls);
        }

        // Total votes
        const totalVotesElement = document.getElementById('stat-total-votes');
        if (totalVotesElement) {
            this.animateCounter(totalVotesElement, this.stats.total_votes);
        }

        // Total voters
        const totalVotersElement = document.getElementById('stat-total-voters');
        if (totalVotersElement) {
            this.animateCounter(totalVotersElement, this.stats.total_voters);
        }
    }

    // Animate counter
    animateCounter(element, targetValue, duration = 1500) {
        const startValue = 0;
        const startTime = performance.now();

        const updateCounter = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentValue = Math.floor(startValue + (targetValue - startValue) * easeOutQuart);

            element.textContent = currentValue.toLocaleString('fa-IR');

            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = targetValue.toLocaleString('fa-IR');
            }
        };

        requestAnimationFrame(updateCounter);
    }

    // Render polls list
    renderPolls() {
        const pollsList = document.getElementById('polls-list');
        if (!pollsList) return;

        pollsList.innerHTML = '';

        if (this.polls.length === 0) {
            pollsList.innerHTML = `
                <div class="empty-state">
                    <span class="material-icons">ballot</span>
                    <p>هیچ نظرسنجی‌ای یافت نشد</p>
                    <button class="btn btn-primary" onclick="window.location.href='/admin/create-poll'">
                        <span class="material-icons">add</span>
                        ایجاد نظرسنجی جدید
                    </button>
                </div>
            `;
            return;
        }

        // Sort polls by creation date (newest first)
        const sortedPolls = [...this.polls].sort((a, b) =>
            new Date(b.created_at) - new Date(a.created_at)
        );

        sortedPolls.forEach(poll => {
            const pollCard = this.createPollCard(poll);
            pollsList.appendChild(pollCard);
        });
    }

    // Create poll card element
    createPollCard(poll) {
        const card = document.createElement('div');
        card.className = 'poll-card';
        card.dataset.pollId = poll.id;

        const statusClass = poll.is_active ? 'status-active' : 'status-inactive';
        const statusText = poll.is_active ? 'فعال' : 'غیرفعال';

        card.innerHTML = `
            <div class="poll-card-header">
                <div class="poll-info">
                    <h3 class="poll-title">${this.escapeHtml(poll.title)}</h3>
                    ${poll.description ? `<p class="poll-description">${this.escapeHtml(poll.description)}</p>` : ''}
                    <div class="poll-meta">
                        <span class="meta-item">
                            <span class="material-icons">how_to_vote</span>
                            ${poll.total_votes.toLocaleString('fa-IR')} رأی
                        </span>
                        <span class="meta-item">
                            <span class="material-icons">people</span>
                            ${poll.total_voters.toLocaleString('fa-IR')} رأی‌دهنده
                        </span>
                        <span class="meta-item">
                            <span class="material-icons">calendar_today</span>
                            ${this.formatDate(poll.created_at)}
                        </span>
                    </div>
                </div>
                <div class="poll-status">
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
            </div>
            <div class="poll-card-actions">
                <button class="btn btn-icon btn-view" onclick="adminDashboard.viewResults('${poll.id}')" title="مشاهده نتایج">
                    <span class="material-icons">bar_chart</span>
                </button>
                <button class="btn btn-icon btn-edit" onclick="adminDashboard.editPoll('${poll.id}')" title="ویرایش">
                    <span class="material-icons">edit</span>
                </button>
                <button class="btn btn-icon btn-toggle" onclick="adminDashboard.togglePollStatus('${poll.id}', ${!poll.is_active})" title="${poll.is_active ? 'غیرفعال کردن' : 'فعال کردن'}">
                    <span class="material-icons">${poll.is_active ? 'toggle_on' : 'toggle_off'}</span>
                </button>
                <button class="btn btn-icon btn-delete" onclick="adminDashboard.confirmDeletePoll('${poll.id}')" title="حذف">
                    <span class="material-icons">delete</span>
                </button>
            </div>
        `;

        return card;
    }

    // Setup event listeners
    setupEventListeners() {
        // Create poll button
        const createPollBtn = document.getElementById('create-poll-btn');
        if (createPollBtn) {
            createPollBtn.addEventListener('click', () => {
                window.location.href = '/admin/create-poll';
            });
        }

        // Refresh button
        const refreshBtn = document.getElementById('refresh-dashboard-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadDashboardStats();
                this.loadPolls();
                this.showNotification('داده‌ها به‌روزرسانی شد', 'success');
            });
        }

        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.logout();
            });
        }
    }

    // Setup CSV upload
    setupUploadCSV() {
        const uploadInput = document.getElementById('csv-upload-input');
        const uploadBtn = document.getElementById('upload-csv-btn');
        const uploadArea = document.getElementById('csv-upload-area');

        if (!uploadInput || !uploadBtn) return;

        // Click upload button
        uploadBtn.addEventListener('click', () => {
            uploadInput.click();
        });

        // File selection
        uploadInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.uploadCSVFile(file);
            }
        });

        // Drag and drop
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('drag-over');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('drag-over');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('drag-over');

                const file = e.dataTransfer.files[0];
                if (file && file.name.endsWith('.csv')) {
                    this.uploadCSVFile(file);
                } else {
                    this.showNotification('لطفاً یک فایل CSV انتخاب کنید', 'error');
                }
            });
        }
    }

    // Upload CSV file
    async uploadCSVFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        this.showLoading(true);

        try {
            const response = await fetch('/api/admin/upload-voters', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification(`${data.count.toLocaleString('fa-IR')} رأی‌دهنده با موفقیت آپلود شد`, 'success');
                this.loadDashboardStats();
            } else {
                this.showNotification(data.message || 'خطا در آپلود فایل', 'error');
            }
        } catch (error) {
            console.error('Error uploading CSV:', error);
            this.showNotification('خطا در ارتباط با سرور', 'error');
        } finally {
            this.showLoading(false);
            document.getElementById('csv-upload-input').value = '';
        }
    }

    // View poll results
    viewResults(pollId) {
        window.location.href = `/results?poll_id=${pollId}`;
    }

    // Edit poll
    editPoll(pollId) {
        window.location.href = `/admin/edit-poll/${pollId}`;
    }

    // Toggle poll status
    async togglePollStatus(pollId, newStatus) {
        try {
            const response = await fetch(`/api/admin/poll/${pollId}/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ is_active: newStatus })
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification(
                    newStatus ? 'نظرسنجی فعال شد' : 'نظرسنجی غیرفعال شد',
                    'success'
                );
                await this.loadPolls();
                await this.loadDashboardStats();
            } else {
                this.showNotification(data.message || 'خطا در تغییر وضعیت', 'error');
            }
        } catch (error) {
            console.error('Error toggling poll status:', error);
            this.showNotification('خطا در ارتباط با سرور', 'error');
        }
    }

    // Confirm delete poll
    confirmDeletePoll(pollId) {
        const poll = this.polls.find(p => p.id === pollId);
        if (!poll) return;

        const modal = document.getElementById('delete-confirm-modal');
        const pollTitleElement = document.getElementById('delete-poll-title');
        const confirmBtn = document.getElementById('confirm-delete-btn');
        const cancelBtn = document.getElementById('cancel-delete-btn');

        if (!modal) {
            if (confirm(`آیا از حذف نظرسنجی "${poll.title}" اطمینان دارید؟`)) {
                this.deletePoll(pollId);
            }
            return;
        }

        // Set poll title
        if (pollTitleElement) {
            pollTitleElement.textContent = poll.title;
        }

        // Show modal
        modal.style.display = 'flex';

        // Confirm button
        const handleConfirm = () => {
            this.deletePoll(pollId);
            modal.style.display = 'none';
            cleanup();
        };

        // Cancel button
        const handleCancel = () => {
            modal.style.display = 'none';
            cleanup();
        };

        // Cleanup listeners
        const cleanup = () => {
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
        };

        confirmBtn.addEventListener('click', handleConfirm);
        cancelBtn.addEventListener('click', handleCancel);
    }

    // Delete poll
    async deletePoll(pollId) {
        this.showLoading(true);

        try {
            const response = await fetch(`/api/admin/delete-poll/${pollId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('نظرسنجی با موفقیت حذف شد', 'success');
                // Since the page is partially server-rendered, reload might be needed 
                // if we are not using the loadPolls() logic to re-render the table
                setTimeout(() => window.location.reload(), 1000);
            } else {
                this.showNotification(data.message || 'خطا در حذف نظرسنجی', 'error');
            }
        } catch (error) {
            console.error('Error deleting poll:', error);
            this.showNotification('خطا در ارتباط با سرور', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // Logout
    async logout() {
        try {
            const response = await fetch('/admin/logout');
            if (response.ok) {
                window.location.href = '/admin';
            }
        } catch (error) {
            console.error('Error logging out:', error);
            window.location.href = '/admin';
        }
    }

    // Animate stat cards
    animateStatCards() {
        const statCards = document.querySelectorAll('.stat-card');

        statCards.forEach((card, index) => {
            setTimeout(() => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';

                setTimeout(() => {
                    card.style.transition = 'all 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, 50);
            }, index * 100);
        });
    }

    // Show/hide loading overlay
    showLoading(show) {
        const loadingOverlay = document.getElementById('loading-overlay');

        if (loadingOverlay) {
            loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }

    // Show notification
    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');

        if (!notification) {
            alert(message);
            return;
        }

        notification.textContent = message;
        notification.className = `notification notification-${type} show`;

        setTimeout(() => {
            notification.classList.remove('show');
        }, 4000);
    }

    // Format date
    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return new Intl.DateTimeFormat('fa-IR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                calendar: 'persian'
            }).format(date);
        } catch (error) {
            return dateString;
        }
    }

    // Escape HTML
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global instance
let adminDashboard;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    adminDashboard = new AdminDashboard();
    adminDashboard.init();
});
