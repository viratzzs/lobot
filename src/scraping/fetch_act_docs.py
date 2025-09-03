# 1. css selector for search bar in https://www.indiacode.nic.in/handle/123456789/1359/simple-search?page-token=3694e3ca47a9&page-token-value=682018a04eb53c22eee9c33f5b8f8513&nccharset=06355B94&location=123456789%2F1359&query=&rpp=10&sort_by=score&order=DESC&submit_search=Update
# .discovery-query > form:nth-child(1) > input:nth-child(5)

# 2. the go button that has to be pressed after inserting the query to show results
# #main-query-submit

# 3. css selector for first result that shows up
# .table > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(4) > a:nth-child(1)

# 4. selector for url that contains the pdf for that document
# a.standard:nth-child(1)

# 5. loop and repeat for each record's act name in extracted_acts.json


import json
import requests
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options
from loguru import logger
import re

logger.add("scraping.log", rotation="1 MB")

bare_acts_dir = "d:\\projects\\lobot\\src\\scraping\\bare_acts"
os.makedirs(bare_acts_dir, exist_ok=True)

with open("d:\\projects\\lobot\\extracted_acts.json", "r", encoding="utf-8") as f:
    acts = json.load(f)

logger.info(f"Loaded {len(acts)} acts to process")

firefox_options = Options()
firefox_options.add_argument("--headless")
firefox_options.add_argument("--no-sandbox")
firefox_options.add_argument("--disable-dev-shm-usage")
firefox_options.add_argument("--disable-web-security")
firefox_options.add_argument("--disable-features=VizDisplayCompositor")
firefox_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
driver = webdriver.Firefox(options=firefox_options)

base_url = "https://www.indiacode.nic.in/handle/123456789/1359/simple-search"

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def download_pdf(pdf_url, filename):
    """Download PDF from URL and save to bare_acts directory"""
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        filepath = os.path.join(bare_acts_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.success(f"Downloaded: {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {filename}: {str(e)}")
        return False

def search_and_download_act(act_name, act_year, s_no):
    """Search for act and download PDF"""
    try:
        # Navigate to search page
        driver.get(base_url)
        logger.debug(f"Navigated to search page for {act_name}")
        
        search_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".discovery-query > form:nth-child(1) > input:nth-child(5)"))
        )
        search_input.clear()
        search_input.send_keys(act_name)
        logger.debug(f"Entered search query: {act_name}")
        
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#main-query-submit"))
        )
        search_button.click()
        logger.debug("Clicked search button")
        
        time.sleep(5)
        
        # td.oddRowEvenCol:nth-child(3)
        
        first_result = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".table > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(4) > a:nth-child(1)"))
        )
        first_result.click()
        logger.debug("Clicked first result")
        
        time.sleep(5)
        
        pdf_link = None
        pdf_url = None
        
        pdf_selectors = [
            #"a.standard:nth-child(1)",
            "html body.undernavigation main#content div.container-fluid div.display-item div.container div.row a p#short_title.standard"
        ]
        
        for selector in pdf_selectors:
            try:
                pdf_link = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                pdf_url = pdf_link.get_attribute("href")
                if pdf_url and '.pdf' in pdf_url.lower():
                    logger.debug(f"Found PDF URL with selector '{selector}': {pdf_url}")
                    break
                else:
                    pdf_link = None
            except:
                continue
        
        # If no PDF link found with selectors, try to find any PDF links on the page
        if not pdf_link:
            try:
                all_links = driver.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and '.pdf' in href.lower():
                        pdf_url = href
                        logger.debug(f"Found PDF URL by scanning all links: {pdf_url}")
                        break
            except:
                pass
        
        if pdf_url:
            # Generate filename
            sanitized_name = sanitize_filename(act_name)
            filename = f"{s_no}_{sanitized_name}_{act_year}.pdf"
            
            # Download PDF
            return download_pdf(pdf_url, filename)
        else:
            logger.warning(f"No PDF URL found for {act_name}")
            # Log page source for debugging
            logger.debug(f"Page title: {driver.title}")
            logger.debug(f"Current URL: {driver.current_url}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing {act_name}: {str(e)}")
        return False

# Process each act
successful_downloads = 0
failed_downloads = 0

for i, act in enumerate(acts):
    act_name = act.get("Name", "")
    act_year = act.get("Year", "")
    s_no = act.get("S.No", "")
    
    logger.info(f"Processing {i+1}/{len(acts)}: {act_name} ({act_year})")
    
    if search_and_download_act(act_name, act_year, s_no):
        successful_downloads += 1
    else:
        failed_downloads += 1
    
    # Add delay to avoid overwhelming the server
    time.sleep(2)
    
    # Log progress every 10 acts
    if (i + 1) % 10 == 0:
        logger.info(f"Progress: {i+1}/{len(acts)} processed, {successful_downloads} successful, {failed_downloads} failed")

# Close driver
driver.quit()

logger.info(f"Scraping completed! Successfully downloaded: {successful_downloads}, Failed: {failed_downloads}")
