// Initialize all functionality
function initializeApp() {
    // Theme persistence logic
    const themeSwitch = document.getElementById('theme-switch');
    if (themeSwitch) {
        // Check for saved theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light') {
            document.body.classList.add('light-theme');
            themeSwitch.checked = true;
        }

        themeSwitch.addEventListener('change', () => {
            if (themeSwitch.checked) {
                document.body.classList.add('light-theme');
                localStorage.setItem('theme', 'light');
            } else {
                document.body.classList.remove('light-theme');
                localStorage.setItem('theme', 'dark');
            }
        });
    }

    // Handle logout link standard behavior
    const logoutLink = document.getElementById('logoutLink');
    if (logoutLink) {
        logoutLink.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = '/logout';
        });
    }

    // Hamburger Menu Toggle
    const hamburgerToggle = document.getElementById('hamburger-toggle');
    const navTabs = document.getElementById('nav-tabs');

    if (hamburgerToggle && navTabs) {
        // Toggle menu on hamburger button click
        hamburgerToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const isOpen = navTabs.classList.contains('mobile-open');
            navTabs.classList.toggle('mobile-open');
        });

        // Close menu when a tab is clicked
        const tabs = navTabs.querySelectorAll('.tab a');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                navTabs.classList.remove('mobile-open');
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navTabs.contains(e.target) && !hamburgerToggle.contains(e.target)) {
                if (navTabs.classList.contains('mobile-open')) {
                    navTabs.classList.remove('mobile-open');
                }
            }
        });
    } else {
        console.error('Hamburger menu elements not found:', {
            hamburgerToggle: !!hamburgerToggle,
            navTabs: !!navTabs
        });
    }

    // Auto-hide notifications
    const alerts = document.querySelectorAll('.flash-messages-container .alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert && alert.parentElement) {
                alert.classList.add('fade-out');
                setTimeout(() => {
                    alert.remove();
                }, 400); // Wait for fade-out animation
            }
        }, 5000); // 5 seconds
    });
}

// Run on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}
