
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file');
    const uploadArea = document.getElementById('uploadArea');
    const selectedFile = document.getElementById('selectedFile');
    const fileName = document.getElementById('fileName');
    const uploadForm = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const loading = document.getElementById('loading');
    
    // Click to upload
    uploadArea.addEventListener('click', function(e) {
        if (e.target !== fileInput) {
            fileInput.click();
        }
    });
    
    // File selected
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            fileName.textContent = this.files[0].name;
            selectedFile.classList.add('show');
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].name.endsWith('.csv')) {
            fileInput.files = files;
            fileName.textContent = files[0].name;
            selectedFile.classList.add('show');
        }
    });
    
    // Form submission with AJAX
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';
        loading.classList.add('show');
        
        // Create FormData from form
        const formData = new FormData(uploadForm);
        
        // Send AJAX request
        fetch('/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Trigger download
                window.location.href = '/download/' + data.download_id;
                
                // Reset form after short delay
                setTimeout(() => {
                    resetForm();
                    showMessage('Analysis complete! Your PDF has been downloaded.', 'success');
                }, 2000);
            } else {
                resetForm();
                showMessage('Error: ' + data.error, 'error');
            }
        })
        .catch(error => {
            resetForm();
            showMessage('Network error: ' + error.message, 'error');
        });
    });
    
    function resetForm() {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Analyze Data';
        loading.classList.remove('show');
    }
    
    function showMessage(message, type) {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());
        
        // Create new alert
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        
        // Insert at top of container
        const container = document.querySelector('.container');
        const subtitle = document.querySelector('.subtitle');
        subtitle.parentNode.insertBefore(alert, subtitle.nextSibling);
        
        // Auto-remove success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                alert.remove();
            }, 5000);
        }
    }
});

