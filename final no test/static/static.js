document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - initializing event listeners');
    
    // FIX FOR LABEL CLICK ISSUE
    const fileLabel = document.querySelector('.file-label');
    if (fileLabel) {
        fileLabel.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('pdfFile').click();
        });
    }
    
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('pdfFile');
    const fileName = document.getElementById('fileName');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');

    console.log('Elements found:', {
        form: !!form,
        fileInput: !!fileInput,
        fileName: !!fileName,
        loading: !!loading,
        results: !!results
    });

    // Update file name display
    if (fileInput && fileName) {
        fileInput.addEventListener('change', function() {
            console.log('File selected:', this.files[0]?.name);
            fileName.textContent = this.files[0] ? this.files[0].name : 'No file chosen';
        });
    }

    // Handle form submission
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Form submitted');
            
            if (!fileInput.files[0]) {
                console.log('No file selected');
                alert('Please select a PDF file first!');
                return;
            }

            console.log('Starting file upload...');
            const formData = new FormData();
            formData.append('pdf', fileInput.files[0]);

            // Show loading, hide results
            loading.classList.remove('hidden');
            results.classList.add('hidden');

            try {
                console.log('Sending request to /generate');
                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });

                console.log('Response received:', response.status);
                const data = await response.json();
                console.log('Response data:', data);

                if (response.ok) {
                    // Check if we got flashcards back
                    if (data.flashcards && data.flashcards.length > 0) {
                        console.log('Flashcards generated:', data.flashcards.length);
                        displayResults(data.flashcards);
                    } else {
                        throw new Error('No flashcards were generated from the PDF');
                    }
                } else {
                    throw new Error(data.error || 'Something went wrong');
                }
            } catch (error) {
                console.error('Error occurred:', error);
                alert('Error: ' + error.message);
            } finally {
                loading.classList.add('hidden');
                console.log('Request completed');
            }
        });
    }

    function displayResults(flashcards) {
        if (!flashcards || flashcards.length === 0) {
            results.innerHTML = '<p class="no-cards" style="color: white; text-align: center;">No flashcards could be generated. Try a different PDF.</p>';
            results.classList.remove('hidden');
            return;
        }

        let html = '<h2 style="color: white; text-align: center; margin-bottom: 2rem;">🎉 Your Flashcards Were Generated!</h2>';
        html += '<div style="text-align: center; margin-bottom: 2rem;">';
        html += '<a href="/dashboard" class="view-cards-btn" style="display: inline-block; padding: 1rem 2rem; background: #4CAF50; color: white; text-decoration: none; border-radius: 50px; font-size: 1.1rem;">View All Flashcards</a>';
        html += '</div>';
        
        html += '<div class="flashcards-grid">';
        flashcards.forEach((card, index) => {
            html += `
                <div class="flashcard-container" onclick="this.classList.toggle('flipped')">
                    <div class="flashcard">
                        <div class="flashcard-front">
                            <h3>Q${index + 1}</h3>
                            <p>${card.question}</p>
                            <div class="hint">Click to see answer</div>
                        </div>
                        <div class="flashcard-back">
                            <h3>Answer</h3>
                            <p>${card.answer}</p>
                            <div class="hint">Click to see question</div>
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        results.innerHTML = html;
        results.classList.remove('hidden');
        results.scrollIntoView({ behavior: 'smooth' });
    }
});