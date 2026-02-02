// OSINT Panel Controller
document.addEventListener('DOMContentLoaded', function() {
    // State
    let currentTab = 'email';
    let searchHistory = {
        total: 0,
        email: 0,
        username: 0,
        photo: 0
    };
    let lastResult = null;

    // DOM Elements
    const tabs = {
        email: document.getElementById('tabEmail'),
        username: document.getElementById('tabUsername'),
        photo: document.getElementById('tabPhoto')
    };

    const panels = {
        email: document.getElementById('panelEmail'),
        username: document.getElementById('panelUsername'),
        photo: document.getElementById('panelPhoto')
    };

    const inputs = {
        email: document.getElementById('emailInput'),
        username: document.getElementById('usernameInput'),
        photo: document.getElementById('photoInput')
    };

    const searchButtons = {
        email: document.getElementById('emailSearchBtn'),
        username: document.getElementById('usernameSearchBtn'),
        photo: document.getElementById('photoSearchBtn')
    };

    // UI Elements
    const loadingState = document.getElementById('loadingState');
    const resultsContainer = document.getElementById('resultsContainer');
    const emptyState = document.getElementById('emptyState');
    const jsonViewer = document.getElementById('jsonViewer');
    const loadingMessage = document.getElementById('loadingMessage');

    // Stats
    const statsElements = {
        total: document.getElementById('totalSearches'),
        email: document.getElementById('emailChecks'),
        username: document.getElementById('usernameScans'),
        photo: document.getElementById('photoSearches')
    };

    // ============================================
    // Tab Navigation
    // ============================================

    Object.keys(tabs).forEach(tabName => {
        tabs[tabName].addEventListener('click', () => switchTab(tabName));
    });

    function switchTab(tabName) {
        currentTab = tabName;

        // Update tabs
        Object.keys(tabs).forEach(name => {
            if (name === tabName) {
                tabs[name].classList.add('tab-active');
                panels[name].classList.remove('hidden');
            } else {
                tabs[name].classList.remove('tab-active');
                panels[name].classList.add('hidden');
            }
        });
    }

    // ============================================
    // Photo Upload Handling
    // ============================================

    const photoDropzone = document.getElementById('photoDropzone');
    const photoPreview = document.getElementById('photoPreview');
    const photoPreviewImg = document.getElementById('photoPreviewImg');
    const removePhotoBtn = document.getElementById('removePhoto');

    photoDropzone.addEventListener('click', () => inputs.photo.click());

    photoDropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        photoDropzone.classList.add('border-purple-500', 'bg-purple-50');
    });

    photoDropzone.addEventListener('dragleave', () => {
        photoDropzone.classList.remove('border-purple-500', 'bg-purple-50');
    });

    photoDropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        photoDropzone.classList.remove('border-purple-500', 'bg-purple-50');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            handlePhotoUpload(file);
        }
    });

    inputs.photo.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handlePhotoUpload(file);
        }
    });

    function handlePhotoUpload(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            photoPreviewImg.src = e.target.result;
            photoDropzone.classList.add('hidden');
            photoPreview.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }

    removePhotoBtn.addEventListener('click', () => {
        inputs.photo.value = '';
        photoDropzone.classList.remove('hidden');
        photoPreview.classList.add('hidden');
    });

    // ============================================
    // Search Functions
    // ============================================

    searchButtons.email.addEventListener('click', () => performEmailSearch());
    searchButtons.username.addEventListener('click', () => performUsernameSearch());
    searchButtons.photo.addEventListener('click', () => performPhotoSearch());

    async function performEmailSearch() {
        const email = inputs.email.value.trim();
        if (!email) {
            alert('Please enter an email address');
            return;
        }

        const checkBreaches = document.getElementById('checkBreaches').checked;
        const checkRegistrations = document.getElementById('checkRegistrations').checked;

        showLoading('Checking email breaches and registrations...');

        try {
            const response = await fetch('/api/osint/email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    check_breaches: checkBreaches,
                    check_registrations: checkRegistrations
                })
            });

            const data = await response.json();
            lastResult = data;
            updateStats('email');
            displayEmailResults(data);
        } catch (error) {
            showError('Failed to check email: ' + error.message);
        }
    }

    async function performUsernameSearch() {
        const username = inputs.username.value.trim();
        if (!username) {
            alert('Please enter a username');
            return;
        }

        const maxSites = parseInt(document.getElementById('maxSites').value);
        const extractMetadata = document.getElementById('extractMetadata').checked;

        showLoading(`Searching ${maxSites} platforms for username...`);

        try {
            const response = await fetch('/api/osint/username', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username,
                    max_sites: maxSites,
                    extract_metadata: extractMetadata
                })
            });

            const data = await response.json();
            lastResult = data;
            updateStats('username');
            displayUsernameResults(data);
        } catch (error) {
            showError('Failed to search username: ' + error.message);
        }
    }

    async function performPhotoSearch() {
        const file = inputs.photo.files[0];
        if (!file) {
            alert('Please select a photo');
            return;
        }

        showLoading('Performing reverse image search on 3 engines...');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/osint/photo', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            lastResult = data;
            updateStats('photo');
            displayPhotoResults(data);
        } catch (error) {
            showError('Failed to search photo: ' + error.message);
        }
    }

    // ============================================
    // Display Results
    // ============================================

    function displayEmailResults(data) {
        hideLoading();

        const { email, data: results, processing_time } = data;
        const { metadata, breaches, registrations, summary } = results;

        document.getElementById('resultsSubtitle').textContent = `Email: ${email}`;
        document.getElementById('processingTime').textContent = `${processing_time}s`;

        // Summary stats
        const riskColor = {
            low: 'text-green-600',
            medium: 'text-yellow-600',
            high: 'text-orange-600',
            critical: 'text-red-600'
        }[summary.risk_level] || 'text-gray-600';

        document.getElementById('summaryStats').innerHTML = `
            <div class="grid grid-cols-3 gap-4 text-center">
                <div>
                    <p class="text-2xl font-bold ${riskColor}">${summary.risk_level.toUpperCase()}</p>
                    <p class="text-sm text-gray-600">Risk Level</p>
                </div>
                <div>
                    <p class="text-2xl font-bold text-red-600">${summary.total_breaches}</p>
                    <p class="text-sm text-gray-600">Breaches</p>
                </div>
                <div>
                    <p class="text-2xl font-bold text-blue-600">${summary.total_registrations}</p>
                    <p class="text-sm text-gray-600">Registrations</p>
                </div>
            </div>
        `;

        // Results content
        let html = '<div class="space-y-6">';

        // Metadata
        html += `
            <div class="border rounded-lg p-4">
                <h3 class="font-semibold text-gray-800 mb-3 flex items-center">
                    <svg class="w-5 h-5 mr-2 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                        <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
                    </svg>
                    Email Metadata
                </h3>
                <div class="grid grid-cols-2 gap-3 text-sm">
                    <div><span class="text-gray-600">Provider:</span> <span class="font-medium">${metadata.provider}</span></div>
                    <div><span class="text-gray-600">Disposable:</span> <span class="font-medium">${metadata.disposable ? '⚠️ Yes' : '✅ No'}</span></div>
                    <div><span class="text-gray-600">MX Valid:</span> <span class="font-medium">${metadata.mx_valid ? '✅ Yes' : '❌ No'}</span></div>
                    <div><span class="text-gray-600">Domain:</span> <span class="font-medium code-font text-xs">${metadata.domain}</span></div>
                </div>
            </div>
        `;

        // Breaches
        if (breaches.found && breaches.breaches.length > 0) {
            html += `
                <div class="border rounded-lg p-4">
                    <h3 class="font-semibold text-gray-800 mb-3 flex items-center">
                        <svg class="w-5 h-5 mr-2 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"/>
                        </svg>
                        Data Breaches (${breaches.breach_count})
                    </h3>
                    <div class="space-y-2">
                        ${breaches.breaches.slice(0, 10).map(breach => `
                            <div class="bg-red-50 border border-red-200 rounded p-3">
                                <div class="flex justify-between items-start">
                                    <div class="flex-1">
                                        <p class="font-semibold text-red-900">${breach.title || breach.name}</p>
                                        <p class="text-xs text-red-700 mt-1">${breach.breach_date}</p>
                                        <p class="text-xs text-gray-600 mt-1">
                                            ${breach.data_classes.slice(0, 5).join(', ')}
                                        </p>
                                    </div>
                                    <span class="badge badge-danger">${(breach.pwn_count / 1000000).toFixed(1)}M</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // Registrations
        if (registrations.registrations_found > 0) {
            html += `
                <div class="border rounded-lg p-4">
                    <h3 class="font-semibold text-gray-800 mb-3 flex items-center">
                        <svg class="w-5 h-5 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                            <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"/>
                        </svg>
                        Site Registrations (${registrations.registrations_found})
                    </h3>
                    <div class="grid grid-cols-2 gap-2">
                        ${registrations.sites.map(site => {
                            const statusColor = site.registered === 'yes' ? 'badge-success' :
                                              site.registered === 'likely' ? 'badge-warning' : 'badge-info';
                            return `
                                <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                                    <span class="text-sm font-medium">${site.site}</span>
                                    <span class="badge ${statusColor}">${site.registered}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }

        html += '</div>';
        document.getElementById('resultsContent').innerHTML = html;

        showResults();
        updateJSONViewer(data);
    }

    function displayUsernameResults(data) {
        hideLoading();

        const { username, data: results, processing_time } = data;
        const { total_found, results: platforms, by_category, summary } = results;

        document.getElementById('resultsSubtitle').textContent = `Username: ${username}`;
        document.getElementById('processingTime').textContent = `${processing_time}s`;

        // Summary stats
        document.getElementById('summaryStats').innerHTML = `
            <div class="grid grid-cols-4 gap-4 text-center">
                <div>
                    <p class="text-2xl font-bold text-purple-600">${summary.platforms_found}</p>
                    <p class="text-sm text-gray-600">Platforms</p>
                </div>
                <div>
                    <p class="text-2xl font-bold text-green-600">${summary.high_confidence}</p>
                    <p class="text-sm text-gray-600">High Confidence</p>
                </div>
                <div>
                    <p class="text-2xl font-bold text-blue-600">${summary.with_full_name}</p>
                    <p class="text-sm text-gray-600">With Name</p>
                </div>
                <div>
                    <p class="text-2xl font-bold text-pink-600">${summary.with_avatar}</p>
                    <p class="text-sm text-gray-600">With Avatar</p>
                </div>
            </div>
        `;

        // Results content
        let html = '<div class="space-y-6">';

        // Categories
        html += `
            <div class="border rounded-lg p-4">
                <h3 class="font-semibold text-gray-800 mb-3">Categories</h3>
                <div class="flex flex-wrap gap-2">
                    ${Object.entries(by_category).map(([category, items]) => `
                        <span class="badge badge-info">${category} (${items.length})</span>
                    `).join('')}
                </div>
            </div>
        `;

        // Platforms
        html += `
            <div class="space-y-3">
                <h3 class="font-semibold text-gray-800">Found Profiles</h3>
                ${platforms.map(platform => {
                    const confidenceColor = platform.confidence >= 0.8 ? 'text-green-600' :
                                          platform.confidence >= 0.5 ? 'text-yellow-600' : 'text-gray-600';
                    const confidencePercent = Math.round(platform.confidence * 100);

                    return `
                        <div class="border rounded-lg p-4 hover:shadow-md transition result-item">
                            <div class="flex items-start justify-between">
                                <div class="flex-1">
                                    <div class="flex items-center space-x-3">
                                        ${platform.avatar_url ? `<img src="${platform.avatar_url}" class="w-12 h-12 rounded-full" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect fill=%22%23e5e7eb%22 width=%22100%22 height=%22100%22/></svg>'">` : ''}
                                        <div class="flex-1">
                                            <h4 class="font-semibold text-gray-900">${platform.platform}</h4>
                                            ${platform.full_name ? `<p class="text-sm text-gray-600">${platform.full_name}</p>` : ''}
                                            <a href="${platform.url}" target="_blank" class="text-xs text-purple-600 hover:underline">${platform.url}</a>
                                        </div>
                                    </div>
                                    ${platform.bio ? `<p class="text-sm text-gray-600 mt-2">${platform.bio.substring(0, 150)}${platform.bio.length > 150 ? '...' : ''}</p>` : ''}
                                    <div class="flex flex-wrap gap-1 mt-2">
                                        ${platform.tags ? platform.tags.map(tag => `<span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">${tag}</span>`).join('') : ''}
                                    </div>
                                </div>
                                <div class="ml-4">
                                    <div class="text-right">
                                        <p class="${confidenceColor} font-bold text-lg">${confidencePercent}%</p>
                                        <p class="text-xs text-gray-500">confidence</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        html += '</div>';
        document.getElementById('resultsContent').innerHTML = html;

        showResults();
        updateJSONViewer(data);
    }

    function displayPhotoResults(data) {
        hideLoading();

        const { filename, data: results, processing_time } = data;
        const { total_results, results: searchResults, social_profiles, summary } = results;

        document.getElementById('resultsSubtitle').textContent = `Photo: ${filename}`;
        document.getElementById('processingTime').textContent = `${processing_time}s`;

        // Summary stats
        document.getElementById('summaryStats').innerHTML = `
            <div class="grid grid-cols-3 gap-4 text-center">
                <div>
                    <p class="text-2xl font-bold text-purple-600">${summary.total_found}</p>
                    <p class="text-sm text-gray-600">Total Results</p>
                </div>
                <div>
                    <p class="text-2xl font-bold text-blue-600">${summary.social_profiles_found}</p>
                    <p class="text-sm text-gray-600">Social Profiles</p>
                </div>
                <div>
                    <p class="text-2xl font-bold text-green-600">${summary.unique_domains}</p>
                    <p class="text-sm text-gray-600">Unique Domains</p>
                </div>
            </div>
        `;

        // Results content
        let html = '<div class="space-y-6">';

        // Social Profiles
        if (social_profiles && social_profiles.length > 0) {
            html += `
                <div class="border rounded-lg p-4">
                    <h3 class="font-semibold text-gray-800 mb-3 flex items-center">
                        <svg class="w-5 h-5 mr-2 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"/>
                        </svg>
                        Detected Social Profiles
                    </h3>
                    <div class="space-y-2">
                        ${social_profiles.map(profile => `
                            <div class="flex items-center justify-between p-3 bg-purple-50 border border-purple-200 rounded">
                                <div>
                                    <p class="font-semibold text-purple-900">${profile.network}</p>
                                    <a href="${profile.url}" target="_blank" class="text-xs text-purple-600 hover:underline">${profile.url}</a>
                                </div>
                                <span class="badge badge-info">${Math.round(profile.similarity * 100)}% match</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // Search Results by Engine
        ['yandex', 'google', 'tineye'].forEach(engine => {
            if (searchResults[engine] && searchResults[engine].length > 0) {
                html += `
                    <div class="border rounded-lg p-4">
                        <h3 class="font-semibold text-gray-800 mb-3 capitalize">${engine} Results (${searchResults[engine].length})</h3>
                        <div class="grid grid-cols-3 gap-3">
                            ${searchResults[engine].slice(0, 9).map(result => `
                                <a href="${result.url}" target="_blank" class="block hover:opacity-75 transition">
                                    <img src="${result.thumbnail || result.url}" alt="Result" class="w-full h-32 object-cover rounded">
                                    ${result.similarity ? `<p class="text-xs text-center mt-1 text-gray-600">${Math.round(result.similarity * 100)}% match</p>` : ''}
                                </a>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
        });

        html += '</div>';
        document.getElementById('resultsContent').innerHTML = html;

        showResults();
        updateJSONViewer(data);
    }

    // ============================================
    // UI Helpers
    // ============================================

    function showLoading(message) {
        loadingMessage.textContent = message;
        emptyState.classList.add('hidden');
        resultsContainer.classList.add('hidden');
        loadingState.classList.remove('hidden');
    }

    function hideLoading() {
        loadingState.classList.add('hidden');
    }

    function showResults() {
        emptyState.classList.add('hidden');
        resultsContainer.classList.remove('hidden');
        jsonViewer.classList.remove('hidden');
    }

    function showError(message) {
        hideLoading();
        alert(message);
    }

    function updateStats(type) {
        searchHistory[type]++;
        searchHistory.total++;
        statsElements.total.textContent = searchHistory.total;
        statsElements[type].textContent = searchHistory[type];
    }

    function updateJSONViewer(data) {
        const formatted = JSON.stringify(data, null, 2);
        document.getElementById('jsonContent').textContent = formatted;
    }

    // ============================================
    // Quick Actions
    // ============================================

    document.getElementById('clearResults').addEventListener('click', () => {
        resultsContainer.classList.add('hidden');
        jsonViewer.classList.add('hidden');
        emptyState.classList.remove('hidden');
        lastResult = null;
    });

    document.getElementById('exportJSON').addEventListener('click', () => {
        if (!lastResult) {
            alert('No results to export');
            return;
        }
        const dataStr = JSON.stringify(lastResult, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `osint-result-${Date.now()}.json`;
        a.click();
    });

    document.getElementById('viewDocs').addEventListener('click', () => {
        window.open('/docs', '_blank');
    });

    document.getElementById('copyJSON').addEventListener('click', () => {
        const text = document.getElementById('jsonContent').textContent;
        navigator.clipboard.writeText(text).then(() => {
            alert('JSON copied to clipboard!');
        });
    });

    // ============================================
    // API Health Check
    // ============================================

    async function checkAPIHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();

            if (data.status === 'healthy') {
                document.getElementById('apiStatus').innerHTML = `
                    <span class="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
                    API Online (v${data.version})
                `;
            }
        } catch (error) {
            document.getElementById('apiStatus').innerHTML = `
                <span class="w-2 h-2 bg-red-400 rounded-full mr-2"></span>
                API Offline
            `;
        }
    }

    // Initial health check
    checkAPIHealth();
    setInterval(checkAPIHealth, 30000); // Check every 30 seconds

    console.log('🔥 OSINT Panel initialized');
});
