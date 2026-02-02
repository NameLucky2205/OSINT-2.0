/**
 * PeopleFinder Frontend Application
 */

// Ждём загрузки DOM
document.addEventListener('DOMContentLoaded', function() {

// State
let currentMode = 'photo'; // 'photo' or 'data'
let searchType = 'username'; // 'username' or 'email'
let selectedFile = null;

// API Base URL
const API_BASE = window.location.origin;

// DOM Elements
const photoBtn = document.getElementById('photoBtn');
const dataBtn = document.getElementById('dataBtn');
const photoSearch = document.getElementById('photoSearch');
const dataSearch = document.getElementById('dataSearch');
const dropzone = document.getElementById('dropzone');
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const previewImg = document.getElementById('previewImg');
const removeImage = document.getElementById('removeImage');
const photoSearchBtn = document.getElementById('photoSearchBtn');
const dataInput = document.getElementById('dataInput');
const usernameBtn = document.getElementById('usernameBtn');
const emailBtn = document.getElementById('emailBtn');
const dataSearchBtn = document.getElementById('dataSearchBtn');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const resultsCount = document.getElementById('resultsCount');
const resultsContainer = document.getElementById('resultsContainer');

// Toggle between Photo and Data search
photoBtn.addEventListener('click', () => {
    currentMode = 'photo';
    photoBtn.classList.add('active');
    dataBtn.classList.remove('active');
    photoSearch.classList.remove('hidden');
    dataSearch.classList.add('hidden');
    hideResults();
});

dataBtn.addEventListener('click', () => {
    currentMode = 'data';
    dataBtn.classList.add('active');
    photoBtn.classList.remove('active');
    dataSearch.classList.remove('hidden');
    photoSearch.classList.add('hidden');
    hideResults();
});

// Toggle between Username and Email search
usernameBtn.addEventListener('click', () => {
    searchType = 'username';
    usernameBtn.classList.remove('bg-gray-100', 'text-gray-700');
    usernameBtn.classList.add('bg-purple-100', 'text-purple-700');
    emailBtn.classList.remove('bg-purple-100', 'text-purple-700');
    emailBtn.classList.add('bg-gray-100', 'text-gray-700');
    dataInput.placeholder = 'Введите username...';
});

emailBtn.addEventListener('click', () => {
    searchType = 'email';
    emailBtn.classList.remove('bg-gray-100', 'text-gray-700');
    emailBtn.classList.add('bg-purple-100', 'text-purple-700');
    usernameBtn.classList.remove('bg-purple-100', 'text-purple-700');
    usernameBtn.classList.add('bg-gray-100', 'text-gray-700');
    dataInput.placeholder = 'Введите email...';
});

// Drag and Drop functionality
dropzone.addEventListener('click', () => imageInput.click());

dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

imageInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

removeImage.addEventListener('click', () => {
    selectedFile = null;
    imageInput.value = '';
    imagePreview.classList.add('hidden');
    dropzone.classList.remove('hidden');
});

// Handle file selection
function handleFileSelect(file) {
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        alert('Пожалуйста, выберите изображение (JPG, PNG, GIF, WEBP)');
        return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('Файл слишком большой. Максимальный размер: 10MB');
        return;
    }

    selectedFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        dropzone.classList.add('hidden');
        imagePreview.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
}

// Photo Search
photoSearchBtn.addEventListener('click', async () => {
    if (!selectedFile) {
        alert('Пожалуйста, выберите изображение');
        return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    await performSearch(`${API_BASE}/api/search/image`, formData, false);
});

// Data Search
dataSearchBtn.addEventListener('click', async () => {
    const query = dataInput.value.trim();

    if (!query || query.length < 3) {
        alert('Введите минимум 3 символа');
        return;
    }

    const data = {
        query: query,
        search_type: searchType,
        max_sites: 15
    };

    await performSearch(`${API_BASE}/api/search/text`, data, true);
});

// Enter key for text search
dataInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        dataSearchBtn.click();
    }
});

// Perform Search
async function performSearch(url, data, isJSON) {
    showLoading();
    hideResults();

    try {
        const options = {
            method: 'POST',
        };

        if (isJSON) {
            options.headers = {
                'Content-Type': 'application/json',
            };
            options.body = JSON.stringify(data);
        } else {
            options.body = data;
        }

        const response = await fetch(url, options);
        const result = await response.json();

        hideLoading();

        if (!response.ok) {
            throw new Error(result.detail || 'Ошибка при поиске');
        }

        displayResults(result);

    } catch (error) {
        hideLoading();
        alert(`Ошибка: ${error.message}`);
        console.error('Search error:', error);
    }
}

// Display Results
function displayResults(data) {
    resultsContainer.innerHTML = '';

    const totalResults = data.total_found || 0;
    const resultsList = data.results || [];

    if (totalResults === 0) {
        resultsCount.textContent = 'Результаты не найдены';
        resultsContainer.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <svg class="mx-auto h-16 w-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <p class="text-lg">К сожалению, ничего не найдено</p>
                <p class="text-sm mt-2">Попробуйте другой запрос или изображение</p>
            </div>
        `;
    } else {
        resultsCount.textContent = `Найдено результатов: ${totalResults}`;

        resultsList.forEach((result, index) => {
            const card = createResultCard(result, index);
            resultsContainer.appendChild(card);
        });
    }

    results.classList.remove('hidden');
    results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Create Result Card
function createResultCard(result, index) {
    const card = document.createElement('div');
    card.className = 'result-card bg-gray-50 rounded-lg p-5 hover:bg-gray-100 transition';
    card.style.animationDelay = `${index * 0.1}s`;

    // Определяем тип результата
    const platform = result.platform || result.source || result.type || 'Неизвестно';
    const url = result.url || '#';
    const title = result.title || platform;
    const confidence = result.confidence || 0.5;
    const status = result.status || 'found';

    // Confidence bar
    const confidencePercent = Math.round(confidence * 100);
    const confidenceColor = confidence > 0.7 ? 'bg-green-500' : confidence > 0.4 ? 'bg-yellow-500' : 'bg-red-500';

    card.innerHTML = `
        <div class="flex items-start justify-between">
            <div class="flex-1">
                <div class="flex items-center gap-2 mb-2">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        ${platform}
                    </span>
                    ${status === 'found' ?
                        '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">Найдено</span>' :
                        '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Возможно</span>'
                    }
                </div>
                <p class="text-gray-800 font-medium mb-2">${escapeHtml(title)}</p>
                ${url !== '#' ? `
                    <a href="${escapeHtml(url)}" target="_blank" class="text-purple-600 hover:text-purple-800 text-sm break-all">
                        ${escapeHtml(url)}
                    </a>
                ` : ''}
                ${result.note ? `<p class="text-gray-500 text-sm mt-2">${escapeHtml(result.note)}</p>` : ''}

                <!-- Confidence Bar -->
                <div class="mt-3">
                    <div class="flex justify-between text-xs text-gray-600 mb-1">
                        <span>Уверенность</span>
                        <span>${confidencePercent}%</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2">
                        <div class="${confidenceColor} h-2 rounded-full transition-all duration-500" style="width: ${confidencePercent}%"></div>
                    </div>
                </div>
            </div>

            ${url !== '#' ? `
                <a href="${escapeHtml(url)}" target="_blank" class="ml-4 text-purple-600 hover:text-purple-800">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                    </svg>
                </a>
            ` : ''}
        </div>
    `;

    return card;
}

// Utility Functions
function showLoading() {
    loading.classList.remove('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
}

function hideResults() {
    results.classList.add('hidden');
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

// Health Check on Load
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        const health = await response.json();
        console.log('API Health:', health);
    } catch (error) {
        console.error('API не доступен:', error);
    }
}

// Проверяем здоровье API при загрузке
checkHealth();

}); // Конец DOMContentLoaded
