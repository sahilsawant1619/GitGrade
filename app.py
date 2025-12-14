from flask import Flask, render_template, request, jsonify
import requests
import re
import os
from datetime import datetime

app = Flask(__name__)

# GitHub API base URL
GITHUB_API_BASE = "https://api.github.com"

# ============================================
# SCORING FUNCTIONS (Our "Grading Rubric")
# ============================================

def check_readme(contents_data):
    """
    Check if README file exists (20 points)
    Returns: (score, message)
    """
    # Look for any file starting with README
    if isinstance(contents_data, list):
        for item in contents_data:
            if item.get('name', '').upper().startswith('README'):
                return (20, "✅ README file found")
    
    return (0, "❌ No README file found")

def check_commit_history(commits_data):
    """
    Analyze commit history (20 points)
    Returns: (score, message)
    """
    if not isinstance(commits_data, list) or len(commits_data) == 0:
        return (0, "❌ No commits found")
    
    commit_count = len(commits_data)
    
    # Score based on number of commits
    if commit_count >= 20:
        return (20, f"✅ Excellent commit history ({commit_count} recent commits)")
    elif commit_count >= 10:
        return (15, f"⚠️ Good commit history ({commit_count} recent commits)")
    elif commit_count >= 5:
        return (10, f"⚠️ Moderate commit history ({commit_count} recent commits)")
    else:
        return (5, f"❌ Limited commit history ({commit_count} commits)")

def check_structure(contents_data):
    """
    Check repository structure (15 points)
    Returns: (score, message)
    """
    if not isinstance(contents_data, list):
        return (0, "❌ Unable to analyze structure")
    
    # Look for important folders
    folders = []
    for item in contents_data:
        if item.get('type') == 'dir':  # It's a folder
            folders.append(item.get('name', '').lower())
    
    # Common good folder names
    good_folders = ['src', 'lib', 'app', 'public', 'docs', 'config', 'assets', 'static']
    
    found_count = 0
    for folder in folders:
        if folder in good_folders:
            found_count += 1
    
    # Score based on found folders
    if found_count >= 4:
        return (15, f"✅ Excellent structure ({found_count} key folders found)")
    elif found_count >= 2:
        return (10, f"⚠️ Good structure ({found_count} key folders found)")
    elif found_count == 1:
        return (5, f"⚠️ Basic structure ({found_count} key folder found)")
    else:
        return (0, "❌ Poor structure (no standard folders)")

def check_languages(repo_data):
    """
    Check languages used (15 points)
    Returns: (score, message)
    """
    primary_language = repo_data.get('language')
    
    if primary_language:
        # Bonus for popular/mainstream languages
        popular_languages = ['JavaScript', 'Python', 'Java', 'TypeScript', 'C++', 'Go', 'Rust']
        if primary_language in popular_languages:
            return (15, f"✅ Mainstream language ({primary_language})")
        else:
            return (10, f"⚠️ Using {primary_language}")
    else:
        return (0, "❌ No primary language detected")

def check_tests(contents_data):
    """
    Check for test files/folders (20 points)
    Returns: (score, message)
    """
    if not isinstance(contents_data, list):
        return (0, "❌ Unable to check for tests")
    
    # Look for test-related folders/files
    test_indicators = ['test', 'tests', '__tests__', 'spec', 'cypress', 'jest']
    
    for item in contents_data:
        name_lower = item.get('name', '').lower()
        
        # Check folder names
        if item.get('type') == 'dir':
            for indicator in test_indicators:
                if indicator in name_lower:
                    return (20, f"✅ Test folder found ({item.get('name')})")
        
        # Check file names (like test.js, spec.js)
        elif item.get('type') == 'file':
            for indicator in test_indicators:
                if f".{indicator}." in name_lower or name_lower.startswith(indicator):
                    return (15, f"⚠️ Test files found")
    
    return (0, "❌ No test structure found")

def check_code_quality(repo_data):
    """
    Check overall code quality indicators (10 points)
    Returns: (score, message)
    """
    score = 0
    messages = []
    
    # 1. Has description? (2 points)
    if repo_data.get('description'):
        score += 2
        messages.append("✓ Has description")
    else:
        messages.append("✗ Missing description")
    
    # 2. Has wiki? (2 points)
    if repo_data.get('has_wiki'):
        score += 2
        messages.append("✓ Wiki enabled")
    else:
        messages.append("✗ No wiki")
    
    # 3. Recent activity (3 points)
    updated_at = repo_data.get('pushed_at', '')
    if updated_at:
        try:
            # Convert string to datetime
            update_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            days_since_update = (datetime.utcnow() - update_date).days
            
            if days_since_update < 30:
                score += 3
                messages.append("✓ Recently updated")
            elif days_since_update < 90:
                score += 2
                messages.append("⚠️ Updated within 3 months")
            elif days_since_update < 180:
                score += 1
                messages.append("⚠️ Updated within 6 months")
            else:
                messages.append("✗ Not updated recently")
        except:
            messages.append("⚠️ Could not parse update date")
    
    # 4. Size indicator (3 points)
    size_kb = repo_data.get('size', 0)
    if size_kb > 1000:  # More than 1MB
        score += 3
        messages.append("✓ Substantial codebase")
    elif size_kb > 100:
        score += 2
        messages.append("⚠️ Moderate size")
    else:
        messages.append("✗ Small codebase")
    
    message = " | ".join(messages)
    return (score, message)

def calculate_level(score):
    """
    Convert score to level
    Returns: (level, color)
    """
    if score >= 80:
        return "Advanced", "#4cc9f0"
    elif score >= 60:
        return "Intermediate", "#f8961e"
    else:
        return "Beginner", "#ff6b6b"

def analyze_repository_data(repo_data, commits_data, contents_data):
    """
    Main analysis function - Calculate all scores
    Returns: Complete analysis results
    """
    # Calculate scores for each category
    readme_score, readme_msg = check_readme(contents_data)
    commit_score, commit_msg = check_commit_history(commits_data)
    structure_score, structure_msg = check_structure(contents_data)
    language_score, language_msg = check_languages(repo_data)
    test_score, test_msg = check_tests(contents_data)
    quality_score, quality_msg = check_code_quality(repo_data)
    
    # Calculate total score
    total_score = (readme_score + commit_score + structure_score + 
                   language_score + test_score + quality_score)
    
    # Ensure score doesn't exceed 100
    total_score = min(total_score, 100)
    
    # Get level
    level, level_color = calculate_level(total_score)
    
    # Prepare breakdown for frontend
    breakdown = [
        {"name": "README Quality", "score": readme_score, "max": 20, "status": "good" if readme_score >= 10 else "needs-work", "message": readme_msg},
        {"name": "Commit History", "score": commit_score, "max": 20, "status": "good" if commit_score >= 15 else "needs-work", "message": commit_msg},
        {"name": "Repository Structure", "score": structure_score, "max": 15, "status": "good" if structure_score >= 10 else "needs-work", "message": structure_msg},
        {"name": "Languages Used", "score": language_score, "max": 15, "status": "good" if language_score >= 10 else "needs-work", "message": language_msg},
        {"name": "Testing", "score": test_score, "max": 20, "status": "good" if test_score >= 10 else "missing", "message": test_msg},
        {"name": "Code Quality", "score": quality_score, "max": 10, "status": "good" if quality_score >= 5 else "needs-work", "message": quality_msg}
    ]
    
    # Generate AI-style summary
    summary = generate_summary(repo_data, total_score, level, breakdown)
    
    # Generate personalized roadmap
    roadmap = generate_roadmap(breakdown, repo_data)
    
    return {
        'score': total_score,
        'level': level,
        'level_color': level_color,
        'breakdown': breakdown,
        'summary': summary,
        'roadmap': roadmap
    }

def generate_summary(repo_data, score, level, breakdown):
    """
    Generate an AI-style summary that sounds like a mentor
    """
    repo_name = repo_data.get('name', 'the repository')
    owner = repo_data.get('owner', {}).get('login', 'Unknown')
    description = repo_data.get('description', '')
    language = repo_data.get('language', 'unknown language')
    stars = repo_data.get('stargazers_count', 0)
    forks = repo_data.get('forks_count', 0)
    
    # Find strongest and weakest categories
    strongest_category = max(breakdown, key=lambda x: x['score'] / x['max'])
    weakest_category = min(breakdown, key=lambda x: x['score'] / x['max'])
    
    # Different opening phrases based on score
    if score >= 85:
        opening = f"🌟 **Impressive work!** {repo_name} by {owner} demonstrates professional-grade development practices. "
        tone = "This repository could serve as a model for other open-source projects."
    elif score >= 70:
        opening = f"📈 **Solid foundation!** {repo_name} shows good software engineering principles. "
        tone = "With some targeted improvements, this could become an exemplary repository."
    elif score >= 50:
        opening = f"🚧 **Good start!** {repo_name} has the basics in place. "
        tone = "Focus on the roadmap below to elevate your project quality."
    else:
        opening = f"🌱 **Getting started!** Every great project begins somewhere. "
        tone = "Use this analysis as a guide for your development journey."
    
    # Language-specific advice
    lang_advice = ""
    if language == "JavaScript":
        lang_advice = " As a JavaScript project, consider adding ESLint for code consistency and Prettier for formatting."
    elif language == "Python":
        lang_advice = " For Python projects, adding type hints and using Black for code formatting would be beneficial."
    elif language == "TypeScript":
        lang_advice = " TypeScript provides excellent type safety - ensure you're leveraging strict mode for maximum benefits."
    
    # Activity-based advice
    activity_advice = ""
    if stars > 1000:
        activity_advice = f" With {stars:,} stars, this project shows significant community interest."
    elif stars > 100:
        activity_advice = f" The project has gained traction with {stars:,} stars."
    
    # Strengths and weaknesses
    strengths = f" Your strongest area is **{strongest_category['name']}**, scoring {strongest_category['score']}/{strongest_category['max']}. "
    improvements = f" The main area for improvement is **{weakest_category['name']}**."
    
    # Combine everything
    summary = f"{opening}{strengths}{improvements}{lang_advice}{activity_advice} {tone}"
    
    return summary

def generate_roadmap(breakdown, repo_data):
    """
    Generate personalized, actionable improvement steps
    """
    roadmap = []
    
    # Sort by score (lowest first = most needed improvements)
    sorted_breakdown = sorted(breakdown, key=lambda x: x['score'] / x['max'])
    
    # Check each category and add specific advice
    for category in sorted_breakdown:
        category_name = category["name"]
        category_score = category["score"]
        category_max = category["max"]
        percentage = (category_score / category_max * 100)
        
        if percentage < 50:  # Needs significant improvement
            if category_name == "README Quality":
                roadmap.append({
                    "priority": "HIGH",
                    "title": "Create comprehensive documentation",
                    "steps": [
                        "Add a detailed README.md with project description",
                        "Include installation instructions",
                        "Add usage examples and API documentation",
                        "Consider adding badges for build status, coverage, etc."
                    ]
                })
            
            elif category_name == "Commit History":
                roadmap.append({
                    "priority": "HIGH",
                    "title": "Improve commit practices",
                    "steps": [
                        "Make smaller, more frequent commits",
                        "Use conventional commit messages (feat:, fix:, docs:, etc.)",
                        "Write descriptive commit messages that explain 'why' not just 'what'",
                        "Consider using git hooks for consistency"
                    ]
                })
            
            elif category_name == "Repository Structure":
                roadmap.append({
                    "priority": "MEDIUM",
                    "title": "Organize project structure",
                    "steps": [
                        "Create logical folders (src/, tests/, docs/, config/)",
                        "Separate source code from configuration files",
                        "Use consistent naming conventions",
                        "Consider using a project template or generator"
                    ]
                })
            
            elif category_name == "Testing":
                roadmap.append({
                    "priority": "HIGH",
                    "title": "Add testing framework",
                    "steps": [
                        "Choose a testing framework (Jest for JS, Pytest for Python, etc.)",
                        "Add unit tests for critical functions",
                        "Set up continuous integration to run tests automatically",
                        "Add test coverage reporting"
                    ]
                })
    
    # Always add these general best practices
    roadmap.append({
        "priority": "MEDIUM",
        "title": "Implement continuous integration",
        "steps": [
            "Set up GitHub Actions or similar CI/CD pipeline",
            "Automate testing on pull requests",
            "Add automated dependency updates",
            "Set up automated builds and deployments"
        ]
    })
    
    roadmap.append({
        "priority": "LOW",
        "title": "Enhance project visibility",
        "steps": [
            "Add a LICENSE file if not present",
            "Create a CONTRIBUTING.md guide",
            "Add a CODE_OF_CONDUCT.md file",
            "Consider adding issue and pull request templates"
        ]
    })
    
    return roadmap[:4]  # Return top 4 recommendations max

# ============================================
# FLASK ROUTES (Same as before)
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_repo():
    try:
        data = request.json
        repo_url = data.get('url', '').strip()
        
        if not repo_url:
            return jsonify({'error': 'Please provide a GitHub URL'}), 400
        
        # Extract owner and repo name
        pattern = r'github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, repo_url)
        
        if not match:
            return jsonify({'error': 'Invalid GitHub URL format'}), 400
        
        owner = match.group(1)
        repo_name = match.group(2)
        
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        # Make API calls
        repo_api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}"
        repo_response = requests.get(repo_api_url)
        
        if repo_response.status_code != 200:
            return jsonify({
                'error': f'Repository not found. GitHub says: {repo_response.json().get("message", "Unknown error")}'
            }), 404
        
        repo_data = repo_response.json()
        
        # Get additional data
        commits_api_url = f"{repo_api_url}/commits?per_page=30"
        commits_response = requests.get(commits_api_url)
        commits_data = commits_response.json() if commits_response.status_code == 200 else []
        
        contents_api_url = f"{repo_api_url}/contents"
        contents_response = requests.get(contents_api_url)
        contents_data = contents_response.json() if contents_response.status_code == 200 else []
        
        # Run analysis
        analysis_result = analyze_repository_data(repo_data, commits_data, contents_data)
        
        # Prepare response
        result = {
            'status': 'success',
            'analysis': analysis_result,
            'repository_info': {
                'name': repo_data.get('name', 'Unknown'),
                'owner': repo_data.get('owner', {}).get('login', 'Unknown'),
                'description': repo_data.get('description', 'No description'),
                'stars': repo_data.get('stargazers_count', 0),
                'forks': repo_data.get('forks_count', 0),
                'language': repo_data.get('language', 'Not specified'),
                'created_at': repo_data.get('created_at', 'Unknown'),
                'updated_at': repo_data.get('pushed_at', 'Unknown'),
                'size': repo_data.get('size', 0),
                'has_wiki': repo_data.get('has_wiki', False),
                'has_issues': repo_data.get('has_issues', False),
                'open_issues': repo_data.get('open_issues_count', 0)
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)