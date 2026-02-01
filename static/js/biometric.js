// Biometric Video Authentication
// Captures video and sends to server for VideoLive API verification

class BiometricManager {
    constructor() {
        this.mediaStream = null;
        this.mediaRecorder = null;
        this.recordedChunks = [];
    }

    async init() {
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        const verifyBtn = document.getElementById('verify-btn');
        const biometricForm = document.getElementById('biometric-form');
        const video = document.getElementById('video');

        if (!startBtn || !video) return;

        // Request camera access
        try {
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
                audio: false
            });
            video.srcObject = this.mediaStream;
        } catch (err) {
            console.error('Camera access denied:', err);
            startBtn.textContent = 'دسترسی به دوربین رد شد';
            startBtn.disabled = true;
            return;
        }

        // Start recording button
        startBtn.addEventListener('click', () => {
            this.startRecording(startBtn, stopBtn);
        });

        // Stop recording button
        stopBtn.addEventListener('click', () => {
            this.stopRecording(stopBtn, verifyBtn);
        });

        // Form submission
        if (biometricForm) {
            biometricForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitVideo(biometricForm, verifyBtn);
            });
        }
    }

    startRecording(startBtn, stopBtn) {
        this.recordedChunks = [];
        this.mediaRecorder = new MediaRecorder(this.mediaStream, {
            mimeType: 'video/webm;codecs=vp9'
        });

        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.recordedChunks.push(event.data);
            }
        };

        this.mediaRecorder.onerror = (event) => {
            console.error('Recording error:', event.error);
            alert('خطا در ضبط ویدئو');
        };

        this.mediaRecorder.start();
        startBtn.style.display = 'none';
        stopBtn.style.display = 'block';
        stopBtn.textContent = 'پایان ضبط...';
    }

    stopRecording(stopBtn, verifyBtn) {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
            stopBtn.style.display = 'none';
            verifyBtn.style.display = 'block';
            verifyBtn.disabled = false;
        }
    }

    async submitVideo(form, verifyBtn) {
        if (this.recordedChunks.length === 0) {
            alert('لطفاً ابتدا ویدئو را ضبط کنید');
            return;
        }

        verifyBtn.disabled = true;
        verifyBtn.textContent = 'در حال تأیید...';

        try {
            // Create blob from recorded chunks
            const videoBlob = new Blob(this.recordedChunks, { type: 'video/webm' });
            
            // Convert to base64
            const reader = new FileReader();
            reader.onload = () => {
                const base64Video = reader.result.split(',')[1];
                
                // Set the hidden input with video data
                document.getElementById('video_data').value = base64Video;
                
                // Submit the form
                form.submit();
            };
            reader.readAsDataURL(videoBlob);
        } catch (err) {
            console.error('Error processing video:', err);
            alert('خطا در پردازش ویدئو');
            verifyBtn.disabled = false;
            verifyBtn.textContent = 'تأیید و ورود به سیستم';
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const biometricManager = new BiometricManager();
    biometricManager.init();
});
