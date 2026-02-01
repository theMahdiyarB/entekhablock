/**
 * auth.js
 * Authentication Management for Entekhablock
 */

class AuthManager {
    constructor() {
        this.otpTimer = null;
        this.remainingTime = 0;
        console.log("[AuthManager] Instance created");
    }

    init() {
        const path = window.location.pathname;
        console.log("[AuthManager] Initializing for path:", path);

        this.setupCommonUI();

        // Find timer element - many pages use it
        const timerElement = document.getElementById('timer');
        if (timerElement) {
            console.log("[AuthManager] Timer element found, initiating countdown");
            this.setupOTPForm();

            // Determine duration based on context
            let duration = 60; // Default 1 minute
            if (path.includes('/admin')) {
                duration = 120; // 2 minutes for admin
            }

            this.startOTPTimer(duration);
        }

        // Logic for biometric page
        if (path.includes('/biometric')) {
            this.setupBiometricAuth();
        }
    }

    setupCommonUI() {
        // Auto-focus next input for OTP digit fields
        const otpInputs = document.querySelectorAll('.otp-input, .otp-inputs input');
        if (otpInputs.length > 0) {
            otpInputs.forEach((input, index) => {
                input.addEventListener('input', (e) => {
                    if (e.target.value.length === 1 && index < otpInputs.length - 1) {
                        otpInputs[index + 1].focus();
                    }
                    this.updateOTPValue(); // Keep the hidden field in sync
                });

                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Backspace' && !e.target.value && index > 0) {
                        otpInputs[index - 1].focus();
                        this.updateOTPValue();
                    }
                });
            });
        }
    }

    /**
     * Concatenates individual digit inputs into a single hidden field
     */
    updateOTPValue() {
        const otpInputs = document.querySelectorAll('.otp-input, .otp-inputs input');
        const hiddenInput = document.getElementById('otpCode') || document.getElementById('otp_code') || document.getElementById('otp');

        // Special case: if there's only one 'otp' field (normal voter flow), we don't need this
        if (otpInputs.length > 1 && hiddenInput) {
            const code = Array.from(otpInputs).map(i => i.value).join('');
            hiddenInput.value = code;
        }
    }

    setupOTPForm() {
        const resendBtn = document.getElementById('resend-otp-btn') || document.getElementById('resendBtn');
        if (resendBtn) {
            resendBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log("[AuthManager] Resend requested");
                // Reset timer for demo purposes
                this.startOTPTimer(60);
                alert("کد جدید مجدداً ارسال شد.");
            });
        }
    }

    startOTPTimer(seconds) {
        if (this.otpTimer) {
            clearInterval(this.otpTimer);
        }

        this.remainingTime = seconds;
        const timerElement = document.getElementById('timer');
        const resendBtn = document.getElementById('resend-otp-btn') || document.getElementById('resendBtn');

        if (!timerElement) return;

        if (resendBtn) resendBtn.disabled = true;

        const tick = () => {
            const mins = Math.floor(this.remainingTime / 60);
            const secs = this.remainingTime % 60;
            const timeString = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

            // Just update the text content. 
            timerElement.textContent = timeString;

            if (this.remainingTime <= 0) {
                clearInterval(this.otpTimer);
                timerElement.textContent = "منقضی شده";
                if (resendBtn) resendBtn.disabled = false;
                console.log("[AuthManager] Timer expired");
                return;
            }
            this.remainingTime--;
        };

        tick();
        this.otpTimer = setInterval(tick, 1000);
        console.log(`[AuthManager] Countdown started: ${seconds}s`);
    }

    setupBiometricAuth() {
        console.log("[AuthManager] Biometric setup (placeholder)");
    }
}

// Global initialization
function startAuth() {
    if (!window.authManager) {
        window.authManager = new AuthManager();
        window.authManager.init();
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startAuth);
} else {
    startAuth();
}
