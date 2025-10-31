// AuroraMart Storefront JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all functionality
    initCartFunctionality();
    initWishlistFunctionality();
    initProductActions();
    initFormEnhancements();
    initCarousel();
    initMessages();
    updateCartCount();
});

// Cart Functionality
function initCartFunctionality() {
    // Add to cart buttons
    document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            const quantity = 1; // Default quantity
            
            addToCart(productId, quantity);
        });
    });
}

function addToCart(productId, quantity = 1) {
    fetch('/api/add-to-cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, 'success');
            updateCartCount(data.cart_total);
            
            // Update button state
            const btn = document.querySelector(`[data-product-id="${productId}"]`);
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = 'Added!';
                btn.style.background = '#28a745';
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = '';
                }, 2000);
            }
        } else {
            showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Error adding item to cart', 'error');
    });
}

// Wishlist Functionality
function initWishlistFunctionality() {
    document.querySelectorAll('.wishlist-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            
            if (isUserLoggedIn()) {
                addToWishlist(productId);
            } else {
                showMessage('Please log in to use wishlist', 'warning');
                // Redirect to login page
                setTimeout(() => {
                    window.location.href = '/login/';
                }, 2000);
            }
        });
    });
}

function addToWishlist(productId) {
    fetch('/api/add-to-wishlist/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            product_id: productId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, 'success');
            updateWishlistButton(productId, true);
        } else {
            showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Error adding item to wishlist', 'error');
    });
}

function updateWishlistButton(productId, isInWishlist) {
    const btn = document.querySelector(`[data-product-id="${productId}"]`);
    if (btn) {
        const icon = btn.querySelector('i');
        if (isInWishlist) {
            icon.classList.remove('far');
            icon.classList.add('fas');
            btn.style.color = '#dc3545';
        } else {
            icon.classList.remove('fas');
            icon.classList.add('far');
            btn.style.color = '';
        }
    }
}

// Product Actions
function initProductActions() {
    // Quick view buttons
    document.querySelectorAll('.quick-view-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            // Implement quick view modal
            showQuickView(productId);
        });
    });
    
    // Share buttons
    document.querySelectorAll('.share-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            shareProduct();
        });
    });
}

function showQuickView(productId) {
    // This would open a modal with product details
    // For now, redirect to product detail page
    window.location.href = `/products/${productId}/`;
}

function shareProduct() {
    if (navigator.share) {
        navigator.share({
            title: document.title,
            url: window.location.href
        });
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            showMessage('Product link copied to clipboard!', 'success');
        });
    }
}

// Form Enhancements
function initFormEnhancements() {
    // Newsletter subscription
    const newsletterForm = document.getElementById('newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = this.querySelector('.newsletter-input').value;
            
            subscribeToNewsletter(email);
        });
    }
    
    // Search form enhancements
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                this.closest('form').submit();
            }
        });
    }
    
    // Form field focus effects
    document.querySelectorAll('.form-control').forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
    });
}

function subscribeToNewsletter(email) {
    fetch('/api/subscribe-newsletter/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            email: email
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, 'success');
            document.getElementById('newsletter-form').reset();
        } else {
            showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Error subscribing to newsletter', 'error');
    });
}

// Carousel Functionality
function initCarousel() {
    const carousels = document.querySelectorAll('.hero-carousel, .product-carousel');
    
    carousels.forEach(carousel => {
        const slides = carousel.querySelectorAll('.hero-slide, .product-grid');
        const prevBtn = carousel.querySelector('.carousel-prev');
        const nextBtn = carousel.querySelector('.carousel-next');
        const dots = carousel.querySelectorAll('.dot');
        
        if (slides.length > 1) {
            let currentSlide = 0;
            
            function showSlide(index) {
                slides.forEach((slide, i) => {
                    slide.style.display = i === index ? 'block' : 'none';
                });
                
                if (dots.length > 0) {
                    dots.forEach((dot, i) => {
                        dot.classList.toggle('active', i === index);
                    });
                }
            }
            
            function nextSlide() {
                currentSlide = (currentSlide + 1) % slides.length;
                showSlide(currentSlide);
            }
            
            function prevSlide() {
                currentSlide = (currentSlide - 1 + slides.length) % slides.length;
                showSlide(currentSlide);
            }
            
            // Event listeners
            if (nextBtn) nextBtn.addEventListener('click', nextSlide);
            if (prevBtn) prevBtn.addEventListener('click', prevSlide);
            
            // Dot navigation
            dots.forEach((dot, index) => {
                dot.addEventListener('click', () => {
                    currentSlide = index;
                    showSlide(currentSlide);
                });
            });
            
            // Auto-advance for hero carousel
            if (carousel.classList.contains('hero-carousel')) {
                setInterval(nextSlide, 5000);
            }
            
            // Initialize
            showSlide(0);
        }
    });
}

// Messages System
function initMessages() {
    // Auto-hide messages after 5 seconds
    document.querySelectorAll('.message').forEach(message => {
        setTimeout(() => {
            message.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
    
    // Close button functionality
    document.querySelectorAll('.message-close').forEach(btn => {
        btn.addEventListener('click', function() {
            const message = this.closest('.message');
            message.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(() => {
                message.remove();
            }, 300);
        });
    });
}

function showMessage(text, type = 'info') {
    const messagesContainer = document.querySelector('.messages-container') || createMessagesContainer();
    
    const message = document.createElement('div');
    message.className = `message message-${type}`;
    message.innerHTML = `
        <span>${text}</span>
        <button class="message-close">&times;</button>
    `;
    
    messagesContainer.appendChild(message);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        message.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => {
            message.remove();
        }, 300);
    }, 5000);
    
    // Close button functionality
    message.querySelector('.message-close').addEventListener('click', function() {
        message.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => {
            message.remove();
        }, 300);
    });
}

function createMessagesContainer() {
    const container = document.createElement('div');
    container.className = 'messages-container';
    document.body.appendChild(container);
    return container;
}

// Utility Functions
function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

function isUserLoggedIn() {
    // Check if user is logged in (you can implement this based on your auth system)
    return document.querySelector('.user-dropdown') !== null;
}

function updateCartCount(count) {
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
        cartCountElement.textContent = count;
        cartCountElement.style.display = count > 0 ? 'flex' : 'none';
    }
}

// Initialize cart count on page load
function updateCartCount() {
    // This would typically fetch the current cart count from the server
    // For now, we'll just show 0
    updateCartCount(0);
}

// Smooth scrolling for anchor links
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

// Lazy loading for images
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Initialize lazy loading if supported
if ('IntersectionObserver' in window) {
    initLazyLoading();
}

// Add CSS for slideOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
