# data-scraper-visualization-tool
A tool that scrapes data from multiple sources, processes it with OpenAI API, and creates visualizations

## Features
- Multi-source web scraping with BeautifulSoup and Selenium support
- AI-powered data processing using OpenAI's GPT models
- Interactive chart generation (bar, line, pie, scatter plots)
- User-friendly Gradio interface
- Smart error handling and fallback mechanisms

## Tech Stack
- Python
- OpenAI API
- Gradio
- BeautifulSoup
- Plotly
- Selenium
- Pandas
- Requests

## Installation
1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt

  ## Run the application:
 python app.py

## Usage
- Enter your OpenAI API key
- Add URLs to scrape (one per line)
- Enter a prompt for data processing
- Select a chart type
- Click "Scrape and Visualize"

## License
MIT License
#### 4. `.gitignore` (To exclude unnecessary files)
Create this file with the following content:
Python
pycache/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

## Virtual Environment
venv/
ENV/

## IDE
.vscode/
.idea/
*.swp
*.swo

## Logs
*.log

## Environment variables
.env

### Step 3: Initialize Git and Commit Files
1. Open a terminal/command prompt in your project directory
2. Initialize Git:
   ```bash
   git init

## Add files to staging:
git add .

## Commit your files
git commit -m "Initial commit: Data scraper and visualization tool"
