# Spear Recon Ultimate

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)

A comprehensive reconnaissance tool for gathering and correlating data from social media platforms, DNS, and more.

## Author
- **Shan**  
- GitHub: [github.com/shaa2020](https://github.com/shaa2020)  
- Created: April 07, 2025

## Features
- Reconnaissance on Facebook, WhatsApp, Twitter, Instagram, DNS, and Hunter.io (email lookup).
- NLP analysis using SpaCy for entity extraction.
- Cross-platform data correlation.
- Tor and proxy support for anonymity.
- SQLite caching for results.
- HTML report generation.
- Email notifications.
- CLI and GUI interfaces.

## Prerequisites
- Python 3.8+
- Required libraries: `requests`, `beautifulsoup4`, `fake-useragent`, `proxy-requests`, `spacy`, `rich`, `socks`, `tkinter`, etc.
- Tor installed and running on `localhost:9050` (optional).
- Hunter.io API key (optional).
- Gmail account with app-specific password for notifications (optional).

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/shaa2020/spear-recon-ultimate.git
   cd spear-recon-ultimate

2. Install Dependencies:
   ```bash
   pip install -r requirements.txt

3. Download the SpaCy model:
   ```bash
   python -m spacy download en_core_web_sm

4. Configure credentials (e.g., Hunter.io API key, Gmail credentials) in the script.


---

### Notes for Ensuring It Works Perfectly
1. **Dependencies**: Install all required libraries via `pip install -r requirements.txt`. Some (`tkinter`, `smtplib`, etc.) are part of Python's standard library.
2. **Tor**: Ensure Tor is installed and running on `localhost:9050` if you use the `--tor` flag.
3. **Hunter.io**: Replace `YOUR_HUNTER_API_KEY` with a valid API key from [Hunter.io](https://hunter.io/).
4. **Email**: Replace `your_email@gmail.com` and `your_app_password` with your Gmail credentials (use an [app-specific password](https://support.google.com/accounts/answer/185833)).
5. **Instagram**: The Instagram scraping might not work as expected due to changes in their API/HTML structure. You may need to update the `instagram_recon` function accordingly.
6. **Testing**: Test with dummy data first to avoid rate limits or bans from platforms.
