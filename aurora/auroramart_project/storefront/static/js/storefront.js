// AuroraMart Storefront JavaScript
// Minimal JavaScript - only for UI interactions (carousel, gallery, messages)
// All business logic is in views.py and business_logic.py

document.addEventListener('DOMContentLoaded', function() {
    initCarousel();
    initImageGallery();
    initMessages();
    preventButtonNavigation();
    initAddToCart();
});

// Prevent buttons from triggering link navigation
function preventButtonNavigation() {
    // Prevent product card link navigation when clicking buttons
    document.querySelectorAll('.product-cart-actions, .product-actions, .item-actions, .item-quantity').forEach(container => {
        container.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
}

// Image Gallery Functionality
function initImageGallery() {
    document.querySelectorAll('.thumbnail').forEach(thumbnail => {
        thumbnail.addEventListener('click', function() {
            const mainImage = document.getElementById('main-product-image');
            const imageUrl = this.getAttribute('data-image-url') || this.querySelector('img')?.src;
            if (mainImage && imageUrl) {
                mainImage.src = imageUrl;
            }
            
            // Update active thumbnail
            document.querySelectorAll('.thumbnail').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
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
            let autoSlideInterval = null;
            const slideInterval = 5000; // 5 seconds
            
            function showSlide(index) {
                // Remove active class from all slides
                slides.forEach((slide, i) => {
                    slide.classList.remove('active');
                    if (i !== index) {
                        slide.style.opacity = '0';
                        slide.style.display = 'none';
                    }
                });
                
                // Show current slide with fade-in animation
                const currentSlideElement = slides[index];
                currentSlideElement.style.display = 'block';
                setTimeout(() => {
                    currentSlideElement.classList.add('active');
                    currentSlideElement.style.opacity = '1';
                }, 10);
                
                // Update dots
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
            
            function startAutoSlide() {
                if (autoSlideInterval) {
                    clearInterval(autoSlideInterval);
                }
                autoSlideInterval = setInterval(nextSlide, slideInterval);
            }
            
            function stopAutoSlide() {
                if (autoSlideInterval) {
                    clearInterval(autoSlideInterval);
                    autoSlideInterval = null;
                }
            }
            
            // Button event listeners
            if (nextBtn) {
                nextBtn.addEventListener('click', () => {
                    nextSlide();
                    startAutoSlide(); // Restart auto-slide after manual navigation
                });
            }
            if (prevBtn) {
                prevBtn.addEventListener('click', () => {
                    prevSlide();
                    startAutoSlide(); // Restart auto-slide after manual navigation
                });
            }
            
            // Dot event listeners
            dots.forEach((dot, index) => {
                dot.addEventListener('click', () => {
                    currentSlide = index;
                    showSlide(currentSlide);
                    startAutoSlide(); // Restart auto-slide after manual navigation
                });
            });
            
            // Auto-slide for hero carousel
            if (carousel.classList.contains('hero-carousel')) {
                startAutoSlide();
                
                // Pause on hover, resume on mouse leave
                carousel.addEventListener('mouseenter', stopAutoSlide);
                carousel.addEventListener('mouseleave', startAutoSlide);
            }
            
            // Initialize first slide
            // Set first slide as active initially
            if (slides.length > 0) {
                slides[0].style.display = 'block';
                slides[0].style.opacity = '1';
                slides[0].classList.add('active');
                if (dots.length > 0) {
                    dots[0].classList.add('active');
                }
            }
        }
    });
}

// Messages System
function initMessages() {
    document.querySelectorAll('.message').forEach(message => {
        setTimeout(() => {
            message.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
    
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

// AJAX Add to Cart functionality
function initAddToCart() {
    // Handle add to cart forms - use event delegation to catch dynamically added forms
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (!form.classList.contains('add-to-cart-form')) {
            return;
        }
        
        e.preventDefault();
        e.stopPropagation();
            
            const formData = new FormData(this);
            const submitButton = this.querySelector('.add-to-cart-btn');
            const originalText = submitButton ? submitButton.innerHTML : '';
            
            // Disable button during request
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = 'Adding...';
            }
            
            // Add AJAX header
            const xhr = new XMLHttpRequest();
            xhr.open('POST', this.action, true);
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.setRequestHeader('X-CSRFToken', window.csrfToken || document.querySelector('[name=csrfmiddlewaretoken]')?.value);
            
            xhr.onload = function() {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        
                        // Update cart count
                        const cartCountElement = document.getElementById('cart-count');
                        if (cartCountElement && response.cart_count !== undefined) {
                            cartCountElement.textContent = response.cart_count;
                        }
                        
                        // Show success message
                        showMessage(response.message || 'Item added to cart!', 'success');
                        
                        // If product is now in cart and we're on product detail page, reload to show quantity picker
                        // For other pages, just show success message without reloading
                        if (response.success) {
                            // Check if we're on product detail page (has .product-cart-action)
                            const productCartAction = form.closest('.product-cart-action');
                            if (productCartAction) {
                                // Save scroll position before reload
                                sessionStorage.setItem('scrollPosition', window.pageYOffset || document.documentElement.scrollTop);
                                // Reload after a short delay to show quantity picker
                                setTimeout(() => {
                                    window.location.reload();
                                }, 1000);
                            }
                            // For product list pages and other pages, no reload needed
                        }
                    } catch (e) {
                        showMessage('Item added to cart!', 'success');
                    }
                } else {
                    showMessage('Error adding item to cart. Please try again.', 'error');
                }
                
                // Re-enable button
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalText;
                }
            };
            
            xhr.onerror = function() {
                showMessage('Error adding item to cart. Please try again.', 'error');
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalText;
                }
            };
            
            xhr.send(formData);
        });
    });
    
    // Handle quantity update forms (for product detail page)
    document.querySelectorAll('form[action*="update_cart_item"]').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitButton = this.querySelector('button[type="submit"]');
            
            // Add AJAX header
            const xhr = new XMLHttpRequest();
            xhr.open('POST', this.action, true);
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.setRequestHeader('X-CSRFToken', window.csrfToken || document.querySelector('[name=csrfmiddlewaretoken]')?.value);
            
            xhr.onload = function() {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        
                        // Update cart count
                        const cartCountElement = document.getElementById('cart-count');
                        if (cartCountElement && response.cart_count !== undefined) {
                            cartCountElement.textContent = response.cart_count;
                        }
                        
                        // If item was removed, reload page to show "Add to Cart" button
                        if (response.removed) {
                            setTimeout(() => {
                                window.location.reload();
                            }, 500);
                        } else {
                            // Update quantity display
                            const quantityValue = form.closest('.quantity-picker')?.querySelector('.quantity-value');
                            if (quantityValue && response.quantity !== undefined) {
                                quantityValue.textContent = response.quantity;
                            } else {
                                // Reload to update UI
                                window.location.reload();
                            }
                        }
                    } catch (e) {
                        // Reload on error
                        window.location.reload();
                    }
                } else {
                    window.location.reload();
                }
            };
            
            xhr.onerror = function() {
                window.location.reload();
            };
            
            xhr.send(formData);
        });
    });
}

// Show message without page refresh
function showMessage(message, type) {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.ajax-message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `ajax-message message message-${type}`;
    messageDiv.textContent = message;
    
    // Add close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'message-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', () => messageDiv.remove());
    messageDiv.appendChild(closeBtn);
    
    // Add to messages container or create one
    let messagesContainer = document.querySelector('.messages-container');
    if (!messagesContainer) {
        messagesContainer = document.createElement('div');
        messagesContainer.className = 'messages-container';
        document.body.appendChild(messagesContainer);
    }
    
    messagesContainer.appendChild(messageDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageDiv.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => messageDiv.remove(), 300);
    }, 5000);
}


// Animated Search Placeholder
function initAnimatedSearchPlaceholder() {
    const placeholderText = document.getElementById('placeholder-text');
    const searchInput = document.getElementById('search-input');
    
    if (!placeholderText || !searchInput) {
        return;
    }
    
    // Get subcategories from data attribute
    const subcategoriesData = searchInput.dataset.subcategories;
    let subcategories = ['product'];
    
    if (subcategoriesData) {
        // Split by comma and trim each item
        subcategories = subcategoriesData.split(',').map(function(item) {
            return item.trim();
        }).filter(function(item) {
            return item.length > 0;
        });
    }
    
    // Ensure we have at least one item
    if (subcategories.length === 0) {
        subcategories = ['product'];
    }
    
    let currentIndex = 0;
    let interval = null;
    
    function updatePlaceholder() {
        // Only animate if input is empty and not focused
        if (searchInput.value === '' && document.activeElement !== searchInput) {
            placeholderText.style.opacity = '0';
            setTimeout(function() {
                placeholderText.textContent = subcategories[currentIndex] || 'product';
                placeholderText.style.opacity = '1';
                currentIndex = (currentIndex + 1) % subcategories.length;
            }, 300); // Fade out, then change text, then fade in
        }
    }
    
    function startAnimation() {
        if (interval) {
            clearInterval(interval);
        }
        interval = setInterval(updatePlaceholder, 2500); // Change every 2.5 seconds
    }
    
    function stopAnimation() {
        if (interval) {
            clearInterval(interval);
            interval = null;
        }
    }
    
    // Pause animation when user focuses on input
    searchInput.addEventListener('focus', function() {
        stopAnimation();
    });
    
    // Resume animation when user blurs and input is empty
    searchInput.addEventListener('blur', function() {
        if (searchInput.value === '') {
            startAnimation();
        }
    });
    
    // Stop animation when user types
    searchInput.addEventListener('input', function() {
        if (searchInput.value === '') {
            startAnimation();
        } else {
            stopAnimation();
        }
    });
    
    // Start animation
    startAnimation();
    updatePlaceholder();
}

// All business logic is handled by Django views via form submissions
// AJAX is used only for better UX (no page refresh)

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
