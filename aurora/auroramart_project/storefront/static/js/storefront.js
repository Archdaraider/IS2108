// AuroraMart Storefront JavaScript
// Minimal JavaScript - all logic should be in views.py

document.addEventListener('DOMContentLoaded', function() {
    initCartFunctionality();
    initWishlistFunctionality();
    initProductActions();
    initFormEnhancements();
    initCarousel();
    initImageGallery();
    initMessages();
    initCartCount();
    initShoppingCartPage();
});

// Cart Functionality
function initCartFunctionality() {
    // Prevent product card link navigation when clicking buttons
    document.querySelectorAll('.product-cart-actions, .product-actions').forEach(container => {
        container.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
    
    // Add to cart buttons
    document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const productId = this.getAttribute('data-product-id');
            addToCart(productId, 1);
        });
    });
    
    // Quantity picker buttons
    document.querySelectorAll('.quantity-picker .minus, .quantity-picker .plus, .quantity-picker-inline .minus, .quantity-picker-inline .plus').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const picker = this.closest('.quantity-picker, .quantity-picker-inline');
            const productId = picker.getAttribute('data-product-id');
            const cartItemId = picker.getAttribute('data-cart-item-id');
            const quantityValue = picker.querySelector('.quantity-value');
            const currentQuantity = parseInt(quantityValue.textContent);
            
            if (this.classList.contains('minus')) {
                updateQuantity(productId, Math.max(0, currentQuantity - 1), cartItemId);
            } else {
                updateQuantity(productId, currentQuantity + 1, cartItemId);
            }
        });
    });
    
    // Wishlist button
    document.querySelectorAll('.wishlist-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
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
            
            // Replace "Add to cart" button with quantity picker
            const btn = document.querySelector(`.add-to-cart-btn[data-product-id="${productId}"]`);
            if (btn) {
                const cartActionsContainer = btn.closest('.product-cart-actions');
                const isInline = btn.closest('.product-actions') !== null;
                const quantityPicker = createQuantityPicker(productId, data.quantity, data.cart_item_id, isInline);
                btn.replaceWith(quantityPicker);
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

function createQuantityPicker(productId, quantity = 1, cartItemId = null, isInline = false) {
    const container = document.createElement('div');
    container.className = isInline ? 'quantity-picker-inline' : 'quantity-picker';
    container.setAttribute('data-product-id', productId);
    if (cartItemId) {
        container.setAttribute('data-cart-item-id', cartItemId);
    }
    container.innerHTML = `
        <button class="quantity-btn minus" type="button">-</button>
        <span class="quantity-value">${quantity}</span>
        <button class="quantity-btn plus" type="button">+</button>
    `;
    
    // Add event listeners
    const minusBtn = container.querySelector('.minus');
    const plusBtn = container.querySelector('.plus');
    const quantityValue = container.querySelector('.quantity-value');
    
    minusBtn.addEventListener('click', () => updateQuantity(productId, parseInt(quantityValue.textContent) - 1, cartItemId));
    plusBtn.addEventListener('click', () => updateQuantity(productId, parseInt(quantityValue.textContent) + 1, cartItemId));
    
    return container;
}

function updateQuantity(productId, newQuantity, cartItemId = null) {
    fetch('/api/update-cart-item/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            product_id: productId,
            item_id: cartItemId,
            quantity: newQuantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.removed) {
                // Item removed, replace quantity picker with "Add to cart" button
                const picker = document.querySelector(`.quantity-picker[data-product-id="${productId}"], .quantity-picker-inline[data-product-id="${productId}"]`);
                if (picker) {
                    const btn = document.createElement('button');
                    btn.className = 'btn btn-primary add-to-cart-btn';
                    btn.setAttribute('data-product-id', productId);
                    btn.type = 'button';
                    btn.textContent = 'Add to cart';
                    btn.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        addToCart(productId, 1);
                    });
                    picker.replaceWith(btn);
                }
            } else {
                // Update quantity display
                const quantityValue = document.querySelector(`.quantity-picker[data-product-id="${productId}"] .quantity-value, .quantity-picker-inline[data-product-id="${productId}"] .quantity-value`);
                if (quantityValue) {
                    quantityValue.textContent = data.quantity;
                }
            }
            updateCartCount(data.cart_total);
        }
    })
    .catch(error => {
        console.error('Error:', error);
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
    const btn = document.querySelector(`.wishlist-btn[data-product-id="${productId}"]`);
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

// Product Actions - Make entire product card clickable
function initProductActions() {
    // Make product cards clickable (clicking anywhere except buttons navigates to product detail)
    document.querySelectorAll('.product-card[data-product-url]').forEach(card => {
        card.style.cursor = 'pointer';
        card.addEventListener('click', function(e) {
            // Only navigate if clicking on the card itself, not on buttons or links
            if (!e.target.closest('.product-actions, .product-cart-actions, .add-to-cart-btn, .quantity-picker, .wishlist-btn, a')) {
                const url = this.getAttribute('data-product-url');
                if (url) {
                    window.location.href = url;
                }
            }
        });
    });
}

// Form Enhancements
function initFormEnhancements() {
    const newsletterForm = document.getElementById('newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = this.querySelector('.newsletter-input').value;
            subscribeToNewsletter(email);
        });
    }
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
            
            if (nextBtn) nextBtn.addEventListener('click', nextSlide);
            if (prevBtn) prevBtn.addEventListener('click', prevSlide);
            
            dots.forEach((dot, index) => {
                dot.addEventListener('click', () => {
                    currentSlide = index;
                    showSlide(currentSlide);
                });
            });
            
            if (carousel.classList.contains('hero-carousel')) {
                setInterval(nextSlide, 5000);
            }
            
            showSlide(0);
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

function showMessage(text, type = 'info') {
    const messagesContainer = document.querySelector('.messages-container') || createMessagesContainer();
    
    const message = document.createElement('div');
    message.className = `message message-${type}`;
    message.innerHTML = `
        <span>${text}</span>
        <button class="message-close">&times;</button>
    `;
    
    messagesContainer.appendChild(message);
    
    setTimeout(() => {
        message.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => {
            message.remove();
        }, 300);
    }, 5000);
    
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
    if (window.csrfToken) {
        return window.csrfToken;
    }
    
    let token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (token) {
        return token.value;
    }
    
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    
    console.warn('CSRF token not found');
    return '';
}

function isUserLoggedIn() {
    return document.querySelector('.user-dropdown') !== null;
}

// Global function to update cart count - NO RECURSION
function updateCartCount(count) {
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
        const numCount = typeof count === 'number' ? count : parseInt(count) || 0;
        cartCountElement.textContent = numCount;
        if (numCount > 0) {
            cartCountElement.style.display = 'flex';
            cartCountElement.style.visibility = 'visible';
        } else {
            cartCountElement.style.display = 'none';
            cartCountElement.style.visibility = 'hidden';
        }
    }
}

// Initialize cart count on page load
function initCartCount() {
    fetch('/api/get-cart-count/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount(data.cart_total || 0);
        } else {
            updateCartCount(0);
        }
    })
    .catch(error => {
        console.error('Error fetching cart count:', error);
        updateCartCount(0);
    });
}

// Shopping Cart Page Functionality
function initShoppingCartPage() {
    // Prevent cart item link navigation when clicking buttons
    document.querySelectorAll('.item-actions, .item-quantity').forEach(container => {
        container.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
    
    // Quantity controls in cart page
    document.querySelectorAll('.quantity-controls .quantity-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const itemId = this.getAttribute('data-item-id');
            const quantityControls = this.closest('.quantity-controls');
            const quantityValue = quantityControls.querySelector('.quantity-value');
            const currentQuantity = parseInt(quantityValue.textContent);
            
            let newQuantity = currentQuantity;
            if (this.classList.contains('minus')) {
                newQuantity = Math.max(0, currentQuantity - 1);
            } else {
                newQuantity = currentQuantity + 1;
            }
            
            // Update via AJAX
            fetch('/api/update-cart-item/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    item_id: itemId,
                    quantity: newQuantity
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.removed) {
                        // Item removed, remove from DOM
                        const cartItem = document.querySelector(`.cart-item[data-item-id="${itemId}"]`);
                        if (cartItem) {
                            cartItem.remove();
                        }
                        // Reload page to update totals
                        location.reload();
                    } else {
                        // Update quantity display
                        quantityValue.textContent = data.quantity;
                        updateCartTotals(data.cart_total, data.cart_price);
                    }
                    updateCartCount(data.cart_total);
                }
            })
            .catch(error => {
                console.error('Error updating cart item:', error);
                showMessage('Error updating quantity', 'error');
            });
        });
    });
    
    // Remove item button
    document.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const itemId = this.getAttribute('data-item-id');
            const cartItem = this.closest('.cart-item');
            
            if (confirm('Are you sure you want to remove this item from your cart?')) {
                fetch('/api/remove-from-cart/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({
                        item_id: itemId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        cartItem.remove();
                        updateCartTotals(data.cart_total, data.cart_price);
                        updateCartCount(data.cart_total);
                        showMessage(data.message, 'success');
                        
                        // Reload if cart is empty
                        if (data.cart_total === 0) {
                            setTimeout(() => location.reload(), 1000);
                        }
                    } else {
                        showMessage(data.message || 'Error removing item', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error removing item:', error);
                    showMessage('Error removing item from cart', 'error');
                });
            }
        });
    });
    
    // Select all checkbox
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            document.querySelectorAll('.item-select').forEach(checkbox => {
                checkbox.checked = isChecked;
            });
        });
    }
    
    // Delete selected items
    const deleteSelectedBtn = document.getElementById('delete-selected');
    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const selectedItems = document.querySelectorAll('.item-select:checked');
            if (selectedItems.length === 0) {
                showMessage('Please select items to delete', 'warning');
                return;
            }
            
            if (confirm(`Are you sure you want to delete ${selectedItems.length} selected item(s)?`)) {
                const promises = Array.from(selectedItems).map(checkbox => {
                    const cartItem = checkbox.closest('.cart-item');
                    const itemId = cartItem.getAttribute('data-item-id');
                    return fetch('/api/remove-from-cart/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCSRFToken()
                        },
                        body: JSON.stringify({
                            item_id: itemId
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            cartItem.remove();
                            return data;
                        }
                    });
                });
                
                Promise.all(promises).then(() => {
                    // Reload page to update totals
                    location.reload();
                });
            }
        });
    }
}

// Update cart totals on shopping cart page
function updateCartTotals(totalItems, totalPrice) {
    // Update header cart count
    updateCartCount(totalItems);
    
    // Update cart page totals
    const subtotalElement = document.querySelector('.subtotal-amount');
    const totalElement = document.querySelector('.total-amount');
    const shippingFee = 4.00;
    
    if (subtotalElement) {
        subtotalElement.textContent = `$${totalPrice.toFixed(2)}`;
    }
    if (totalElement) {
        totalElement.textContent = `$${(totalPrice + shippingFee).toFixed(2)}`;
    }
    
    // Update item count in summary
    const itemCountElement = document.querySelector('.summary-line span:first-child');
    if (itemCountElement) {
        itemCountElement.textContent = `Subtotal (${totalItems} items)`;
    }
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
