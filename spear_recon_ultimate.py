#!/usr/bin/env python3

# Spear Recon Ultimate - A comprehensive reconnaissance tool
# Author: Shan
# Date: April 07, 2025
# GitHub: github.com/yourusername/spear-recon-ultimate
# Description: A multi-platform recon tool for gathering and correlating data from social media, DNS, and more.

import requests
from bs4 import BeautifulSoup
import re
import json
import logging
from fake_useragent import UserAgent
import time
from proxy_requests import ProxyRequests
import threading
import queue
import os
from urllib.parse import urlparse
import sqlite3
from datetime import datetime
import webbrowser
import socket
from rich.console import Console
from rich.table import Table
import spacy
import socks
import socket as sock
import smtplib
import argparse
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread

# Initialize utilities
ua = UserAgent()
console = Console()
q = queue.Queue()
results = {}
nlp = spacy.load("en_core_web_sm")  # Load small English NLP model

# Tor setup
def setup_tor():
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "localhost", 9050)
    sock.socket = socks.socksocket

# Logging setup
logging.basicConfig(filename='spear_recon_ultimate.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# SQLite database setup
def init_db():
    conn = sqlite3.connect('recon_cache.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS recon 
                 (target TEXT, platform TEXT, data TEXT, timestamp TEXT, correlated TEXT)''')
    conn.commit()
    conn.close()

def cache_result(target, platform, data, correlated=""):
    conn = sqlite3.connect('recon_cache.db')
    c = conn.cursor()
    c.execute("INSERT INTO recon VALUES (?, ?, ?, ?, ?)",
              (target, platform, json.dumps(data), datetime.now().isoformat(), correlated))
    conn.commit()
    conn.close()

def get_headers():
    return {'User-Agent': ua.random, 'Accept-Language': 'en-US,en;q=0.9'}

# Fetch URL with Tor or proxy
def fetch_url(url, platform, target):
    try:
        setup_tor() if args.tor else None
        if args.tor:
            response = requests.get(url, headers=get_headers(), timeout=10)
        else:
            r = ProxyRequests(url)
            r.set_headers(get_headers())
            response = r.get()
        if response.status_code == 200:
            q.put((platform, target, response))
        else:
            q.put((platform, target, None))
    except Exception as e:
        logging.error(f"Fetch failed for {platform} - {url}: {e}")
        q.put((platform, target, None))

# Recon Functions with NLP
def facebook_recon(profile_url):
    platform = "Facebook"
    results[platform] = {}
    try:
        platform, _, response = q.get()
        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find("title").text.strip() if soup.find("title") else "Not found"
        img_match = re.search(r'"profilePic":"(https:[^"]+)"', response.text)
        profile_pic = img_match.group(1).replace('\\', '') if img_match else 'Not found'
        about_section = re.findall(r'"text":"(.*?)"', response.text)
        about = list(set(filter(lambda x: 10 < len(x) < 200 and '\\u' not in x, about_section)))[:5]
        links = [a['href'] for a in soup.find_all('a', href=True) if 'facebook.com' not in a['href']][:5]
        
        # NLP Analysis
        about_text = " ".join(about)
        doc = nlp(about_text)
        entities = {ent.text: ent.label_ for ent in doc.ents}
        
        results[platform] = {"Name": name, "Profile Picture": profile_pic, "About": about, "Links": links, "Entities": entities}
        cache_result(profile_url, platform, results[platform])
    except Exception as e:
        results[platform] = {"Error": str(e)}

def whatsapp_check(phone_number):
    platform = "WhatsApp"
    results[platform] = {}
    try:
        _, _, response = q.get()
        status = "Likely exists" if response.status_code == 302 else "Not associated" if response.status_code == 200 else f"Unexpected: {response.status_code}"
        results[platform] = {"Status": status}
        cache_result(phone_number, platform, results[platform])
    except Exception as e:
        results[platform] = {"Error": str(e)}

def twitter_recon(username):
    platform = "Twitter"
    results[platform] = {}
    try:
        _, _, response = q.get()
        soup = BeautifulSoup(response.text, 'html.parser')
        bio = soup.find('div', {'data-testid': 'UserDescription'})
        bio_text = bio.text.strip() if bio else "Not found"
        doc = nlp(bio_text)
        entities = {ent.text: ent.label_ for ent in doc.ents}
        results[platform] = {"Bio": bio_text, "Entities": entities}
        cache_result(username, platform, results[platform])
    except Exception as e:
        results[platform] = {"Error": str(e)}

def instagram_recon(username):
    platform = "Instagram"
    results[platform] = {}
    try:
        _, _, response = q.get()
        soup = BeautifulSoup(response.text, 'html.parser')
        script = soup.find('script', text=re.compile('window._sharedData'))
        if script:
            data = json.loads(script.text.split(' = ')[1].strip(';'))
            user = data['entry_data']['ProfilePage'][0]['graphql']['user']
            bio = user['biography']
            doc = nlp(bio)
            entities = {ent.text: ent.label_ for ent in doc.ents}
            results[platform] = {
                "Username": user['username'], "Full Name": user['full_name'], 
                "Bio": bio, "Followers": user['edge_followed_by']['count'], 
                "Entities": entities
            }
        cache_result(username, platform, results[platform])
    except Exception as e:
        results[platform] = {"Error": str(e)}

def dns_lookup(domain):
    platform = "DNS"
    results[platform] = {}
    try:
        ip = socket.gethostbyname(domain)
        results[platform] = {"IP Address": ip}
        cache_result(domain, platform, results[platform])
    except Exception as e:
        results[platform] = {"Error": str(e)}

def hunter_email_lookup(phone):
    platform = "Hunter"
    results[platform] = {}
    try:
        api_key = "YOUR_HUNTER_API_KEY"  # Replace with your Hunter.io API key
        response = requests.get(f"https://api.hunter.io/v2/phone-number-lookup?number={phone}&api_key={api_key}")
        if response.status_code == 200:
            data = response.json()['data']
            results[platform] = {"Emails": data.get('emails', [])}
        cache_result(phone, platform, results[platform])
    except Exception as e:
        results[platform] = {"Error": str(e)}

# Cross-platform correlation
def correlate_data():
    entities = {}
    for platform, data in results.items():
        if "Entities" in data:
            for entity, label in data["Entities"].items():
                entities.setdefault(entity, []).append(platform)
    for platform, data in results.items():
        if "Entities" in data:
            correlated = {e: ps for e, ps in entities.items() if platform in ps and len(ps) > 1}
            if correlated:
                cache_result(list(data.keys())[0], platform, data, json.dumps(correlated))

# Notification via email
def send_notification(email, subject, body):
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("your_email@gmail.com", "your_app_password")  # Replace with your credentials
            server.sendmail("your_email@gmail.com", email, f"Subject: {subject}\n\n{body}")
    except Exception as e:
        logging.error(f"Notification failed: {e}")

# Generate HTML report
def generate_report():
    html = "<html><body><h1>Spear Recon Ultimate Report</h1>"
    for platform, data in results.items():
        html += f"<h2>{platform}</h2><pre>{json.dumps(data, indent=2)}</pre>"
    html += "</body></html>"
    with open("recon_report.html", "w") as f:
        f.write(html)
    webbrowser.open("file://" + os.path.realpath("recon_report.html"))

# Main recon function
def one_click_recon(fb_url, phone, twitter_handle, insta_handle, domain, notify_email=None):
    init_db()
    threads = [
        threading.Thread(target=fetch_url, args=(fb_url, "Facebook", fb_url)),
        threading.Thread(target=fetch_url, args=(f"https://wa.me/{phone}", "WhatsApp", phone)),
        threading.Thread(target=fetch_url, args=(f"https://twitter.com/{twitter_handle}", "Twitter", twitter_handle)),
        threading.Thread(target=fetch_url, args=(f"https://instagram.com/{insta_handle}", "Instagram", insta_handle))
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    facebook_recon(fb_url)
    whatsapp_check(phone)
    twitter_recon(twitter_handle)
    instagram_recon(insta_handle)
    dns_lookup(domain)
    hunter_email_lookup(phone)

    correlate_data()

    table = Table(title="Spear Recon Ultimate Results")
    table.add_column("Platform", style="cyan")
    table.add_column("Data", style="green")
    for platform, data in results.items():
        table.add_row(platform, str(data))
    console.print(table)

    generate_report()
    if notify_email:
        send_notification(notify_email, "Spear Recon Complete", json.dumps(results, indent=2))

# GUI Interface
def run_gui():
    def start_recon():
        Thread(target=one_click_recon, args=(
            fb_entry.get(), phone_entry.get(), twitter_entry.get(), 
            insta_entry.get(), domain_entry.get(), email_entry.get()
        )).start()
        messagebox.showinfo("Started", "Recon process has begun!")

    root = tk.Tk()
    root.title("Spear Recon Ultimate by Shan")
    for i, (label, var) in enumerate([
        ("Facebook URL:", tk.StringVar()), ("Phone Number:", tk.StringVar()),
        ("Twitter Handle:", tk.StringVar()), ("Instagram Handle:", tk.StringVar()),
        ("Domain:", tk.StringVar()), ("Notify Email:", tk.StringVar())
    ]):
        ttk.Label(root, text=label).grid(row=i, column=0, padx=5, pady=5)
        entry = ttk.Entry(root, textvariable=var)
        entry.grid(row=i, column=1, padx=5, pady=5)
        if label == "Facebook URL:": fb_entry = entry
        elif label == "Phone Number:": phone_entry = entry
        elif label == "Twitter Handle:": twitter_entry = entry
        elif label == "Instagram Handle:": insta_entry = entry
        elif label == "Domain:": domain_entry = entry
        elif label == "Notify Email:": email_entry = entry

    ttk.Button(root, text="Run Recon", command=start_recon).grid(row=6, column=0, columnspan=2, pady=10)
    root.mainloop()

# CLI Interface
parser = argparse.ArgumentParser(description="Spear Recon Ultimate by Shan")
parser.add_argument("--fb", help="Facebook URL")
parser.add_argument("--phone", help="Phone number with country code")
parser.add_argument("--twitter", help="Twitter handle")
parser.add_argument("--insta", help="Instagram handle")
parser.add_argument("--domain", help="Domain for DNS lookup")
parser.add_argument("--email", help="Email for notifications")
parser.add_argument("--tor", action="store_true", help="Use Tor for anonymity")
parser.add_argument("--gui", action="store_true", help="Launch GUI")
args = parser.parse_args()

if __name__ == "__main__":
    if args.gui:
        run_gui()
    else:
        console.print("[bold green]=== Spear Recon Ultimate by Shan ===[/bold green]")
        fb_url = args.fb or input("Enter Facebook profile URL: ")
        phone = args.phone or input("Enter phone number (with country code): ")
        twitter_handle = args.twitterStattdessen or input("Enter Twitter/X handle: ")
        insta_handle = args.insta or input("Enter Instagram handle: ")
        domain = args.domain or input("Enter domain for DNS lookup: ")
        notify_email = args.email or input("Enter email for notification (optional): ")
        one_click_recon(fb_url, phone, twitter_handle, insta_handle, domain, notify_email)
