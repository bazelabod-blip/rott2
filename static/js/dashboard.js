// Dashboard JavaScript - Dark Mode & Interactions

document.addEventListener('DOMContentLoaded', function () {

    // ===============================
    // Dark Mode Toggle
    // ===============================

    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;

    // Load saved theme
    const savedTheme = localStorage.getItem('dashboard-theme') || 'light';
    html.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';

            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('dashboard-theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }

    function updateThemeIcon(theme) {
        const icon = themeToggle?.querySelector('i');
        if (icon) {
            icon.className = theme === 'light' ? 'bi bi-moon-fill' : 'bi bi-sun-fill';
        }
    }

    // ===============================
    // Sidebar Toggle (Mobile)
    // ===============================

    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.dashboard-sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('active');
        });
    }

    // ===============================
    // Animate Cards on Scroll
    // ===============================

    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe all stat cards and chart cards
    document.querySelectorAll('.stat-card, .chart-card, .table-card').forEach(card => {
        observer.observe(card);
    });

    // ===============================
    // Chart.js Animations
    // ===============================

    if (typeof Chart !== 'undefined') {
        Chart.defaults.animation = {
            duration: 1500,
            easing: 'easeInOutQuart'
        };

        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.padding = 15;
    }

    // ===============================
    // Number Counter Animation
    // ===============================

    function animateValue(element, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = Math.floor(progress * (end - start) + start);
            element.textContent = value.toLocaleString('ar-EG');
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // Animate stat values on page load
    document.querySelectorAll('.stat-value').forEach(element => {
        const finalValue = parseInt(element.textContent.replace(/,/g, ''));
        if (!isNaN(finalValue)) {
            element.textContent = '0';
            setTimeout(() => {
                animateValue(element, 0, finalValue, 1000);
            }, 200);
        }
    });

    // ===============================
    // Smooth Scrolling
    // ===============================

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});
