// MindTrace — Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // ── Auto-dismiss alerts after 5s ────────────────────────
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // ── Staggered card animations ────────────────────────────
    // Use IntersectionObserver for cards below the fold
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08 });

        document.querySelectorAll('.card, .entry-card, .stat-card').forEach(el => {
            // Only observe elements that are well below the viewport
            const rect = el.getBoundingClientRect();
            if (rect.top > window.innerHeight * 1.1) {
                el.style.opacity = '0';
                el.style.transform = 'translateY(14px)';
                el.style.transition = 'opacity 0.45s ease, transform 0.45s ease';
                observer.observe(el);
            }
        });
    }

    // ── Active nav link highlight ─────────────────────────────
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href && href !== '/' && currentPath.startsWith(href)) {
            link.style.color = 'var(--text-primary)';
            link.style.background = 'var(--bg-glass-hover)';
        }
    });
});
