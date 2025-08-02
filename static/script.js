// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const resumeFile = document.getElementById('resume-file');
    const resultsContainer = document.getElementById('results-container');
    const loader = document.getElementById('loader');
    
    const scoreCircle = document.querySelector('.score-circle');
    const scoreText = document.querySelector('.score-text');
    const detailsList = document.getElementById('details-list');
    const notesList = document.getElementById('notes-list');

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (resumeFile.files.length === 0) {
            alert('Please select a file to upload.');
            return;
        }

        const formData = new FormData();
        formData.append('resume', resumeFile.files[0]);

        // Show loader and hide old results
        loader.classList.remove('hidden');
        resultsContainer.classList.add('hidden');

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Something went wrong');
            }

            const data = await response.json();
            displayResults(data);

        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            loader.classList.add('hidden');
        }
    });

    function displayResults(data) {
        // Update score circle
        scoreText.textContent = `${data.score}%`;
        scoreCircle.style.background = `conic-gradient(#2ECC71 ${data.score * 3.6}deg, #E0E0E0 0deg)`;

        // Clear previous details
        detailsList.innerHTML = '';
        notesList.innerHTML = '';

        // Populate extracted details
        detailsList.innerHTML = `
            <li><strong>Email:</strong> ${data.details.email}</li>
            <li><strong>Phone:</strong> ${data.details.phone}</li>
            <li><strong>Detected Skills:</strong> ${data.details.skills.join(', ') || 'None'}</li>
        `;

        // Populate analysis notes
        data.details.analysis_notes.forEach(note => {
            const li = document.createElement('li');
            li.textContent = note;
            notesList.appendChild(li);
        });

        // Show results
        resultsContainer.classList.remove('hidden');
    }
});