/**
 * AuroraMart Admin Panel JavaScript
 * Handles interactive features and dynamic functionality
 */

// === SIDEBAR TOGGLE ===
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const floatingToggle = document.getElementById('floatingToggle');
    const mainContent = document.querySelector('.main-content');
    
    if (!sidebar || !sidebarToggle || !mainContent) {
        console.warn('Sidebar elements not found');
        return;
    }
    
    /**
     * Apply sidebar visibility state
     * @param {boolean} shouldHide - True to hide sidebar, false to show
     */
    function applySidebarState(shouldHide) {
        if (shouldHide) {
            // Hide sidebar
            sidebar.classList.add('hidden');
            sidebar.classList.remove('show');
            mainContent.style.marginLeft = '0';
            mainContent.style.width = '100%';
            if (floatingToggle) {
                floatingToggle.style.display = 'flex';
            }
        } else {
            // Show sidebar
            sidebar.classList.remove('hidden');
            sidebar.classList.add('show');
            mainContent.style.marginLeft = 'var(--sidebar-width)';
            mainContent.style.width = 'calc(100% - var(--sidebar-width))';
            if (floatingToggle) {
                floatingToggle.style.display = 'none';
            }
        }
        
        // Save preference
        localStorage.setItem('sidebarHidden', shouldHide.toString());
        console.log('Sidebar state changed:', shouldHide ? 'hidden' : 'visible');
    }
    
    /**
     * Toggle sidebar visibility
     */
    function toggleSidebar(event) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        
        const isCurrentlyHidden = sidebar.classList.contains('hidden');
        applySidebarState(!isCurrentlyHidden);
    }
    
    // Main sidebar toggle button (hamburger icon in sidebar header)
    sidebarToggle.addEventListener('click', toggleSidebar);
    
    // Floating toggle button (appears when sidebar is hidden)
    if (floatingToggle) {
        floatingToggle.addEventListener('click', toggleSidebar);
    }
    
    // Restore saved sidebar state on page load
    const savedState = localStorage.getItem('sidebarHidden');
    const shouldStartHidden = savedState === 'true';
    applySidebarState(shouldStartHidden);
    
    // Close sidebar when clicking outside on mobile/tablet
    document.addEventListener('click', function(e) {
        // Only apply on smaller screens
        if (window.innerWidth > 1024) {
            return;
        }
        
        // Check if sidebar is currently visible
        if (sidebar.classList.contains('hidden')) {
            return;
        }
        
        // Check if click was inside sidebar or on toggle buttons
        const isClickInsideSidebar = sidebar.contains(e.target);
        const isClickOnToggle = sidebarToggle.contains(e.target) || 
                                (floatingToggle && floatingToggle.contains(e.target));
        
        // If click was outside sidebar and not on toggle, hide sidebar
        if (!isClickInsideSidebar && !isClickOnToggle) {
            applySidebarState(true);
        }
    });
    
    console.log('Sidebar toggle initialized');
});

// === AUTO-HIDE ALERTS ===
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.3s, transform 0.3s';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

// === CONFIRMATION DIALOGS ===
function confirmDelete(itemType, itemName) {
    return confirm(`Are you sure you want to delete this ${itemType}${itemName ? ': ' + itemName : ''}?`);
}

// Attach to delete buttons
document.addEventListener('DOMContentLoaded', function() {
    const deleteForms = document.querySelectorAll('form[action*="delete"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const itemType = this.dataset.itemType || 'item';
            const itemName = this.dataset.itemName || '';
            if (!confirmDelete(itemType, itemName)) {
                e.preventDefault();
            }
        });
    });
});

// === FORM VALIDATION ===
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error-field');
            isValid = false;
        } else {
            field.classList.remove('error-field');
        }
    });
    
    return isValid;
}

// === TABLE SORTING ===
function sortTable(columnIndex, tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        return aValue.localeCompare(bValue, undefined, { numeric: true });
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// === SEARCH/FILTER FUNCTIONALITY ===
function filterTable(searchValue, tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = tbody.querySelectorAll('tr');
    
    searchValue = searchValue.toLowerCase();
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchValue) ? '' : 'none';
    });
}

// === MODAL HANDLING ===
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Close modal on outside click
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal(e.target.id);
    }
});

// === AJAX HELPERS ===
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// === TOGGLE SWITCH HANDLER ===
function handleToggle(checkbox, url, itemId) {
    const isChecked = checkbox.checked;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ is_active: isChecked })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message || 'Updated successfully', 'success');
        } else {
            checkbox.checked = !isChecked; // Revert on error
            showNotification(data.error || 'Update failed', 'error');
        }
    })
    .catch(error => {
        checkbox.checked = !isChecked; // Revert on error
        showNotification('An error occurred', 'error');
        console.error('Error:', error);
    });
}

// === NOTIFICATION SYSTEM ===
function showNotification(message, type = 'info') {
    const container = document.querySelector('.messages-container') || createMessageContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <i class="fas fa-${getIconForType(type)}"></i>
        <span>${message}</span>
        <button class="alert-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(alert);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        alert.style.transition = 'opacity 0.3s, transform 0.3s';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}

function createMessageContainer() {
    const container = document.createElement('div');
    container.className = 'messages-container';
    const contentWrapper = document.querySelector('.content-wrapper');
    contentWrapper.insertBefore(container, contentWrapper.firstChild);
    return container;
}

function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// === BULK ACTIONS ===
function toggleSelectAll(checkbox, tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const checkboxes = table.querySelectorAll('tbody input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = checkbox.checked);
    updateBulkActionButtons();
}

function updateBulkActionButtons() {
    const checkedBoxes = document.querySelectorAll('tbody input[type="checkbox"]:checked');
    const bulkActionBtn = document.getElementById('bulkActionBtn');
    
    if (bulkActionBtn) {
        bulkActionBtn.disabled = checkedBoxes.length === 0;
        bulkActionBtn.textContent = `Action (${checkedBoxes.length} selected)`;
    }
}

function getSelectedIds(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return [];
    
    const checkboxes = table.querySelectorAll('tbody input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// === FORM HANDLING ===
// Dynamic formset handling for OrderItems
document.addEventListener('DOMContentLoaded', function() {
    const formsets = document.querySelectorAll('[data-formset]');
    
    formsets.forEach(formset => {
        const addButton = formset.querySelector('[data-add-form]');
        if (addButton) {
            addButton.addEventListener('click', function(e) {
                e.preventDefault();
                addFormsetRow(formset);
            });
        }
    });
});

function addFormsetRow(formset) {
    const template = formset.querySelector('[data-form-template]');
    if (!template) return;
    
    const totalForms = formset.querySelector('[name$="-TOTAL_FORMS"]');
    const newFormIndex = parseInt(totalForms.value);
    
    const newForm = template.cloneNode(true);
    newForm.innerHTML = newForm.innerHTML.replace(/__prefix__/g, newFormIndex);
    newForm.removeAttribute('data-form-template');
    newForm.style.display = '';
    
    formset.querySelector('[data-forms-container]').appendChild(newForm);
    totalForms.value = newFormIndex + 1;
    
    // Add delete button handler
    const deleteBtn = newForm.querySelector('[data-delete-form]');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function(e) {
            e.preventDefault();
            removeFormsetRow(newForm, formset);
        });
    }
}

function removeFormsetRow(row, formset) {
    row.remove();
    updateFormsetIndexes(formset);
}

function updateFormsetIndexes(formset) {
    const forms = formset.querySelectorAll('[data-form]:not([data-form-template])');
    const totalForms = formset.querySelector('[name$="-TOTAL_FORMS"]');
    
    forms.forEach((form, index) => {
        form.querySelectorAll('input, select, textarea').forEach(field => {
            const name = field.getAttribute('name');
            if (name) {
                field.setAttribute('name', name.replace(/\d+/, index));
            }
            const id = field.getAttribute('id');
            if (id) {
                field.setAttribute('id', id.replace(/\d+/, index));
            }
        });
    });
    
    totalForms.value = forms.length;
}

// === IMAGE PREVIEW ===
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    if (!preview || !input.files || !input.files[0]) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        preview.src = e.target.result;
        preview.style.display = 'block';
    };
    reader.readAsDataURL(input.files[0]);
}

// === NUMBER FORMATTING ===
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-SG', {
        style: 'currency',
        currency: 'SGD'
    }).format(amount);
}

function formatNumber(number) {
    return new Intl.NumberFormat('en-SG').format(number);
}

// === DATE FORMATTING ===
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-SG', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// === EXPORT FUNCTIONALITY ===
function exportTableToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => {
            let text = col.textContent.trim();
            // Escape quotes and wrap in quotes if contains comma
            if (text.includes(',') || text.includes('"')) {
                text = '"' + text.replace(/"/g, '""') + '"';
            }
            return text;
        });
        csv.push(rowData.join(','));
    });
    
    // Create download link
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// === PRINT FUNCTIONALITY ===
function printPage() {
    window.print();
}

// === DEBOUNCE HELPER ===
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// === LIVE SEARCH ===
const liveSearch = debounce(function(input, resultsId) {
    const searchTerm = input.value.toLowerCase();
    const results = document.getElementById(resultsId);
    
    if (!results) return;
    
    const items = results.querySelectorAll('[data-searchable]');
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}, 300);

// === CLIPBOARD COPY ===
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard', 'success');
    }).catch(err => {
        showNotification('Failed to copy', 'error');
        console.error('Copy failed:', err);
    });
}

// === LOADING STATE ===
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="spinner"></div>';
    }
}

function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '';
    }
}

// === KEYBOARD SHORTCUTS ===
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search focus
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[type="search"], input[name="search"]');
        if (searchInput) searchInput.focus();
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            modal.style.display = 'none';
        });
    }
});

// === UTILITY FUNCTIONS ===
// Add active class to current nav item
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.closest('.nav-item').classList.add('active');
        }
    });
});

// === CONSOLE LOG (Development Helper) ===
console.log('%c🛒 AuroraMart Admin Panel Loaded', 'color: #000; font-size: 14px; font-weight: bold;');
console.log('%cVersion 1.0.0', 'color: #666; font-size: 12px;');

