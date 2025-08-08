# Install required packages 
!pip install gradio requests beautifulsoup4 pandas plotly openai selenium fake-useragent tenacity

# Import all required modules
import gradio as gr
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import openai
import json
import re
import time
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to set up OpenAI API
def setup_openai(api_key):
    openai.api_key = api_key
    return True

# Function to get random headers
def get_headers():
    ua = UserAgent()
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

# Function to scrape a static URL
def scrape_static_url(url, timeout=30):
    try:
        headers = get_headers()
        session = requests.Session()
        session.headers.update(headers)

        logger.info(f"Scraping: {url}")
        response = session.get(url, timeout=timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract text content
        text_content = ' '.join([p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5'])])

        # Extract tables if any
        tables = []
        for table in soup.find_all('table'):
            table_data = []
            for row in table.find_all('tr'):
                row_data = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
                if row_data:
                    table_data.append(row_data)
            if table_data:
                tables.append(table_data)

        return {
            'url': url,
            'text_content': text_content,
            'tables': tables,
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        return {
            'url': url,
            'error': str(e),
            'status': 'error'
        }

# Function to scrape multiple URLs
def scrape_multiple_sources(urls, use_selenium=False, timeout=30, wait_time=10):
    results = []

    for url in urls:
        if use_selenium:
            # For simplicity, we'll just use static scraping for now
            result = scrape_static_url(url, timeout)
        else:
            result = scrape_static_url(url, timeout)

        results.append(result)
        time.sleep(1)  # Small delay to avoid being blocked

    return results

# Function to process data with OpenAI - Updated for new API
def process_with_openai(api_key, scraped_data, prompt, chart_type, model="gpt-3.5-turbo", timeout=120):
    try:
        # Set up OpenAI
        setup_openai(api_key)

        # Prepare the data for OpenAI
        combined_text = ""
        success_count = 0

        for data in scraped_data:
            if data['status'] == 'success':
                content = data['text_content'][:1000]  # Limit content
                combined_text += f"URL: {data['url']}\n"
                combined_text += f"Content: {content}...\n\n"
                success_count += 1

                if len(combined_text) > 15000:  # Limit total content
                    combined_text += "\n[Content truncated due to length limitations]"
                    break

        if success_count == 0:
            return {
                'status': 'error',
                'error': 'No data was successfully scraped from the provided URLs'
            }

        # Create a simple, direct prompt
        full_prompt = f"""
        Extract numerical data from the following web content for a {chart_type} visualization.

        TASK: {prompt}

        Respond ONLY with valid JSON in this format:
        {{
            "labels": ["Category1", "Category2"],
            "values": [10, 20],
            "title": "Chart Title"
        }}

        WEB CONTENT:
        {combined_text}
        """

        logger.info(f"Sending request to OpenAI API")

        # Generate response - Updated for new OpenAI API
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You extract numerical data from text and format it as JSON. Respond only with JSON."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.0,
            max_tokens=2048,
            timeout=timeout
        )

        # Extract response text - Updated for new OpenAI API
        response_text = response.choices[0].message.content
        logger.info(f"OpenAI response: {response_text[:200]}...")

        return {
            'status': 'success',
            'response': response_text
        }
    except Exception as e:
        logger.error(f"Error processing with OpenAI: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

# Function to extract JSON from OpenAI response
def extract_json_from_response(response_text):
    try:
        # Try to find JSON in code blocks
        json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # Try to find JSON object
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))

        # If no JSON found, return None
        return None
    except Exception as e:
        logger.error(f"Error extracting JSON: {str(e)}")
        return None

# Function to create a bar chart
def create_bar_chart(data):
    try:
        if isinstance(data, dict) and 'labels' in data and 'values' in data:
            fig = px.bar(
                x=data['labels'],
                y=data['values'],
                title=data.get('title', 'Bar Chart')
            )
            return fig

        # If data is not in the expected format, create a simple example chart
        fig = px.bar(
            x=['A', 'B', 'C'],
            y=[1, 2, 3],
            title='Example Bar Chart (Data format was incorrect)'
        )
        return fig
    except Exception as e:
        logger.error(f"Error creating bar chart: {str(e)}")
        # Return a simple error chart
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating chart: {str(e)}", showarrow=False)
        return fig

# Function to create a line chart
def create_line_chart(data):
    try:
        if isinstance(data, dict) and 'x' in data and 'y' in data:
            fig = px.line(
                x=data['x'],
                y=data['y'],
                title=data.get('title', 'Line Chart')
            )
            return fig

        # If data is not in the expected format, create a simple example chart
        fig = px.line(
            x=[1, 2, 3],
            y=[1, 4, 2],
            title='Example Line Chart (Data format was incorrect)'
        )
        return fig
    except Exception as e:
        logger.error(f"Error creating line chart: {str(e)}")
        # Return a simple error chart
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating chart: {str(e)}", showarrow=False)
        return fig

# Function to create a pie chart
def create_pie_chart(data):
    try:
        if isinstance(data, dict) and 'labels' in data and 'values' in data:
            fig = px.pie(
                names=data['labels'],
                values=data['values'],
                title=data.get('title', 'Pie Chart')
            )
            return fig

        # If data is not in the expected format, create a simple example chart
        fig = px.pie(
            names=['A', 'B', 'C'],
            values=[1, 2, 3],
            title='Example Pie Chart (Data format was incorrect)'
        )
        return fig
    except Exception as e:
        logger.error(f"Error creating pie chart: {str(e)}")
        # Return a simple error chart
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating chart: {str(e)}", showarrow=False)
        return fig

# Function to create a scatter plot
def create_scatter_plot(data):
    try:
        if isinstance(data, dict) and 'x' in data and 'y' in data:
            fig = px.scatter(
                x=data['x'],
                y=data['y'],
                title=data.get('title', 'Scatter Plot')
            )
            return fig

        # If data is not in the expected format, create a simple example chart
        fig = px.scatter(
            x=[1, 2, 3],
            y=[1, 4, 2],
            title='Example Scatter Plot (Data format was incorrect)'
        )
        return fig
    except Exception as e:
        logger.error(f"Error creating scatter plot: {str(e)}")
        # Return a simple error chart
        fig = go.Figure()
        fig.add_annotation(text=f"Error creating chart: {str(e)}", showarrow=False)
        return fig

# Main function to scrape and visualize
def scrape_and_visualize(api_key, urls, prompt, chart_type, use_selenium=False, timeout=30, wait_time=10, openai_timeout=120, model="gpt-3.5-turbo"):
    try:
        logger.info("Starting scrape_and_visualize")

        # Parse URLs
        url_list = [url.strip() for url in urls.split('\n') if url.strip()]
        logger.info(f"Parsed {len(url_list)} URLs")

        # Scrape data
        scraped_data = scrape_multiple_sources(url_list, use_selenium, timeout, wait_time)

        # Process with OpenAI
        openai_result = process_with_openai(api_key, scraped_data, prompt, chart_type, model, openai_timeout)

        # Extract data for visualization
        visualization_data = None
        if openai_result['status'] == 'success':
            visualization_data = extract_json_from_response(openai_result['response'])

        # If we couldn't extract valid data, create a fallback
        if visualization_data is None:
            logger.warning("Could not extract valid JSON, creating fallback visualization")
            visualization_data = {
                "labels": ["No Data", "Extracted", "From Sites"],
                "values": [1, 2, 3],
                "title": "Fallback Chart (Data extraction failed)"
            }

        # Create visualization based on chart type
        if chart_type == "Bar Chart":
            fig = create_bar_chart(visualization_data)
        elif chart_type == "Line Chart":
            fig = create_line_chart(visualization_data)
        elif chart_type == "Pie Chart":
            fig = create_pie_chart(visualization_data)
        elif chart_type == "Scatter Plot":
            fig = create_scatter_plot(visualization_data)
        else:
            fig = create_bar_chart(visualization_data)

        # Prepare scraped data summary
        scraped_summary = ""
        for data in scraped_data:
            if data['status'] == 'success':
                scraped_summary += f"✓ {data['url']}: Successfully scraped\n"
                if data['tables']:
                    scraped_summary += f"  - Found {len(data['tables'])} table(s)\n"
            else:
                scraped_summary += f"✗ {data['url']}: {data['error']}\n"

        # Prepare OpenAI response
        if openai_result['status'] == 'success':
            openai_response = openai_result['response']
        else:
            openai_response = f"Error: {openai_result['error']}"

        return (
            openai_response,
            fig,
            scraped_summary
        )
    except Exception as e:
        logger.error(f"Error in scrape_and_visualize: {str(e)}")

        # Create a fallback chart
        fig = go.Figure()
        fig.add_annotation(text=f"Error: {str(e)}", showarrow=False)

        return (
            f"Error: {str(e)}",
            fig,
            f"Error: {str(e)}"
        )

# Create the Gradio UI
def create_ui():
    with gr.Blocks(title="Data Scraper and Visualization Tool") as app:
        gr.Markdown("# Data Scraper and Visualization Tool")
        gr.Markdown("This tool scrapes data from multiple sources, processes it with OpenAI API, and creates visualizations.")

        with gr.Row():
            with gr.Column(scale=1):
                api_key = gr.Textbox(
                    label="OpenAI API Key",
                    placeholder="Enter your OpenAI API key",
                    type="password"
                )

                urls = gr.Textbox(
                    label="URLs to Scrape",
                    placeholder="Enter URLs (one per line)",
                    lines=5,
                    value="https://en.wikipedia.org/wiki/World_population"
                )

                prompt = gr.Textbox(
                    label="Prompt for OpenAI",
                    placeholder="Enter instructions for data processing",
                    lines=3,
                    value="Extract population data by year for a bar chart visualization."
                )

                chart_type = gr.Dropdown(
                    label="Chart Type",
                    choices=["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot"],
                    value="Bar Chart"
                )

                with gr.Accordion("Advanced Settings", open=False):
                    use_selenium = gr.Checkbox(
                        label="Use Selenium for Dynamic Content",
                        value=False
                    )

                    timeout = gr.Slider(
                        label="Request Timeout (seconds)",
                        minimum=10,
                        maximum=120,
                        value=30,
                        step=5
                    )

                    wait_time = gr.Slider(
                        label="Page Load Wait Time (seconds)",
                        minimum=5,
                        maximum=30,
                        value=10,
                        step=1
                    )

                    openai_timeout = gr.Slider(
                        label="OpenAI API Timeout (seconds)",
                        minimum=30,
                        maximum=300,
                        value=120,
                        step=10
                    )

                    model = gr.Dropdown(
                        label="OpenAI Model",
                        choices=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                        value="gpt-3.5-turbo"
                    )

                submit_btn = gr.Button("Scrape and Visualize")

            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.TabItem("Visualization"):
                        visualization_output = gr.Plot(label="Data Visualization")

                    with gr.TabItem("OpenAI Response"):
                        openai_output = gr.Textbox(
                            label="OpenAI Response",
                            lines=15,
                            interactive=False
                        )

                    with gr.TabItem("Scraping Results"):
                        scraping_output = gr.Textbox(
                            label="Scraping Results",
                            lines=10,
                            interactive=False
                        )

        submit_btn.click(
            fn=scrape_and_visualize,
            inputs=[api_key, urls, prompt, chart_type, use_selenium, timeout, wait_time, openai_timeout, model],
            outputs=[openai_output, visualization_output, scraping_output]
        )

    return app

# Run the application
if __name__ == "__main__":
    app = create_ui()
    app.launch(debug=True, share=True)
