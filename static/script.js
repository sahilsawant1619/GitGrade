// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const repoUrlInput = document.getElementById('repoUrl');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingCard = document.getElementById('loadingCard');
    const resultsSection = document.getElementById('resultsSection');
    const scoreValue = document.getElementById('scoreValue');
    const levelBadge = document.getElementById('levelBadge');
    const breakdownList = document.getElementById('breakdownList');
    const summaryContent = document.getElementById('summaryContent');
    const roadmapContent = document.getElementById('roadmapContent');
    const repoInfo = document.getElementById('repoInfo');

    // Debug: Check if elements exist
    console.log('Button found:', analyzeBtn);
    console.log('Input found:', repoUrlInput);

    // Event Listeners
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzeRepository);
        console.log('Event listener added to button');
    } else {
        console.error('Analyze button not found!');
    }

    if (repoUrlInput) {
        repoUrlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') analyzeRepository();
        });
    }

    // Initialize with instructions
    initializePage();

    // Main Analysis Function
    async function analyzeRepository() {
        console.log('Button clicked! Starting analysis...');
        
        const repoUrl = repoUrlInput.value.trim();
        
        if (!repoUrl) {
            showError('Please enter a GitHub repository URL');
            return;
        }
        
        // Validate URL format
        if (!isValidGitHubUrl(repoUrl)) {
            showError('Please enter a valid GitHub repository URL (e.g., https://github.com/username/repo)');
            return;
        }
        
        // Show loading, hide results
        loadingCard.style.display = 'block';
        resultsSection.style.display = 'none';
        
        console.log('Fetching data for:', repoUrl);
        
        try {
            // Prepare data to send to backend
            const requestData = {
                url: repoUrl
            };
            
            // Send request to Flask backend
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            // Get response
            const result = await response.json();
            console.log('Response received:', result);
            
            // Check if analysis was successful
            if (result.status === 'success') {
                showSuccess(`Successfully analyzed ${repoUrl}`);
                displayResults(result);
            } else {
                showError(result.error || 'Failed to analyze repository');
            }
            
        } catch (error) {
            console.error('Analysis failed:', error);
            showError('Network error. Please check your connection and try again.');
        } finally {
            loadingCard.style.display = 'none';
        }
    }

    // Display Results
    function displayResults(result) {
        const analysis = result.analysis;
        const repoInfoData = result.repository_info;
        
        // Update score and level
        scoreValue.textContent = analysis.score || 0;
        levelBadge.textContent = analysis.level || 'Beginner';
        levelBadge.style.background = getLevelColor(analysis.level || 'Beginner');
        
        // Update breakdown with REAL scores
        updateBreakdown(analysis.breakdown);
        
        // Update summary
        summaryContent.innerHTML = `
            <p><strong>Analysis of ${repoInfoData.owner}/${repoInfoData.name}:</strong></p>
            <p>${analysis.summary || "No summary available"}</p>
            <p style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px; font-size: 0.9em;">
                <strong>Language:</strong> ${repoInfoData.language} | 
                <strong>Stars:</strong> ${repoInfoData.stars.toLocaleString()} | 
                <strong>Updated:</strong> ${formatDate(repoInfoData.updated_at)}
            </p>
        `;
        
        // Update roadmap
        updateRoadmap(analysis.roadmap);
        
        // Update repository info
        updateRepoInfo([
            { label: "Repository Name", value: repoInfoData.name },
            { label: "Owner", value: repoInfoData.owner },
            { label: "Stars", value: repoInfoData.stars.toLocaleString() },
            { label: "Forks", value: repoInfoData.forks.toLocaleString() },
            { label: "Primary Language", value: repoInfoData.language || "Not detected" },
            { label: "Repository Size", value: `${(repoInfoData.size / 1024).toFixed(1)} MB` },
            { label: "Open Issues", value: repoInfoData.open_issues },
            { label: "Created", value: formatDate(repoInfoData.created_at) }
        ]);
        
        // Show results
        resultsSection.style.display = 'block';
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Update breakdown list
    function updateBreakdown(breakdown) {
        breakdownList.innerHTML = '';
        
        breakdown.forEach(item => {
            const itemElement = document.createElement('div');
            itemElement.className = `breakdown-item ${item.status}`;
            
            const scorePercent = (item.score / item.max * 100).toFixed(0);
            
            itemElement.innerHTML = `
                <h4>${item.name}</h4>
                <div style="margin: 8px 0; font-size: 0.9em; color: #555;">
                    ${item.message || ''}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                    <span>${item.score}/${item.max} points</span>
                    <span style="font-weight: 600; color: ${getStatusColor(item.status)}">${scorePercent}%</span>
                </div>
                <div style="height: 8px; background: #e9ecef; border-radius: 4px; margin-top: 8px; overflow: hidden;">
                    <div style="width: ${scorePercent}%; height: 100%; background: ${getStatusColor(item.status)};"></div>
                </div>
            `;
            
            breakdownList.appendChild(itemElement);
        });
    }

    // Update roadmap
    function updateRoadmap(roadmap) {
        if (!roadmap || roadmap.length === 0) {
            roadmapContent.innerHTML = `
                <p>Excellent! Your repository follows best practices. Consider:</p>
                <div class="roadmap-item" style="background: #f0f9ff; border-left: 4px solid #4cc9f0;">
                    <div class="roadmap-header">
                        <span class="priority-badge" style="background: #4cc9f0;">ADVANCED</span>
                        <h4>Next-Level Improvements</h4>
                    </div>
                    <ul>
                        <li>Add performance benchmarking</li>
                        <li>Implement automated security scanning</li>
                        <li>Create a changelog with semantic versioning</li>
                        <li>Add integration with package registries</li>
                    </ul>
                </div>
            `;
            return;
        }
        
        let roadmapHTML = `
            <p>Based on our analysis, here's your personalized improvement roadmap:</p>
            <p><small>Items are prioritized by impact on your repository quality.</small></p>
        `;
        
        roadmap.forEach((item, index) => {
            const priorityColor = getPriorityColor(item.priority);
            const priorityText = item.priority.charAt(0) + item.priority.slice(1).toLowerCase();
            
            roadmapHTML += `
                <div class="roadmap-item" style="margin-bottom: 20px; padding: 20px; background: ${priorityColor}15; border-left: 4px solid ${priorityColor}; border-radius: 0 8px 8px 0;">
                    <div class="roadmap-header" style="display: flex; align-items: center; margin-bottom: 12px;">
                        <span class="priority-badge" style="background: ${priorityColor}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: 600; margin-right: 10px;">
                            ${priorityText} PRIORITY
                        </span>
                        <h4 style="margin: 0; font-size: 1.1em;">${item.title}</h4>
                    </div>
                    <ol style="margin: 0; padding-left: 20px;">
                        ${item.steps.map(step => `<li style="margin-bottom: 8px;">${step}</li>`).join('')}
                    </ol>
                </div>
            `;
        });
        
        roadmapContent.innerHTML = roadmapHTML;
    }

    // Update repository info
    function updateRepoInfo(details) {
        repoInfo.innerHTML = '';
        
        details.forEach(detail => {
            const itemElement = document.createElement('div');
            itemElement.className = 'info-item';
            
            itemElement.innerHTML = `
                <h4>${detail.label}</h4>
                <p>${detail.value}</p>
            `;
            
            repoInfo.appendChild(itemElement);
        });
    }

    // Initialize page with instructions
    function initializePage() {
        summaryContent.innerHTML = `
            <p>Enter a GitHub repository URL above and click "Analyze Repository"</p>
            <p>Example: https://github.com/facebook/react</p>
        `;
        
        roadmapContent.innerHTML = `
            <p>The analysis will check:</p>
            <ul>
                <li>✓ Repository structure and organization</li>
                <li>✓ README quality and presence</li>
                <li>✓ Commit history patterns</li>
                <li>✓ Code quality indicators</li>
                <li>✓ Testing practices</li>
            </ul>
        `;
        
        updateRepoInfo([
            { label: "Status", value: "Ready to analyze" },
            { label: "API", value: "GitHub REST API" },
            { label: "Authentication", value: "None required" },
            { label: "Rate Limit", value: "60 requests/hour" }
        ]);
        
        // Show mock score for demo
        scoreValue.textContent = "85";
        levelBadge.textContent = "Advanced";
        levelBadge.style.background = getLevelColor("Advanced");
    }

    // Error handling functions
    function showError(message) {
        // Remove any existing alerts
        const existingAlert = document.querySelector('.alert');
        if (existingAlert) existingAlert.remove();
        
        // Create error message
        const alert = document.createElement('div');
        alert.className = 'alert error';
        alert.innerHTML = `
            <strong>⚠️ Error:</strong> ${message}
            <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; cursor: pointer; font-size: 1.2em;">×</button>
        `;
        
        // Insert after input card
        const inputCard = document.querySelector('.input-card');
        inputCard.parentNode.insertBefore(alert, inputCard.nextSibling);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) alert.remove();
        }, 5000);
    }

    function showSuccess(message) {
        // Remove any existing alerts
        const existingAlert = document.querySelector('.alert');
        if (existingAlert) existingAlert.remove();
        
        // Create success message
        const alert = document.createElement('div');
        alert.className = 'alert success';
        alert.innerHTML = `
            <strong>✅ Success:</strong> ${message}
            <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; cursor: pointer; font-size: 1.2em;">×</button>
        `;
        
        // Insert after input card
        const inputCard = document.querySelector('.input-card');
        inputCard.parentNode.insertBefore(alert, inputCard.nextSibling);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (alert.parentNode) alert.remove();
        }, 3000);
    }

    // Helper Functions
    function isValidGitHubUrl(url) {
        const pattern = /^https?:\/\/github\.com\/[a-zA-Z0-9-_.]+\/[a-zA-Z0-9-_.]+$/;
        return pattern.test(url);
    }

    function getLevelColor(level) {
        switch(level.toLowerCase()) {
            case 'beginner': return 'linear-gradient(135deg, #ff6b6b, #ee5a52)';
            case 'intermediate': return 'linear-gradient(135deg, #ffd93d, #ffb347)';
            case 'advanced': return 'linear-gradient(135deg, #4cc9f0, #4361ee)';
            default: return '#e9ecef';
        }
    }

    function getStatusColor(status) {
        switch(status) {
            case 'good': return '#4cc9f0';
            case 'needs-work': return '#f8961e';
            case 'missing': return '#6c757d';
            default: return '#4361ee';
        }
    }

    function getPriorityColor(priority) {
        switch(priority.toUpperCase()) {
            case 'HIGH': return '#f72585';
            case 'MEDIUM': return '#f8961e';
            case 'LOW': return '#4cc9f0';
            default: return '#6c757d';
        }
    }

    function formatDate(dateString) {
        if (!dateString || dateString === 'Unknown') return 'Unknown';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (e) {
            return dateString;
        }
    }
});