/**
 * Barcode scanning and input handling functionality
 * Hardware Inventory Tracker
 */

class BarcodeHandler {
    constructor() {
        this.isScanning = false;
        this.scanner = null;
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
    }
    
    setupEventListeners() {
        // Handle barcode input auto-formatting
        document.addEventListener('DOMContentLoaded', () => {
            const barcodeInputs = document.querySelectorAll('input[name="barcode"]');
            barcodeInputs.forEach(input => {
                this.setupBarcodeInput(input);
            });
        });
    }
    
    setupBarcodeInput(input) {
        // Auto-uppercase and format barcode
        input.addEventListener('input', (e) => {
            let value = e.target.value.toUpperCase().replace(/[^A-Z0-9\-_]/g, '');
            e.target.value = value;
        });
        
        // Handle barcode scanning (simulated rapid input)
        let rapidInputTimer = null;
        let rapidInputBuffer = '';
        
        input.addEventListener('keydown', (e) => {
            // Detect rapid input (barcode scanner characteristic)
            if (rapidInputTimer) {
                clearTimeout(rapidInputTimer);
            }
            
            rapidInputBuffer += e.key;
            
            rapidInputTimer = setTimeout(() => {
                if (rapidInputBuffer.length > 5 && e.key === 'Enter') {
                    // Likely barcode scanner input
                    this.handleScannedBarcode(input, rapidInputBuffer.slice(0, -5)); // Remove 'Enter'
                }
                rapidInputBuffer = '';
            }, 100);
        });
    }
    
    handleScannedBarcode(input, barcode) {
        input.value = barcode;
        input.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Visual feedback for successful scan
        input.style.backgroundColor = '#d4edda';
        setTimeout(() => {
            input.style.backgroundColor = '';
        }, 1000);
        
        // Auto-lookup if on pull event page
        if (window.location.pathname.includes('log_pull')) {
            this.lookupBarcodeInfo(barcode);
        }
    }
    
    async lookupBarcodeInfo(barcode) {
        try {
            const response = await fetch(`/get_box_info/${encodeURIComponent(barcode)}`);
            const data = await response.json();
            
            const boxInfoDiv = document.getElementById('boxInfo');
            const boxInfoContent = document.getElementById('boxInfoContent');
            
            if (data.found) {
                boxInfoContent.innerHTML = `
                    <strong>Box ID:</strong> ${data.box_id}<br>
                    <strong>Hardware Type:</strong> ${data.hardware_type}<br>
                    <strong>Lot Number:</strong> ${data.lot_number}<br>
                    <strong>Available Quantity:</strong> ${data.remaining_quantity}
                `;
                boxInfoDiv.style.display = 'block';
                
                // Update quantity input max value
                const quantityInput = document.getElementById('quantity_pulled');
                if (quantityInput) {
                    quantityInput.max = data.remaining_quantity;
                    quantityInput.placeholder = `Max: ${data.remaining_quantity}`;
                }
            } else {
                boxInfoContent.innerHTML = `
                    <span class="text-danger">
                        <i class="fas fa-exclamation-triangle me-1"></i>
                        Barcode not found in inventory
                    </span>
                `;
                boxInfoDiv.style.display = 'block';
            }
        } catch (error) {
            console.error('Error looking up barcode:', error);
        }
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + B to focus barcode input
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                const barcodeInput = document.querySelector('input[name="barcode"]');
                if (barcodeInput) {
                    barcodeInput.focus();
                    barcodeInput.select();
                }
            }
        });
    }
    
    // Camera scanning placeholder (would integrate with html5-qrcode or similar)
    async startCameraScanning() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert('Camera access not supported on this device/browser');
            return;
        }
        
        try {
            // This would integrate with html5-qrcode library
            alert('Camera barcode scanning would be implemented here using html5-qrcode library. For now, please enter barcodes manually.');
        } catch (error) {
            console.error('Camera access error:', error);
            alert('Unable to access camera. Please enter barcode manually.');
        }
    }
    
    // Utility function to validate barcode format
    isValidBarcode(barcode) {
        // Basic barcode validation - adjust based on your barcode format
        const barcodePattern = /^[A-Z0-9\-_]{4,50}$/;
        return barcodePattern.test(barcode);
    }
    
    // Auto-complete functionality for frequently used barcodes
    setupBarcodeAutocomplete(input, suggestions = []) {
        const datalistId = 'barcode-suggestions';
        let datalist = document.getElementById(datalistId);
        
        if (!datalist) {
            datalist = document.createElement('datalist');
            datalist.id = datalistId;
            document.body.appendChild(datalist);
        }
        
        // Update suggestions
        datalist.innerHTML = '';
        suggestions.forEach(suggestion => {
            const option = document.createElement('option');
            option.value = suggestion;
            datalist.appendChild(option);
        });
        
        input.setAttribute('list', datalistId);
    }
}

// Form validation utilities
class FormValidator {
    static validateQuantity(input, maxValue = null) {
        const value = parseInt(input.value);
        const feedback = input.parentNode.querySelector('.invalid-feedback') || 
                        this.createFeedbackElement(input);
        
        if (isNaN(value) || value <= 0) {
            input.classList.add('is-invalid');
            feedback.textContent = 'Quantity must be a positive number';
            return false;
        }
        
        if (maxValue && value > maxValue) {
            input.classList.add('is-invalid');
            feedback.textContent = `Quantity cannot exceed ${maxValue}`;
            return false;
        }
        
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        return true;
    }
    
    static validateBarcode(input) {
        const value = input.value.trim();
        const feedback = input.parentNode.querySelector('.invalid-feedback') || 
                        this.createFeedbackElement(input);
        
        if (!value) {
            input.classList.add('is-invalid');
            feedback.textContent = 'Barcode is required';
            return false;
        }
        
        if (!/^[A-Z0-9\-_]{4,50}$/.test(value)) {
            input.classList.add('is-invalid');
            feedback.textContent = 'Invalid barcode format';
            return false;
        }
        
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        return true;
    }
    
    static createFeedbackElement(input) {
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        input.parentNode.appendChild(feedback);
        return feedback;
    }
}

// Initialize barcode handler when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.barcodeHandler = new BarcodeHandler();
    
    // Setup form validation
    const quantityInputs = document.querySelectorAll('input[name="quantity_pulled"], input[name="initial_quantity"]');
    quantityInputs.forEach(input => {
        input.addEventListener('blur', () => FormValidator.validateQuantity(input));
    });
    
    const barcodeInputs = document.querySelectorAll('input[name="barcode"]');
    barcodeInputs.forEach(input => {
        input.addEventListener('blur', () => FormValidator.validateBarcode(input));
    });
});

// Export for use in other scripts
window.BarcodeHandler = BarcodeHandler;
window.FormValidator = FormValidator;
