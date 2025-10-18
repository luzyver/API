let apisData = [];

// Load APIs from JSON file
async function loadAPIs() {
    try {
        const response = await fetch('apis.json');
        apisData = await response.json();
        renderAPIs();
        checkAllAPIsHealth();
    } catch (error) {
        console.error('Failed to load APIs:', error);
    }
}

// Render API cards dynamically
function renderAPIs() {
    const grid = document.getElementById('apis-grid');
    grid.innerHTML = '';

    apisData.forEach(api => {
        const card = createAPICard(api);
        grid.appendChild(card);
    });
}

// Create API card element
function createAPICard(api) {
    const card = document.createElement('div');
    card.className = 'api-card';
    card.innerHTML = `
        <div class="api-header">
            <h3>${api.name}</h3>
            <div class="status-badge" id="${api.id}-status">
                <div class="status-dot"></div>
                <span>Checking...</span>
            </div>
        </div>

        <p class="api-description">${api.description}</p>

        <div class="url-section">
            <div class="url-label">Base URL</div>
            <div class="url-container">
                <code id="${api.id}-url">${api.baseUrl}</code>
                <button class="copy-btn" onclick="copyToClipboard('${api.id}-url')">Copy</button>
            </div>
        </div>

        <a href="${api.docsUrl}" class="doc-link">
            <span>→</span>
            <span>Documentation</span>
        </a>
    `;
    return card;
}

// Copy to clipboard function
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent;

    navigator.clipboard.writeText(text).then(() => {
        showToast();
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Show toast notification
function showToast() {
    const toast = document.getElementById('toast');
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 2000);
}

// Check single API health
async function checkAPIHealth(api) {
    const badge = document.getElementById(`${api.id}-status`);
    const dot = badge.querySelector('.status-dot');
    const text = badge.querySelector('span');

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(api.healthEndpoint, {
            method: 'GET',
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (response.ok) {
            badge.style.background = 'rgba(34, 197, 94, 0.1)';
            badge.style.color = '#4ade80';
            badge.style.borderColor = 'rgba(34, 197, 94, 0.2)';
            dot.style.background = '#4ade80';
            text.textContent = 'Active';
        } else {
            throw new Error('API not healthy');
        }
    } catch (error) {
        badge.style.background = 'rgba(239, 68, 68, 0.1)';
        badge.style.color = '#f87171';
        badge.style.borderColor = 'rgba(239, 68, 68, 0.2)';
        dot.style.background = '#f87171';
        text.textContent = 'Offline';
    }
}

// Check all APIs health
function checkAllAPIsHealth() {
    apisData.forEach(api => {
        checkAPIHealth(api);
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadAPIs();
});

// Recheck all APIs every 30 seconds
setInterval(() => {
    checkAllAPIsHealth();
}, 30000);
