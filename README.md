# web-scraper

A powerful desktop application for web scraping built with Python and PyQt5.

Features
Easy URL Scraping: Enter any URL and retrieve the full HTML content
CSS Selector Extraction: Extract specific content using CSS selectors
Flexible Content Options: Choose to extract text, links, images, or HTML
Multi-threaded Processing: Background processing keeps the UI responsive
History Tracking: Keep track of previously scraped websites
Dark/Light Theme: Switch between themes for comfortable viewing
Customizable Settings: Adjust timeout, user-agent, and font size
Technical Details
Built with Python and PyQt5
Uses BeautifulSoup4 for HTML parsing
Implements QThread for non-blocking UI during scraping operations
Custom ThemeSwitch widget for theme toggling
Persistent history using JSON storage
Screenshots

[Add screenshots here]

Requirements
Python 3.6+
PyQt5
BeautifulSoup4
Requests
Installation
# Clone the repository
git clone https://github.com/azeddine0/web-scraper.git
cd web-scraper-pro

# Install dependencies
pip install -r requirements.txt

# Run the application
python scraper.py

Usage
Enter a URL in the input field
Click "Scrape" to retrieve the webpage
Enter a CSS selector (e.g., "div.content", "h1", "a.link")
Select extraction options (Text, Links, Images, HTML)
Click "Extract" to get the content
Save results or clear for a new search
License

[Your chosen license]

Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
