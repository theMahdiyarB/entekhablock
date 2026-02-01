// متغیرهای سراسری
let optionCounter = 2;
const MAX_OPTIONS = 10;
const MIN_OPTIONS = 2;

// اعداد فارسی برای نمایش
const persianNumbers = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹', '۱۰'];

// تبدیل عدد به فارسی
function toPersianNumber(num) {
    return num.toString().split('').map(digit => persianNumbers[parseInt(digit)] || digit).join('');
}

// بارگذاری اولیه صفحه
document.addEventListener('DOMContentLoaded', function() {
    initializeDateFields();
    setupFormValidation();
    calculatePollDuration();
});

// مقداردهی اولیه فیلدهای تاریخ
function initializeDateFields() {
    const now = new Date();
    const today = now.toISOString().split('T')[0];
    const currentTime = now.toTimeString().slice(0, 5);
    
    document.getElementById('startDate').min = today;
    document.getElementById('endDate').min = today;
    
    // پیشنهاد: شروع از فردا ساعت ۸ صبح
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById('startDate').value = tomorrow.toISOString().split('T')[0];
    document.getElementById('startTime').value = '08:00';
    
    // پیشنهاد: پایان ۷ روز بعد ساعت ۲۰
    const weekLater = new Date(tomorrow);
    weekLater.setDate(weekLater.getDate() + 7);
    document.getElementById('endDate').value = weekLater.toISOString().split('T')[0];
    document.getElementById('endTime').value = '20:00';
    
    calculatePollDuration();
}

// محاسبه و نمایش مدت زمان نظرسنجی
function calculatePollDuration() {
    const startDate = document.getElementById('startDate').value;
    const startTime = document.getElementById('startTime').value;
    const endDate = document.getElementById('endDate').value;
    const endTime = document.getElementById('endTime').value;
    
    if (!startDate || !startTime || !endDate || !endTime) {
        document.getElementById('pollDuration').textContent = '-';
        return;
    }
    
    const start = new Date(`${startDate}T${startTime}`);
    const end = new Date(`${endDate}T${endTime}`);
    
    if (end <= start) {
        document.getElementById('pollDuration').innerHTML = 
            '<span style="color: var(--error)">❌ زمان پایان باید بعد از زمان شروع باشد</span>';
        return;
    }
    
    const diffMs = end - start;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    let durationText = '';
    if (diffDays > 0) durationText += `${toPersianNumber(diffDays)} روز `;
    if (diffHours > 0) durationText += `${toPersianNumber(diffHours)} ساعت `;
    if (diffMinutes > 0) durationText += `${toPersianNumber(diffMinutes)} دقیقه`;
    
    document.getElementById('pollDuration').innerHTML = 
        `<span style="color: var(--success)">✓ ${durationText.trim()}</span>`;
}

// افزودن event listener برای تغییرات زمان
['startDate', 'startTime', 'endDate', 'endTime'].forEach(id => {
    document.getElementById(id).addEventListener('change', calculatePollDuration);
});

// افزودن گزینه جدید
function addOption() {
    const container = document.getElementById('optionsContainer');
    const currentOptions = container.querySelectorAll('.option-item').length;
    
    if (currentOptions >= MAX_OPTIONS) {
        showNotification(`حداکثر ${toPersianNumber(MAX_OPTIONS)} گزینه مجاز است`, 'warning');
        return;
    }
    
    const optionItem = document.createElement('div');
    optionItem.className = 'option-item';
    optionItem.setAttribute('data-index', optionCounter);
    optionItem.innerHTML = `
        <div class="option-number">${persianNumbers[currentOptions + 1]}</div>
        <input 
            type="text" 
            name="options[]" 
            class="form-input option-input" 
            placeholder="گزینه ${persianNumbers[currentOptions + 1]}"
            required
            maxlength="100"
        >
        <button type="button" class="btn-remove-option" onclick="removeOption(${optionCounter})">
            🗑️
        </button>
    `;
    
    container.appendChild(optionItem);
    optionCounter++;
    
    updateRemoveButtons();
}

// حذف گزینه
function removeOption(index) {
    const container = document.getElementById('optionsContainer');
    const currentOptions = container.querySelectorAll('.option-item').length;
    
    if (currentOptions <= MIN_OPTIONS) {
        showNotification(`حداقل ${toPersianNumber(MIN_OPTIONS)} گزینه الزامی است`, 'warning');
        return;
    }
    
    const optionItem = container.querySelector(`[data-index="${index}"]`);
    if (optionItem) {
        optionItem.remove();
        updateOptionNumbers();
        updateRemoveButtons();
    }
}

// به‌روزرسانی شماره‌گذاری گزینه‌ها
function updateOptionNumbers() {
    const options = document.querySelectorAll('.option-item');
    options.forEach((option, index) => {
        const numberDiv = option.querySelector('.option-number');
        const input = option.querySelector('.option-input');
        numberDiv.textContent = persianNumbers[index + 1];
        input.placeholder = `گزینه ${persianNumbers[index + 1]}`;
    });
}

// به‌روزرسانی وضعیت دکمه‌های حذف
function updateRemoveButtons() {
    const container = document.getElementById('optionsContainer');
    const currentOptions = container.querySelectorAll('.option-item').length;
    const removeButtons = container.querySelectorAll('.btn-remove-option');
    
    removeButtons.forEach(btn => {
        if (currentOptions <= MIN_OPTIONS) {
            btn.disabled = true;
            btn.title = `حداقل ${toPersianNumber(MIN_OPTIONS)} گزینه الزامی است`;
        } else {
            btn.disabled = false;
            btn.title = 'حذف گزینه';
        }
    });
}

// مدیریت آپلود فایل
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // بررسی نوع فایل
    if (!file.name.endsWith('.csv')) {
        showNotification('فقط فایل‌های CSV مجاز هستند', 'error');
        event.target.value = '';
        return;
    }
    
    // بررسی حجم فایل (حداکثر 5MB)
    if (file.size > 5 * 1024 * 1024) {
        showNotification('حجم فایل نباید بیشتر از ۵ مگابایت باشد', 'error');
        event.target.value = '';
        return;
    }
    
    // نمایش اطلاعات فایل
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileStats').textContent = 
        `حجم: ${(file.size / 1024).toFixed(2)} کیلوبایت`;
    
    // پردازش فایل برای شمارش رأی‌دهندگان
    const reader = new FileReader();
    reader.onload = function(e) {
        const text = e.target.result;
        const lines = text.trim().split('\n');
        const votersCount = lines.length - 1; // منهای سطر header
        
        document.getElementById('fileStats').textContent += 
            ` | تعداد رأی‌دهندگان: ${toPersianNumber(votersCount)}`;
    };
    reader.readAsText(file);
    
    // نمایش پیش‌نمایش
    document.getElementById('filePreview').style.display = 'block';
    document.querySelector('.upload-label').style.display = 'none';
}

// حذف فایل آپلود شده
function removeFile() {
    document.getElementById('votersFile').value = '';
    document.getElementById('filePreview').style.display = 'none';
    document.querySelector('.upload-label').style.display = 'flex';
}

// تغییر وضعیت استفاده از لیست موررسی نوع فایل
    if (!file.name.endsWith('.csv')) {
        showNotification('فقط فایل‌های CSV مجاز هستند', 'error');
        event.target.value = '';
        return;
    }
    
    // بررسی حجم فایل (حداکثر 5MB)
    if (file.size > 5 * 1024 * 1024) {
        showNotification('حجم فایل نباید بیشتر از ۵ مگابایت باشد', 'error');
        event.target.value = '';
        return;
    }
    
    // نمایش اطلاعات فایل
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileStats').textContent = 
        `حجم: ${(file.size / 1024).toFixed(2)} کیلوبایت`;
    
    // پردازش فایل برای شمارش رأی‌دهندگان
    const reader = new FileReader();
    reader.onload = function(e) {
        const text = e.target.result;
        const lines = text.trim().split('\n');
        const votersCount = lines.length - 1; // منهای سطر header
        
        document.getElementById('fileStats').textContent += 
            ` | تعداد رأی‌دهندگان: ${toPersianNumber(votersCount)}`;
    };
    reader.readAsText(file);
    
    // نمایش پیش‌نمایش
    document.getElementById('filePreview').style.display = 'block';
    document.querySelector('.upload-label').style.display = 'none';
}

// حذف فایل آپلود شده
function removeFile() {
    document.getElementById('votersFile').value = '';
    document.getElementById('filePreview').style.display = 'none';
    document.querySelector('.upload-label').style.display = 'flex';
}

// تغییر وضعیت استفاده از لیست موجود
function toggleVotersFile() {
    const useExisting = document.getElementById('useExistingVoters').checked;
    const fileInput = document.getElementById('votersFile');
    const uploadArea = document.getElementById('uploadArea');
    
    if (useExisting) {
        fileInput.required = false;
        uploadArea.style.opacity = '0.5';
        uploadArea.style.pointerEvents = 'none';
    } else {
        fileInput.required = true;
        uploadArea.style.opacity = '1';
        uploadArea.style.pointerEvents = 'auto';
    }
}

// اعتبارسنجی فرم
function setupFormValidation() {
    const form = document.getElementById('createPollForm');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // بررسی تاریخ‌ها
        const startDate = document.getElementById('startDate').value;
        const startTime = document.getElementById('startTime').value;
        const endDate = document.getElementById('endDate').value;
        const endTime = document.getElementById('endTime').value;
        
        const start = new Date(`${startDate}T${startTime}`);
        const end = new Date(`${endDate}T${endTime}`);
        
        if (end <= start) {
            showNotification('زمان پایان باید بعد از زمان شروع باشد', 'error');
            return;
        }
        
        // بررسی گزینه‌ها
        const options = Array.from(document.querySelectorAll('.option-input'))
            .map(input => input.value.trim())
            .filter(val => val !== '');
        
        if (options.length < MIN_OPTIONS) {
            showNotification(`حداقل ${toPersianNumber(MIN_OPTIONS)} گزینه الزامی است`, 'error');
            return;
        }
        
        // بررسی تکراری نبودن گزینه‌ها
        const uniqueOptions = new Set(options);
        if (uniqueOptions.size !== options.length) {
            showNotification('گزینه‌ها نباید تکراری باشند', 'error');
            return;
        }
        
        // بررسی فایل رأی‌دهندگان
        const useExisting = document.getElementById('useExistingVoters').checked;
        const fileInput = document.getElementById('votersFile');
        
        if (!useExisting && !fileInput.files.length) {
            showNotification('لطفاً فایل رأی‌دهندگان را آپلود کنید', 'error');
            return;
        }
        
        // ارسال فرم
        showNotification('در حال ایجاد نظرسنجی...', 'info');
        this.submit}`);
        const end = new Date(`${endDate}T${endTime}`);
        
        if (end <= start) {
            showNotification('زمان پایان باید بعد از زمان شروع باشد', 'error');
            return;
        }
        
        // بررسی گزینه‌ها
        const options = Array.from(document.querySelectorAll('.option-input'))
            .map(input => input.value.trim())
            .filter(val => val !== '');
        
        if (options.length < MIN_OPTIONS) {
            showNotification(`حداقل ${toPersianNumber(MIN_OPTIONS)} گزینه الزامی است`, 'error');
            return;
        }
        
        // بررسی تکراری نبودن گزینه‌ها
        const uniqueOptions = new Set(options);
        if (uniqueOptions.size !== options.length) {
            showNotification('گزینه‌ها نباید تکراری باشند', 'error');
            return;
        }
        
        // بررسی فایل رأی‌دهندگان
        const useExisting = document.getElementById('useExistingVoters').checked;
        const fileInput = document.getElementById('votersFile');
        
        if (!useExisting && !fileInput.files.length) {
            showNotification('لطفاً فایل رأی‌دهندگان را آپلود کنید', 'error');
            return;
        }
        
        // ارسال فرم
        showNotification('در حال ایجاد نظرسنجی...', 'info');
        this.submit();
    });
}

// پیش‌نمایش نظرسنجی
function previewPoll() {
    const title = document.getElementById('pollTitle').value;
    const description = document.getElementById('pollDescription').value;
    const startDate = document.getElementById('startDate').value;
    const startTime = document.getElementById('startTime').value;
    const endDate = document.getElementById('endDate').value;
    const endTime = document.getElementById('endTime').value;
    
    const options = Array.from(document.querySelectorAll('.option-input'))
        .map(input => input.value.trim())
        .filter(val => val !== '');
    
    if (!title || options.length < MIN_OPTIONS) {
        showNotification('لطفاً عنوان و حداقل دو گزینه را وارد کنید', 'warning');
        return;
    }
    
    const start = new Date(`${startDate}T${startTime}`);
    const end = new Date(`${endDate}T${endTime}`);
    
    const optionsHTML = options.map((opt, index) => `
        <div class="preview-option">
            <span class="preview-option-number">${persianNumbers[index + 1]}</span>
            <span class="preview-option-text">${opt}</span>
        </div>
    `).join('');
    
    const previewContent = `
        <div class="preview-container">
            <div class="preview-header">
                <h2>${title}</h2>
                ${description ? `<p class="preview-description">${description}</p>` : ''}
            </div>
            
            <div class="preview-info">
                <div class="preview-info-item">
                    <span class="preview-label">⏰ زمان شروع:</span>
                    <span class="preview-value">${new Date(start).toLocaleString('fa-IR')}</span>
                </div>
                <div class="preview-info-item">
                    <span class="preview-label">⏰ زمان پایان:</span>
                    <span class="preview-value">${new Date(end).toLocaleString('fa-IR')}</span>
                </div>
            </div>
            
            <div class="preview-options">
                <h4>گزینه‌های رأی‌گیری:</h4>
                ${optionsHTML}
            </div>
            
            <div class="preview-settings">
                <h4>تنظیمات:</h4>
                <ul>
                    <li>امکان تغییر رأی: ${document.getElementById('allowVoteChange').checked ? '✓ فعال' : '✗ غیرفعال'}</li>
                    <li>نمایش نتایج لحظه‌ای: ${document.getElementById('showLiveResults').checked ? '✓ فعال' : '✗ غیرفعال'}</li>
                    <li>رأی‌گیری ناشناس: ✓ فعال (پیش‌فرض)</li>
                </ul>
            </div>
        </div>
    `;
    
    document.getElementById('previewContent').innerHTML = previewContent;
    document.getElementById('previewModal').style.display = 'flex';
}

// بستن مودال پیش‌نمایش
function closePreviewModal() {
    document.getElementById('previewModal').style.display = 'none';
}

// ارسال از پیش‌نمایش
function submitFromPreview() {
    closePreviewModal();
    document.getElementById('createPollForm').requestSubmit();
}

// ذخیره پیش‌نویس
function saveDraft() {
    const formData = {
        title: document.getElementById('pollTitle').value,
        description: document.getElementById('pollDescription').value,
        startDate: document.getElementById('startDate').value,
        startTime: document.getElementById('startTime').value,
        endDate: document.getElementById('endDate').value,
        endTime: document.getElementById('endTime').value,
        options: Array.from(document.querySelectorAll('.option- class="preview-option-text">${opt}</span>
        </div>
    `).join('');
    
    const previewContent = `
        <div class="preview-container">
            <div class="preview-header">
                <h2>${title}</h2>
                ${description ? `<p class="preview-description">${description}</p>` : ''}
            </div>
            
            <div class="preview-info">
                <div class="preview-info-item">
                    <span class="preview-label">⏰ زمان شروع:</span>
                    <span class="preview-value">${new Date(start).toLocaleString('fa-IR')}</span>
                </div>
                <div class="preview-info-item">
                    <span class="preview-label">⏰ زمان پایان:</span>
                    <span class="preview-value">${new Date(end).toLocaleString('fa-IR')}</span>
                </div>
            </div>
            
            <div class="preview-options">
                <h4>گزینه‌های رأی‌گیری:</h4>
                ${optionsHTML}
            </div>
            
            <div class="preview-settings">
                <h4>تنظیمات:</h4>
                <ul>
                    <li>امکان تغییر رأی: ${document.getElementById('allowVoteChange').checked ? '✓ فعال' : '✗ غیرفعال'}</li>
                    <li>نمایش نتایج لحظه‌ای: ${document.getElementById('showLiveResults').checked ? '✓ فعال' : '✗ غیرفعال'}</li>
                    <li>رأی‌گیری ناشناس: ✓ فعال (پیش‌فرض)</li>
                </ul>
            </div>
        </div>
    `;
    
    document.getElementById('previewContent').innerHTML = previewContent;
    document.getElementById('previewModal').style.display = 'flex';
}

// بستن مودال پیش‌نمایش
function closePreviewModal() {
    document.getElementById('previewModal').style.display = 'none';
}

// ارسال از پیش‌نمایش
function submitFromPreview() {
    closePreviewModal();
    document.getElementById('createPollForm').requestSubmit();
}

// ذخیره پیش‌نویس
function saveDraft() {
    const formData = {
        title: document.getElementById('pollTitle').value,
        description: document.getElementById('pollDescription').value,
        startDate: document.getElementById('startDate').value,
        startTime: document.getElementById('startTime').value,
        endDate: document.getElementById('endDate').value,
        endTime: document.getElementById('endTime').value,
        options: Array.from(document.querySelectorAll('.option-input')).map(input => input.value),
        settings: {
            allowVoteChange: document.getElementById('allowVoteChange').checked,
            showLiveResults: document.getElementById('showLiveResults').checked,
            useExistingVoters: document.getElementById('useExistingVoters').checked
        }
    };
    
    localStorage.setItem('pollDraft', JSON.stringify(formData));
    showNotification('پیش‌نویس با موفقیت ذخیره شد', 'success');
}

// بارگذاری پیش‌نویس (در صورت وجود)
window.addEventListener('load', function() {
    const draft = localStorage.getItem('pollDraft');
    if (draft) {
        const showDraft = confirm('یک پیش‌نویس ذخیره شده وجود دارد. آیا می‌خواهید آن را بارگذاری کنید؟');
        if (showDraft) {
            const data = JSON.parse(draft);
            document.getElementById('pollTitle').value = data.title || '';
            document.getElementById('pollDescription').value = data.description || '';
            document.getElementById('startDate').value = data.startDate || '';
            document.getElementById('startTime').value = data.startTime || '';
            document.getElementById('endDate').value = data.endDate || '';
            document.getElementById('endTime').value = data.endTime || '';
            
            if (data.options && data.options.length > 0) {
                const inputs = document.querySelectorAll('.option-input');
                data.options.forEach((opt, index) => {
                    if (inputs[index]) {
                        inputs[index].value = opt;
                    } else if (opt) {
                        addOption();
                        const newInputs = document.querySelectorAll('.option-input');
                        newInputs[newInputs.length - 1].value = opt;
                    }
                });
            }
            
            if (data.settings) {
                document.getElementById('allowVoteChange').checked = data.settings.allowVoteChange || false;
                document.getElementById('showLiveResults').checked = data.settings.showLiveResults || false;
                document.getElementById('useExistingVoters').checked = data.settings.useExistingVoters || false;
            }
            
            calculatePollDuration();
        }
    }
});

// نمایش نوتیفیکیشن
function showNotification(message, type = 'info') {
    // ایجاد المان نوتیفیکیشن
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${getNotificationIcon(type)}</span>
        <span class="notification-message">${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // نمایش با انیمیشن
    setTimeout(() => notification.classList.add('show'), 10);
    
    // حذف بعد از 3 ثانیه
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// آیکون نوتیفیکیشن
function getNotificationIcon(type) {
    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };
    return icons[type] || icons.info;
}
