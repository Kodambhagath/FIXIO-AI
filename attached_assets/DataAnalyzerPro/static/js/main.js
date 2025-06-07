// Handle sample prompts for AI Excel Editor
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('sample-prompt')) {
        const promptText = e.target.getAttribute('data-prompt');
        const commandInput = document.getElementById('command');
        if (commandInput) {
            commandInput.value = promptText;
        }
    }
});

// File upload handling
document.addEventListener('DOMContentLoaded', function() {
    // File upload handling
    const fileInputs = document.querySelectorAll('.file-input');
    fileInputs.forEach(input => {
        // File upload area
        const uploadArea = input.closest('.file-upload');
        if (uploadArea) {
            uploadArea.addEventListener('click', function(e) {
                if (e.target === this || e.target.classList.contains('upload-text') || e.target.classList.contains('file-upload-icon')) {
                    input.click();
                }
            });

            // Drag and drop functionality
            uploadArea.addEventListener('dragover', function(e) {
                e.preventDefault();
                this.classList.add('highlight');
            });

            uploadArea.addEventListener('dragleave', function(e) {
                e.preventDefault();
                this.classList.remove('highlight');
            });

            uploadArea.addEventListener('drop', function(e) {
                e.preventDefault();
                this.classList.remove('highlight');
                input.files = e.dataTransfer.files;
                handleFileSelection(input);
            });
        }

        // Handle file selection
        input.addEventListener('change', function() {
            handleFileSelection(this);
        });
    });

    function handleFileSelection(input) {
        const fileListContainer = input.closest('.file-upload-container').querySelector('.file-list');
        const maxFiles = input.getAttribute('data-max-files') || 1;

        if (fileListContainer) {
            fileListContainer.innerHTML = '';

            // Check for file count limit on multiple file inputs
            if (input.multiple && maxFiles && input.files.length > maxFiles) {
                showAlert(`You can only select up to ${maxFiles} files.`, 'danger');
                input.value = '';
                return;
            }

            // Display selected files
            Array.from(input.files).forEach(file => {
                // Validate file type if needed
                const acceptAttr = input.getAttribute('accept');
                if (acceptAttr) {
                    const acceptedTypes = acceptAttr.split(',').map(type => type.trim());
                    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
                    const fileMime = file.type;

                    if (!acceptedTypes.some(type => type === fileExt || type === fileMime || (type.includes('/*') && fileMime.startsWith(type.replace('/*', '/'))))) {
                        showAlert(`File type ${fileExt} is not supported.`, 'danger');
                        input.value = '';
                        return;
                    }
                }

                // Create file item element
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.innerHTML = `
                    <div class="file-name">${file.name}</div>
                    <span class="remove-file"><i class="fas fa-times"></i></span>
                `;

                // Add remove functionality
                const removeBtn = fileItem.querySelector('.remove-file');
                removeBtn.addEventListener('click', function() {
                    fileItem.remove();

                    // Clear the file input if all files are removed
                    if (fileListContainer.children.length === 0) {
                        input.value = '';
                    }
                });

                fileListContainer.appendChild(fileItem);
            });
        }
    }

    // Form submission with loading overlay
    const processingForms = document.querySelectorAll('.processing-form');
    processingForms.forEach(form => {
        form.addEventListener('submit', function() {
            // Validate if files are selected
            const fileInputs = this.querySelectorAll('input[type="file"]');
            let filesSelected = false;

            fileInputs.forEach(input => {
                if (input.files.length > 0) {
                    filesSelected = true;
                }
            });

            if (!filesSelected) {
                showAlert('Please select files to process.', 'danger');
                return false;
            }

            // Show loading overlay
            const loadingOverlay = document.createElement('div');
            loadingOverlay.className = 'loading-overlay';
            loadingOverlay.innerHTML = `
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="loading-text">Processing your files...</div>
            `;
            document.body.appendChild(loadingOverlay);

            return true;
        });
    });

    // Alert handling
    function showAlert(message, type = 'success') {
        const alertContainer = document.querySelector('.alert-container');
        if (alertContainer) {
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} alert-dismissible fade show`;
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;

            alertContainer.appendChild(alert);

            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }, 5000);
        }
    }

    // Size converter tool
    const sizeConverterForm = document.getElementById('size-converter-form');
    if (sizeConverterForm) {
        sizeConverterForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const inputValue = parseFloat(document.getElementById('input-value').value);
            const inputUnit = document.getElementById('input-unit').value;
            const outputUnit = document.getElementById('output-unit').value;
            const resultElement = document.getElementById('conversion-result');

            if (isNaN(inputValue) || inputValue <= 0) {
                showAlert('Please enter a valid positive number.', 'danger');
                return;
            }

            let result;

            // Convert input to bytes
            let bytes = inputValue;
            if (inputUnit === 'kb') bytes *= 1024;
            else if (inputUnit === 'mb') bytes *= 1024 * 1024;
            else if (inputUnit === 'gb') bytes *= 1024 * 1024 * 1024;
            else if (inputUnit === 'tb') bytes *= 1024 * 1024 * 1024 * 1024;

            // Convert bytes to output unit
            if (outputUnit === 'b') result = bytes;
            else if (outputUnit === 'kb') result = bytes / 1024;
            else if (outputUnit === 'mb') result = bytes / (1024 * 1024);
            else if (outputUnit === 'gb') result = bytes / (1024 * 1024 * 1024);
            else if (outputUnit === 'tb') result = bytes / (1024 * 1024 * 1024 * 1024);

            resultElement.textContent = `${inputValue} ${inputUnit.toUpperCase()} = ${result.toLocaleString('en-US', { maximumFractionDigits: 6 })} ${outputUnit.toUpperCase()}`;
            resultElement.classList.remove('d-none');
        });
    }

    // AI Assistant functionality
    const assistantForm = document.getElementById('assistant-form');
    if (assistantForm) {
        assistantForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const query = document.getElementById('assistant-query').value.trim();
            if (!query) {
                showAlert('Please enter a question.', 'danger');
                return;
            }

            // Send the query to the backend
            fetch('/assistant/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `query=${encodeURIComponent(query)}`
            })
            .then(response => response.json())
            .then(data => {
                const responseContainer = document.getElementById('assistant-response');
                responseContainer.innerHTML = `
                    <div class="card bg-dark text-light mb-3">
                        <div class="card-header">Your question: ${query}</div>
                        <div class="card-body">
                            <p class="card-text">${data.response}</p>
                        </div>
                    </div>
                `;
                responseContainer.classList.remove('d-none');
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Failed to process your request. Please try again.', 'danger');
            });
        });
    }
});