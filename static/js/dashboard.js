// Dashboard - Load user data and animations
class VoterDashboard {
    constructor() {
        this.authenticated = false;
    }

    async init() {
        console.log("[Dashboard] Initializing...");
        this.setupAnimations();
    }

    setupAnimations() {
        const cards = document.querySelectorAll('.poll-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            setTimeout(() => {
                card.style.transition = 'all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100 + 300);
        });
    }

    showNotification(msg, type = 'error') {
        const container = document.getElementById('notifications');
        if (!container) {
            alert(msg);
            return;
        }
        const alert = document.createElement('div');
        alert.className = `notification ${type}`;
        alert.textContent = msg;
        container.appendChild(alert);
        setTimeout(() => alert.remove(), 5000);
    }
}

let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new VoterDashboard();
    dashboard.init();
});
