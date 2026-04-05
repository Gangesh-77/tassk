const API_BASE = "http://localhost:8000/api";

// DOM Elements
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const resultsList = document.getElementById('resultsList');
const resultsInfo = document.getElementById('resultsInfo');
const statsContent = document.getElementById('statsContent');
const categoryFilters = document.getElementById('categoryFilters');
const emailModal = document.getElementById('emailModal');
const closeModal = document.getElementById('closeModal');
const modalBody = document.getElementById('modalBody');

// Application State
let currentCategory = null;

// Initial Setup
document.addEventListener('DOMContentLoaded', () => {
    fetchEmails();
    fetchStats();
});

// Event Listeners
searchBtn.addEventListener('click', () => performSearch());
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
});

closeModal.addEventListener('click', () => {
    emailModal.style.display = 'none';
});

// Functions
async function fetchEmails() {
    try {
        const response = await fetch(`${API_BASE}/emails?limit=20`);
        const data = await response.json();
        renderEmails(data, "Your Inbox");
    } catch (err) {
        console.error("Failed to fetch emails:", err);
        resultsList.innerHTML = `<div style="text-align: center; color: #ef4444;">Error: Could not connect to backend. Make sure it's running.</div>`;
    }
}

async function fetchStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();
        
        statsContent.innerHTML = `
            <div style="margin-bottom: 0.5rem;"><strong>Total:</strong> ${data.total}</div>
            <div><strong>Unread:</strong> ${data.unread}</div>
        `;

        renderCategoryFilters(data.categories);
    } catch (err) {
        console.error("Failed to fetch stats:", err);
    }
}

function renderCategoryFilters(categories) {
    categoryFilters.innerHTML = '';
    
    // Add "All" option
    const allDiv = createFilterDiv('All', null);
    categoryFilters.appendChild(allDiv);

    Object.entries(categories).forEach(([name, count]) => {
        const div = createFilterDiv(name, count);
        categoryFilters.appendChild(div);
    });
}

function createFilterDiv(name, count) {
    const div = document.createElement('div');
    div.className = 'filter-item';
    div.innerHTML = `<span>${name}</span> ${count ? `<span style="font-size: 0.8rem; opacity: 0.5;">(${count})</span>` : ''}`;
    div.onclick = () => {
        currentCategory = name === 'All' ? null : name;
        performSearch();
    };
    return div;
}

async function performSearch() {
    const query = searchInput.value.trim();
    
    if (!query && !currentCategory) {
        fetchEmails();
        return;
    }

    resultsList.innerHTML = `<div style="text-align: center; padding: 2rem;">Searching...</div>`;
    
    try {
        const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query || "show all emails",
                category: currentCategory,
                limit: 15
            })
        });
        const data = await response.json();
        renderEmails(data, query ? `Results for "${query}"` : `${currentCategory} Emails`);
    } catch (err) {
        console.error("Search failed:", err);
    }
}

function renderEmails(emails, titleText) {
    resultsInfo.textContent = titleText;
    resultsList.innerHTML = '';

    if (emails.length === 0) {
        resultsList.innerHTML = `<div style="text-align: center; padding: 4rem; color: #94a3b8;">No emails found.</div>`;
        return;
    }

    emails.forEach((email, index) => {
        const card = document.createElement('div');
        card.className = 'email-card';
        card.style.animationDelay = `${index * 0.1}s`;
        
        card.innerHTML = `
            <div class="email-header">
                <span class="sender">${email.sender}</span>
                ${email.relevance_score ? `<span class="relevance">${Math.round(email.relevance_score * 100)}% Match</span>` : ''}
            </div>
            <div class="subject">${email.subject}</div>
            <div class="body-preview">${email.body}</div>
            <div class="footer">
                <span class="tag">${email.category}</span>
                <span style="opacity: 0.4;">|</span>
                <span style="color: #94a3b8;">${new Date(email.date).toLocaleDateString()}</span>
                ${email.has_attachment ? `<span style="opacity: 0.6;">📎</span>` : ''}
                ${!email.is_read ? `<span style="color: #6366f1; font-weight: bold;">●</span>` : ''}
            </div>
        `;

        card.onclick = () => openEmail(email);
        resultsList.appendChild(card);
    });
}

function openEmail(email) {
    modalBody.innerHTML = `
        <div style="margin-bottom: 2rem;">
            <div style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 0.5rem;">From: <strong style="color: #6366f1;">${email.sender}</strong></div>
            <div style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 1.5rem;">Date: ${new Date(email.date).toLocaleString()}</div>
            <h2 style="font-size: 2rem; border-bottom: 1px solid var(--glass-border); padding-bottom: 1rem; margin-bottom: 2rem;">${email.subject}</h2>
        </div>
        <div style="line-height: 1.8; font-size: 1.1rem; color: #cbd5e1; white-space: pre-wrap;">${email.body}</div>
    `;
    emailModal.style.display = 'flex';
}
