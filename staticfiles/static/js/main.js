// Квартиркинъ - Основной JavaScript файл

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всех компонентов
    initComparisonSlider();
    initMobileMenu();
    initScrollReveal();
    initNavbar();
    initAIAssistant();

    // Дополнительные skills-функции
    initPhotoGallery();
    initApartmentsFilter();
    initCommentLikes();
    calculateBookingTotal();
});

// ===== Слайдер сравнения фото =====
function initComparisonSlider() {
    const slider = document.getElementById('comparison-slider');
    const before = document.getElementById('comparison-before');
    const handle = document.getElementById('comparison-handle');
    
    if (!slider || !before || !handle) return;
    
    let isDragging = false;
    
    const updateSlider = (x) => {
        const rect = slider.getBoundingClientRect();
        let position = ((x - rect.left) / rect.width) * 100;
        position = Math.max(0, Math.min(100, position));
        
        before.style.width = position + '%';
        handle.style.left = position + '%';
    };
    
    handle.addEventListener('mousedown', () => isDragging = true);
    document.addEventListener('mouseup', () => isDragging = false);
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        updateSlider(e.clientX);
    });
    
    // Touch события для мобильных
    handle.addEventListener('touchstart', () => isDragging = true);
    document.addEventListener('touchend', () => isDragging = false);
    document.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        updateSlider(e.touches[0].clientX);
    });
    
    // Клик по слайдеру
    slider.addEventListener('click', (e) => {
        updateSlider(e.clientX);
    });
}

// ===== Мобильное меню =====
function initMobileMenu() {
    const menuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const menuLinks = document.querySelectorAll('.mobile-menu-link');
    
    if (!menuBtn || !mobileMenu) return;
    
    let isOpen = false;
    
    menuBtn.addEventListener('click', () => {
        isOpen = !isOpen;
        if (isOpen) {
            mobileMenu.classList.remove('opacity-0', 'pointer-events-none');
            mobileMenu.classList.add('opacity-100', 'pointer-events-auto');
            menuBtn.children[0].style.transform = 'rotate(45deg) translateY(4px)';
            menuBtn.children[1].style.transform = 'rotate(-45deg) translateY(-4px)';
        } else {
            mobileMenu.classList.add('opacity-0', 'pointer-events-none');
            mobileMenu.classList.remove('opacity-100', 'pointer-events-auto');
            menuBtn.children[0].style.transform = '';
            menuBtn.children[1].style.transform = '';
        }
    });
    
    // Закрытие при клике на ссылку
    menuLinks.forEach(link => {
        link.addEventListener('click', () => {
            isOpen = false;
            mobileMenu.classList.add('opacity-0', 'pointer-events-none');
            mobileMenu.classList.remove('opacity-100', 'pointer-events-auto');
            menuBtn.children[0].style.transform = '';
            menuBtn.children[1].style.transform = '';
        });
    });
}

// ===== Scroll Reveal анимации =====
function initScrollReveal() {
    const reveals = document.querySelectorAll('.reveal');
    
    const revealOnScroll = () => {
        reveals.forEach(element => {
            const windowHeight = window.innerHeight;
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 100;
            
            if (elementTop < windowHeight - elementVisible) {
                element.classList.add('active');
            }
        });
    };
    
    window.addEventListener('scroll', revealOnScroll);
    revealOnScroll(); // Проверка при загрузке
}

// ===== Навигация =====
function initNavbar() {
    const navbar = document.getElementById('navbar');
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            navbar.classList.add('nav-scrolled');
        } else {
            navbar.classList.remove('nav-scrolled');
        }
        
        lastScroll = currentScroll;
    });
}

// ===== Нейро-консультант =====
function initAIAssistant() {
    const btn = document.getElementById('ai-assistant-btn');
    const modal = document.getElementById('ai-modal');
    const modalContent = document.getElementById('ai-modal-content');
    const closeBtn = document.getElementById('ai-modal-close');
    const chatForm = document.getElementById('ai-chat-form');
    const chatInput = document.getElementById('ai-chat-input');
    const chatMessages = document.getElementById('ai-chat-messages');
    
    if (!btn || !modal) return;
    
    // Открытие модального окна
    btn.addEventListener('click', () => {
        modal.classList.remove('opacity-0', 'pointer-events-none');
        modal.classList.add('opacity-100', 'pointer-events-auto');
        setTimeout(() => {
            modalContent.classList.remove('scale-95', 'opacity-0');
            modalContent.classList.add('scale-100', 'opacity-100');
        }, 50);
    });
    
    // Закрытие модального окна
    const closeModal = () => {
        modalContent.classList.add('scale-95', 'opacity-0');
        modalContent.classList.remove('scale-100', 'opacity-100');
        setTimeout(() => {
            modal.classList.add('opacity-0', 'pointer-events-none');
            modal.classList.remove('opacity-100', 'pointer-events-auto');
        }, 300);
    };
    
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    
        // ---- Helpers ------------------------------------------------------
    // Read the CSRF token from the cookie Django sets — required for POST.
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }

    // Minimal HTML-escape — protects against accidental markup in replies.
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text == null ? '' : String(text);
        return div.innerHTML;
    }

    function addMessage(text, sender, opts) {
        if (!chatMessages) return null;
        const options = opts || {};
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`;
                const bubbleClasses = sender === 'user'
            ? 'bg-sea-500 text-white rounded-br-md'
            : 'bg-sand-100 text-sand-800 rounded-bl-md border border-sand-200';
        const degradedNote = options.degraded
            ? '<p class="text-[10px] mt-2 italic opacity-70">Упрощённый режим</p>'
            : '';
        // Preserve newlines from the model output (white-space: pre-wrap).
        messageDiv.innerHTML = `
            <div class="max-w-[80%] px-4 py-3 rounded-2xl ${bubbleClasses}">
                <p class="text-sm" style="white-space: pre-wrap;">${escapeHtml(text)}</p>
                ${degradedNote}
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    }

    function addTypingIndicator() {
        if (!chatMessages) return null;
        const wrap = document.createElement('div');
        wrap.className = 'flex justify-start';
        wrap.setAttribute('data-typing', '1');
        wrap.innerHTML = `
            <div class="max-w-[80%] px-4 py-3 rounded-2xl bg-sand-100 text-sand-800 rounded-bl-md">
                <p class="text-sm opacity-60">…</p>
            </div>
        `;
        chatMessages.appendChild(wrap);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return wrap;
    }

    // ---- Submit handler ----------------------------------------------
    if (chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;

            addMessage(message, 'user');
            chatInput.value = '';
            chatInput.disabled = true;

            const typing = addTypingIndicator();

            try {
                const response = await fetch('/ai/chat/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({ message }),
                });

                if (typing) typing.remove();

                if (response.status === 429) {
                    addMessage(
                        'Слишком много вопросов подряд. Подождите немного и попробуйте снова.',
                        'assistant',
                        { degraded: true }
                    );
                    return;
                }

                if (!response.ok) {
                    let errText = 'Не удалось получить ответ. Попробуйте ещё раз чуть позже.';
                    try {
                        const data = await response.json();
                        if (data && data.error) errText = data.error;
                    } catch (_) { /* ignore */ }
                    addMessage(errText, 'assistant', { degraded: true });
                    return;
                }

                const data = await response.json();
                addMessage(
                    data.reply || 'Извините, ответа не получилось.',
                    'assistant',
                    { degraded: !!data.degraded }
                );
            } catch (err) {
                if (typing) typing.remove();
                addMessage(
                    'Сетевая ошибка. Проверьте подключение и попробуйте ещё раз.',
                    'assistant',
                    { degraded: true }
                );
            } finally {
                chatInput.disabled = false;
                chatInput.focus();
            }
        });
    }
}

// ===== Функция расчёта стоимости бронирования =====
function calculateBookingTotal() {
    const checkIn = document.getElementById('check-in');
    const checkOut = document.getElementById('check-out');
    const guests = document.getElementById('guests');
    const petCheckbox = document.getElementById('pet-checkbox');
    const totalDisplay = document.getElementById('booking-total');
    const pricePerNight = parseInt(document.getElementById('price-per-night')?.value || 0);
    
    if (!checkIn || !checkOut || !totalDisplay) return;
    
    const updateTotal = () => {
        const start = new Date(checkIn.value);
        const end = new Date(checkOut.value);
        
        if (start && end && end > start) {
            const nights = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
            const total = nights * pricePerNight;
            totalDisplay.textContent = total.toLocaleString('ru-RU') + ' ₽';
        }
    };
    
    checkIn.addEventListener('change', updateTotal);
    checkOut.addEventListener('change', updateTotal);
}

// ===== Инициализация Яндекс Карты =====
function initYandexMap(coords, address) {
    if (typeof ymaps === 'undefined') {
        console.warn('Yandex Maps API не загружен');
        return;
    }
    
        // Координаты всегда приходят из БД (apartment.latitude/longitude).
    // Фоллбэк на Геленджик нужен лишь на случай отсутствия данных.
    const fallbackCoords = [44.5622, 38.0848];

    ymaps.ready(function() {
        const map = new ymaps.Map('yandex-map', {
            center: coords || fallbackCoords,
            zoom: 15,
            controls: ['zoomControl', 'fullscreenControl']
        });

        const placemark = new ymaps.Placemark(coords || fallbackCoords, {
            balloonContent: address || 'Квартира Квартиркинъ'
        }, {
            preset: 'islands#icon',
            iconColor: '#3B63BF'
        });
        
        map.geoObjects.add(placemark);
    });
}

// ===== Галерея фото =====
function initPhotoGallery() {
    const mainImage = document.getElementById('gallery-main');
    const thumbnails = document.querySelectorAll('.gallery-thumb');
    
    if (!mainImage || thumbnails.length === 0) return;
    
    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', () => {
            const newSrc = thumb.getAttribute('data-full');
            mainImage.style.opacity = '0';
            setTimeout(() => {
                mainImage.src = newSrc;
                mainImage.style.opacity = '1';
            }, 200);
            
            thumbnails.forEach(t => t.classList.remove('ring-2', 'ring-sea-500'));
            thumb.classList.add('ring-2', 'ring-sea-500');
        });
    });
}

// ===== Валидация форм =====
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('border-red-500');
            } else {
                field.classList.remove('border-red-500');
            }
        });
        
        if (isValid) {
            // Здесь будет отправка данных на сервер
            showNotification('Форма успешно отправлена!', 'success');
            form.reset();
        } else {
            showNotification('Пожалуйста, заполните все обязательные поля', 'error');
        }
    });
}

// ===== Уведомления =====
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-sea-500'
    };
    
    notification.className = `fixed top-24 left-1/2 -translate-x-1/2 ${colors[type]} text-white px-6 py-3 rounded-full shadow-lg z-50 transform transition-all duration-300 translate-y-[-100%] opacity-0`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.remove('translate-y-[-100%]', 'opacity-0');
    }, 100);
    
    setTimeout(() => {
        notification.classList.add('translate-y-[-100%]', 'opacity-0');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ===== Фильтрация квартир =====
function initApartmentsFilter() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const apartmentCards = document.querySelectorAll('.apartment-card');
    
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const filter = btn.getAttribute('data-filter');
            
            filterButtons.forEach(b => b.classList.remove('bg-sand-800', 'text-white'));
            btn.classList.add('bg-sand-800', 'text-white');
            
            apartmentCards.forEach(card => {
                const category = card.getAttribute('data-category');
                if (filter === 'all' || category === filter) {
                    card.style.display = 'block';
                    setTimeout(() => card.style.opacity = '1', 10);
                } else {
                    card.style.opacity = '0';
                    setTimeout(() => card.style.display = 'none', 300);
                }
            });
        });
    });
}

// ===== Лайк/дизлайк комментария =====
function initCommentLikes() {
    const likeButtons = document.querySelectorAll('.comment-like');
    
    likeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const count = btn.querySelector('.like-count');
            const icon = btn.querySelector('i');
            let currentCount = parseInt(count.textContent);
            
            if (btn.classList.contains('text-sea-500')) {
                btn.classList.remove('text-sea-500');
                icon.classList.remove('ph-heart-fill');
                icon.classList.add('ph-heart');
                count.textContent = currentCount - 1;
            } else {
                btn.classList.add('text-sea-500');
                icon.classList.remove('ph-heart');
                icon.classList.add('ph-heart-fill');
                count.textContent = currentCount + 1;
            }
        });
    });
}

// Экспорт функций для использования в других скриптах
window.Kvartirkin = {
    initYandexMap,
    calculateBookingTotal,
    validateForm,
    showNotification,
    initPhotoGallery,
    initApartmentsFilter,
    initCommentLikes
};