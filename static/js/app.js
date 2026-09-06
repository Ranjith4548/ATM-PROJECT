document.addEventListener('DOMContentLoaded', () => {
    document.body.classList.add('is-ready');
    if (window.lucide) {
        window.lucide.createIcons();
    }

    const dateElement = document.querySelector('[data-current-date]');
    const timeElement = document.querySelector('[data-current-time]');
    const updateClock = () => {
        const now = new Date();
        if (dateElement) dateElement.textContent = now.toLocaleDateString(undefined, { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' });
        if (timeElement) timeElement.textContent = now.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
    };
    updateClock();
    window.setInterval(updateClock, 30000);

    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-links a').forEach((link) => {
        if (link.getAttribute('href') === currentPath) {
            link.setAttribute('aria-current', 'page');
        }
    });

    const dashboardPaths = ['/checkBalance', '/deposit', '/withdraw', '/viewtransactions'];
    if (dashboardPaths.includes(currentPath)) {
        const dashboardLink = document.querySelector('.nav-links a[href^="/dashboard/"]');
        dashboardLink?.setAttribute('aria-current', 'page');
    }

    document.querySelectorAll('form').forEach((form) => {
        form.addEventListener('submit', () => {
            const submitButton = form.querySelector('input[type="submit"]');
            if (!submitButton || !form.checkValidity()) {
                return;
            }

            submitButton.disabled = true;
            submitButton.value = 'Processing...';
            form.classList.add('is-processing');
        });
    });

    document.querySelectorAll('[data-amount]').forEach((button) => {
        button.addEventListener('click', () => {
            const amount = document.querySelector('input[name="amount"]');
            if (!amount) return;
            amount.value = button.dataset.amount;
            document.querySelectorAll('[data-amount]').forEach((item) => item.classList.remove('is-selected'));
            button.classList.add('is-selected');
        });
    });

    document.querySelectorAll('[data-toggle-password]').forEach((button) => {
        button.addEventListener('click', () => {
            const input = document.getElementById(button.dataset.togglePassword);
            if (!input) return;
            const visible = input.type === 'text';
            input.type = visible ? 'password' : 'text';
            button.setAttribute('aria-label', visible ? 'Show PIN' : 'Hide PIN');
            button.innerHTML = `<i data-lucide="${visible ? 'eye' : 'eye-off'}"></i>`;
            window.lucide?.createIcons();
        });
    });

    document.querySelectorAll('[data-export-pdf]').forEach((button) => {
        button.addEventListener('click', () => {
            window.print();
        });
    });
});
