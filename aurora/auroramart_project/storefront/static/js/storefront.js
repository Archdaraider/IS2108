// AuroraMart Storefront JavaScript
// Minimal JavaScript - only for UI interactions (carousel, gallery, messages)
// All business logic is in views.py and business_logic.py

document.addEventListener('DOMContentLoaded', function() {
    initCarousel();
    initImageGallery();
    initMessages();
    preventButtonNavigation();
    initAddToCart();
    initAnimatedSearchPlaceholder();
    initDateInputRestrictions();
    initPasswordToggle();
    initCategorySubcategoryPanels();
    initNavigationDropdownPositioning();
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
        // Look for buttons in parent container (hero-section) instead of inside carousel
        const parentSection = carousel.parentElement;
        const prevBtn = parentSection ? parentSection.querySelector('.carousel-prev') : null;
        const nextBtn = parentSection ? parentSection.querySelector('.carousel-next') : null;
        const dots = parentSection ? parentSection.querySelectorAll('.dot') : [];
        
        console.log('Carousel Debug:', {
            slides: slides.length,
            hasPrevBtn: !!prevBtn,
            hasNextBtn: !!nextBtn,
            dotsCount: dots.length
        });
        
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
                console.log('Next button found, adding event listener');
                nextBtn.addEventListener('click', (e) => {
                    console.log('Next button clicked!');
                    e.preventDefault();
                    e.stopPropagation();
                    nextSlide();
                    startAutoSlide(); // Restart auto-slide after manual navigation
                });
            } else {
                console.log('Next button NOT found');
            }
            
            if (prevBtn) {
                console.log('Prev button found, adding event listener');
                prevBtn.addEventListener('click', (e) => {
                    console.log('Prev button clicked!');
                    e.preventDefault();
                    e.stopPropagation();
                    prevSlide();
                    startAutoSlide(); // Restart auto-slide after manual navigation
                });
            } else {
                console.log('Prev button NOT found');
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
            
        const formData = new FormData(form);
        const submitButton = form.querySelector('.add-to-cart-btn');
            const originalText = submitButton ? submitButton.innerHTML : '';
            
            // Disable button during request
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = 'Adding...';
            }
            
            // Add AJAX header
            const xhr = new XMLHttpRequest();
        xhr.open('POST', form.action, true);
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


// Animated Search Placeholder with 3D Flip Animation
function initAnimatedSearchPlaceholder() {
    const placeholderText = document.getElementById('placeholder-text');
    const placeholderTextNext = document.getElementById('placeholder-text-next');
    const placeholderContainer = document.querySelector('.placeholder-text-container');
    const searchInput = document.getElementById('search-input');
    
    if (!placeholderText || !placeholderTextNext || !placeholderContainer || !searchInput) {
        console.log('Search placeholder elements not found:', {
            placeholderText: !!placeholderText,
            placeholderTextNext: !!placeholderTextNext,
            placeholderContainer: !!placeholderContainer,
            searchInput: !!searchInput
        });
        return;
    }
    
    // Get subcategories from data attribute (from ML model predictions)
    const subcategoriesData = searchInput.getAttribute('data-subcategories') || '';
    let subcategories = [];
    
    if (subcategoriesData && subcategoriesData.trim() !== '') {
        // Split by comma and trim each item
        subcategories = subcategoriesData.split(',').map(function(item) {
            return item.trim();
        }).filter(function(item) {
            return item.length > 0 && item !== 'product';
        });
    }
    
    // Always add 'product' as fallback, and ensure we have at least 2 items for animation
    if (subcategories.length === 0) {
        subcategories = ['product', 'items', 'products'];
    } else if (subcategories.length === 1) {
        subcategories.push('product');
    }
    
    // Format subcategories - capitalize first letter
    const formattedSubcategories = subcategories.map(function(subcat) {
        return subcat.charAt(0).toUpperCase() + subcat.slice(1).toLowerCase();
    });
    
    console.log('Subcategories for animation:', formattedSubcategories);
    
    let currentIndex = 0;
    let interval = null;
    let isAnimating = false;
    
    function updatePlaceholder() {
        // Only animate if input is empty and not focused
        const inputEmpty = !searchInput.value || searchInput.value.trim() === '';
        const notFocused = document.activeElement !== searchInput;
        
        if (inputEmpty && notFocused && !isAnimating && formattedSubcategories.length > 1) {
            isAnimating = true;
            
            // Set next text
            const nextIndex = (currentIndex + 1) % formattedSubcategories.length;
            const nextText = formattedSubcategories[nextIndex] || 'Product';
            placeholderTextNext.textContent = nextText;
            
            // Force reflow to ensure initial state is applied
            void placeholderContainer.offsetHeight;
            
            // Start flip animation
            placeholderContainer.classList.add('flipping');
            
            // After animation completes, swap the texts
            setTimeout(function() {
                // Swap current and next
                placeholderText.textContent = nextText;
                placeholderTextNext.textContent = '';
                
                // Reset animation state
                placeholderContainer.classList.remove('flipping');
                
                // Reset next text position for next animation
                setTimeout(function() {
                    placeholderTextNext.style.transform = 'rotateX(90deg)';
                    placeholderTextNext.style.opacity = '0';
                }, 50);
                
                // Move to next index
                currentIndex = nextIndex;
                isAnimating = false;
            }, 600); // Match CSS transition duration
        }
    }
    
    function startAnimation() {
        if (interval) {
            clearInterval(interval);
        }
        // Start immediately, then cycle every 3 seconds
        updatePlaceholder(); // Start immediately
        interval = setInterval(updatePlaceholder, 3000);
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
        // Hide placeholder when focused
        if (placeholderContainer) {
            placeholderContainer.style.opacity = '0';
        }
    });
    
    // Resume animation when user blurs and input is empty
    searchInput.addEventListener('blur', function() {
        if (!searchInput.value || searchInput.value.trim() === '') {
            if (placeholderContainer) {
                placeholderContainer.style.opacity = '1';
            }
            startAnimation();
        }
    });
    
    // Stop animation when user types
    searchInput.addEventListener('input', function() {
        if (!searchInput.value || searchInput.value.trim() === '') {
            if (placeholderContainer) {
                placeholderContainer.style.opacity = '1';
            }
            startAnimation();
        } else {
            if (placeholderContainer) {
                placeholderContainer.style.opacity = '0';
            }
            stopAnimation();
        }
    });
    
    // Initialize with first subcategory
    if (formattedSubcategories.length > 0) {
        placeholderText.textContent = formattedSubcategories[0];
        // Ensure initial state
        placeholderText.style.transform = 'rotateX(0deg)';
        placeholderText.style.opacity = '1';
        placeholderTextNext.style.transform = 'rotateX(90deg)';
        placeholderTextNext.style.opacity = '0';
    }
    
    // Start animation if we have multiple subcategories
    if (formattedSubcategories.length > 1) {
        // Small delay to ensure DOM is ready
        setTimeout(function() {
            startAnimation();
        }, 500);
    }
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

// Password Toggle - Simple UI only (no business logic)
// This just changes the display, password submission is handled by Django views
function initPasswordToggle() {
    document.querySelectorAll('.password-toggle').forEach(function(btn) {
        btn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Find the password input - check parent wrapper first
            var wrapper = this.closest('.password-input-wrapper');
            var input = null;
            
            if (wrapper) {
                input = wrapper.querySelector('input[type="password"], input[type="text"]');
            } else {
                // Fallback: find input in parent
                input = this.parentElement.querySelector('input[type="password"], input[type="text"]');
            }
            
            // If still not found, try by data-target attribute
            if (!input) {
                var targetId = this.getAttribute('data-target');
                if (targetId) {
                    input = document.getElementById(targetId);
                }
            }
            
            // Final fallback: try common IDs
            if (!input) {
                input = document.getElementById('password') || 
                        document.getElementById('id_new_password1') || 
                        document.getElementById('id_new_password2');
            }
            
            if (input) {
                var icon = this.querySelector('i');
                
                // Toggle password visibility
                if (input.type === 'password') {
                    input.type = 'text';
                    if (icon) { 
                        icon.classList.remove('fa-eye');
                        icon.classList.add('fa-eye-slash');
                    }
                } else {
                    input.type = 'password';
                    if (icon) { 
                        icon.classList.remove('fa-eye-slash');
                        icon.classList.add('fa-eye');
                    }
                }
            }
        };
    });
}

// Category Subcategory Panel Positioning
function initCategorySubcategoryPanels() {
    const categoryWrappers = document.querySelectorAll('.category-browser-item-wrapper');
    const nav = document.querySelector('.category-browser-nav');
    const sidebar = document.querySelector('.category-browser-sidebar');
    let currentlyVisiblePanel = null;
    let hideTimeout = null;
    
    if (!categoryWrappers.length) {
        console.log('No category wrappers found');
        return;
    }
    
    // Create a map of category ID to panel
    const panelMap = {};
    document.querySelectorAll('.category-subcategory-panel').forEach(panel => {
        const categoryId = panel.getAttribute('data-category-id');
        if (categoryId) {
            panelMap[categoryId] = panel;
        }
    });
    
    console.log('Found panels:', Object.keys(panelMap).length);
    
    categoryWrappers.forEach(wrapper => {
        const categoryId = wrapper.getAttribute('data-category-id');
        if (!categoryId) return;
        
        const panel = panelMap[categoryId];
        if (!panel) {
            console.log('No panel found for category:', categoryId);
            return;
        }
        
        const categoryItem = wrapper.querySelector('.category-browser-item');
        if (!categoryItem) return;
        
        // Function to position and show panel
        const showPanel = () => {
            // Clear any pending hide
            if (hideTimeout) {
                clearTimeout(hideTimeout);
                hideTimeout = null;
            }
            
            // Hide previously visible panel
            if (currentlyVisiblePanel && currentlyVisiblePanel !== panel) {
                currentlyVisiblePanel.classList.remove('visible');
            }
            
            // Get the position of the category item relative to the viewport
            const itemRect = categoryItem.getBoundingClientRect();
            const sidebarRect = sidebar ? sidebar.getBoundingClientRect() : null;
            
            // Calculate top position
            // Position panel to align with the category item
            const topPosition = itemRect.top;
            
            // Make sure panel doesn't go off screen
            const maxHeight = window.innerHeight - topPosition - 20; // 20px padding from bottom
            
            panel.style.top = topPosition + 'px';
            panel.style.maxHeight = Math.max(300, maxHeight) + 'px'; // At least 300px high
            
            // Show panel with class
            panel.classList.add('visible');
            
            currentlyVisiblePanel = panel;
            
            console.log('Showing panel:', categoryId, 'at top:', topPosition);
        };
        
        // Function to hide panel with delay
        const hidePanel = () => {
            if (hideTimeout) {
                clearTimeout(hideTimeout);
            }
            hideTimeout = setTimeout(() => {
                panel.classList.remove('visible');
                if (currentlyVisiblePanel === panel) {
                    currentlyVisiblePanel = null;
                }
                console.log('Hiding panel:', categoryId);
            }, 200); // Small delay to allow moving to panel
        };
        
        // Show on wrapper hover
        wrapper.addEventListener('mouseenter', showPanel);
        
        // Don't hide immediately when leaving wrapper
        wrapper.addEventListener('mouseleave', hidePanel);
        
        // Keep visible when hovering panel itself
        panel.addEventListener('mouseenter', () => {
            if (hideTimeout) {
                clearTimeout(hideTimeout);
                hideTimeout = null;
            }
            console.log('Mouse entered panel:', categoryId);
        });
        
        // Hide when leaving panel
        panel.addEventListener('mouseleave', hidePanel);
    });
    
    // Update position on scroll
    if (nav) {
        nav.addEventListener('scroll', () => {
            if (currentlyVisiblePanel) {
                // Find the wrapper that corresponds to the current panel
                categoryWrappers.forEach(wrapper => {
                    const categoryId = wrapper.getAttribute('data-category-id');
                    if (panelMap[categoryId] === currentlyVisiblePanel) {
                        const categoryItem = wrapper.querySelector('.category-browser-item');
                        if (categoryItem) {
                            const itemRect = categoryItem.getBoundingClientRect();
                            const sidebarRect = sidebar ? sidebar.getBoundingClientRect() : null;
                            const topPosition = itemRect.top;
                            const maxHeight = window.innerHeight - topPosition - 20;
                            
                            currentlyVisiblePanel.style.top = topPosition + 'px';
                            currentlyVisiblePanel.style.maxHeight = Math.max(300, maxHeight) + 'px';
                        }
                    }
                });
            }
        });
    }
    
    console.log('Category subcategory panels initialized');
}

// Fix navigation dropdown positioning for bottom categories
function initNavigationDropdownPositioning() {
    const categoryDropdowns = document.querySelectorAll('.nav-category-dropdown');
    
    categoryDropdowns.forEach(dropdown => {
        const subcategoryMenu = dropdown.querySelector('.nav-subcategory-dropdown');
        if (!subcategoryMenu) return;
        
        // Check position on hover
        dropdown.addEventListener('mouseenter', function() {
            const rect = dropdown.getBoundingClientRect();
            const menuHeight = subcategoryMenu.offsetHeight || 400; // Default max height
            const spaceBelow = window.innerHeight - rect.bottom;
            const spaceAbove = rect.top;
            
            // If not enough space below but enough space above, position upward
            if (spaceBelow < menuHeight && spaceAbove > menuHeight) {
                subcategoryMenu.style.top = 'auto';
                subcategoryMenu.style.bottom = 'calc(100% + 0.5rem)';
                subcategoryMenu.style.transform = 'translateY(10px)';
            } else {
                // Reset to default downward position
                subcategoryMenu.style.top = 'calc(100% + 0.5rem)';
                subcategoryMenu.style.bottom = 'auto';
                subcategoryMenu.style.transform = 'translateY(-10px)';
            }
            
            // Reset transform when menu becomes visible (after CSS transition)
            setTimeout(() => {
                if (window.getComputedStyle(subcategoryMenu).visibility === 'visible') {
                    subcategoryMenu.style.transform = 'translateY(0)';
                }
            }, 50);
        });
    });
    
    // Also check on window resize
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            categoryDropdowns.forEach(dropdown => {
                const subcategoryMenu = dropdown.querySelector('.nav-subcategory-dropdown');
                if (!subcategoryMenu) return;
                
                // Only adjust if currently visible
                if (window.getComputedStyle(subcategoryMenu).visibility === 'visible') {
                    const rect = dropdown.getBoundingClientRect();
                    const menuHeight = subcategoryMenu.offsetHeight || 400;
                    const spaceBelow = window.innerHeight - rect.bottom;
                    const spaceAbove = rect.top;
                    
                    if (spaceBelow < menuHeight && spaceAbove > menuHeight) {
                        subcategoryMenu.style.top = 'auto';
                        subcategoryMenu.style.bottom = 'calc(100% + 0.5rem)';
                    } else {
                        subcategoryMenu.style.top = 'calc(100% + 0.5rem)';
                        subcategoryMenu.style.bottom = 'auto';
                    }
                }
            });
        }, 100);
    });
}

// Restrict date input fields to maximum digits
function initDateInputRestrictions() {
    // Restrict day input to 2 digits
    const dayInput = document.getElementById('birth-day');
    if (dayInput) {
        dayInput.addEventListener('input', function(e) {
            let value = this.value;
            // Remove any non-digit characters
            value = value.replace(/\D/g, '');
            // Limit to 2 digits
            if (value.length > 2) {
                value = value.slice(0, 2);
            }
            this.value = value;
        });
        
        // Also prevent pasting more than 2 digits
        dayInput.addEventListener('paste', function(e) {
            e.preventDefault();
            const paste = (e.clipboardData || window.clipboardData).getData('text');
            const digits = paste.replace(/\D/g, '').slice(0, 2);
            this.value = digits;
        });
    }
    
    // Restrict year input to 4 digits
    const yearInput = document.getElementById('birth-year');
    if (yearInput) {
        yearInput.addEventListener('input', function(e) {
            let value = this.value;
            // Remove any non-digit characters
            value = value.replace(/\D/g, '');
            // Limit to 4 digits
            if (value.length > 4) {
                value = value.slice(0, 4);
            }
            this.value = value;
        });
        
        // Also prevent pasting more than 4 digits
        yearInput.addEventListener('paste', function(e) {
            e.preventDefault();
            const paste = (e.clipboardData || window.clipboardData).getData('text');
            const digits = paste.replace(/\D/g, '').slice(0, 4);
            this.value = digits;
        });
    }
}
