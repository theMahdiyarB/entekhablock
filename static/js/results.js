// static/js/results.js
// Results Visualization for Entekhablock - Debug Enhanced

class ResultsManager {
    constructor() {
        this.barChart = null;
        this.pieChart = null;
    }

    init() {
        console.log("[Results] Initializing ResultsManager...");

        // 1. Library Check
        if (typeof Chart === 'undefined') {
            console.error("[Results] Chart.js is NOT LOADED. Check network or CDN link.");
            this.showErrorMessage("خطا: کتابخانه نمودار بارگذاری نشد.");
            return;
        }

        // 2. Data Check
        if (typeof chartData === 'undefined') {
            console.error("[Results] chartData global object is MISSING.");
            return;
        }

        console.log("[Results] Received Data:", chartData);

        if (!chartData.labels || !chartData.values || chartData.labels.length === 0) {
            console.warn("[Results] chartData is empty or invalid.");
            this.showErrorMessage("هنوز برای این نظرسنجی رأی ثبت نشده است.");
            return;
        }

        // 3. Render
        try {
            this.renderCharts();
            this.bindToggles();
            console.log("[Results] Charts initialized successfully.");
        } catch (err) {
            console.error("[Results] Initialization error:", err);
            this.showErrorMessage("خطا در ترسیم نمودارها.");
        }
    }

    renderCharts() {
        // Material 3 Expressive Palette
        const colors = [
            'rgba(103, 80, 164, 1.0)', // Primary
            'rgba(0, 106, 106, 1.0)',   // Teal
            'rgba(125, 82, 96, 1.0)',   // Tertiary
            'rgba(186, 26, 26, 1.0)',   // Error
            'rgba(103, 80, 164, 0.7)',
            'rgba(0, 106, 106, 0.7)',
            'rgba(125, 82, 96, 0.7)'
        ];

        const ctxBar = document.getElementById('barChart');
        const ctxPie = document.getElementById('pieChart');

        if (ctxBar) {
            if (this.barChart) this.barChart.destroy();
            this.barChart = new Chart(ctxBar, {
                type: 'bar',
                data: {
                    labels: chartData.labels,
                    datasets: [{
                        label: 'تعداد آرا',
                        data: chartData.values,
                        backgroundColor: colors,
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            rtl: true,
                            titleFont: { family: 'Vazirmatn' },
                            bodyFont: { family: 'Vazirmatn' }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(0,0,0,0.05)' },
                            ticks: { font: { family: 'Vazirmatn' } }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { font: { family: 'Vazirmatn' } }
                        }
                    }
                }
            });
        }

        if (ctxPie) {
            if (this.pieChart) this.pieChart.destroy();
            this.pieChart = new Chart(ctxPie, {
                type: 'doughnut',
                data: {
                    labels: chartData.labels,
                    datasets: [{
                        data: chartData.values,
                        backgroundColor: colors,
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            rtl: true,
                            labels: {
                                padding: 20,
                                usePointStyle: true,
                                font: { family: 'Vazirmatn' }
                            }
                        },
                        tooltip: {
                            rtl: true,
                            titleFont: { family: 'Vazirmatn' },
                            bodyFont: { family: 'Vazirmatn' }
                        }
                    },
                    cutout: '65%'
                }
            });
        }
    }

    bindToggles() {
        const btns = document.querySelectorAll('.chart-btn');
        btns.forEach(btn => {
            btn.addEventListener('click', () => {
                const type = btn.dataset.chart;
                console.log(`[Results] Switching to ${type} chart`);

                btns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                document.querySelectorAll('.chart-canvas').forEach(c => c.classList.remove('active'));
                const target = document.getElementById(`${type}Chart`);
                if (target) {
                    target.classList.add('active');
                    // Force a resize check in case it was hidden
                    if (type === 'bar' && this.barChart) this.barChart.resize();
                    if (type === 'pie' && this.pieChart) this.pieChart.resize();
                }
            });
        });
    }

    showErrorMessage(msg) {
        const wrapper = document.querySelector('.chart-wrapper');
        if (wrapper) {
            wrapper.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--m3-on-surface-variant);font-size:16px;text-align:center;padding:20px;">${msg}</div>`;
        }
    }
}

// Ensure initialization happens
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.resultsManager = new ResultsManager();
        window.resultsManager.init();
    });
} else {
    window.resultsManager = new ResultsManager();
    window.resultsManager.init();
}
