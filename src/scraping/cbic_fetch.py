# open firefox webdriver and go to https://cbic-gst.gov.in/hindi/circulars.html
# extract all pdfs from #circulars > table:nth-child(2) > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(2) > a:nth-child(1)
# upto 
# #circulars > table:nth-child(2) > tbody:nth-child(2) > tr:nth-child(175) > td:nth-child(2) > a:nth-child(1)

import os
import time
import requests
from loguru import logger
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver(download_dir):
    """Setup Firefox WebDriver with options"""
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    
    # Set download preferences
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf,application/octet-stream")
    options.set_preference("pdfjs.disabled", True)  # Disable PDF viewer
    
    service = Service()  # Uses system geckodriver
    driver = webdriver.Firefox(service=service, options=options)
    return driver

def download_pdf(url, filename, folder_path):
    """Download PDF from URL"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        filepath = os.path.join(folder_path, filename)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded: {filename}")
        logger.info(f"Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"Error downloading {filename}: {str(e)}")
        logger.error(f"Error downloading {filename}: {str(e)}")
        return False

def fetch_cbic_pdfs():
    """Fetch PDFs from CBIC website"""
    # Create download directory first
    download_dir = os.path.join(os.path.dirname(__file__), "cbic")
    os.makedirs(download_dir, exist_ok=True)
    
    driver = setup_driver(download_dir)
    
    try:
        # Download directory already created above
        
        # Navigate to the page
        url = "https://cbic-gst.gov.in/hindi/circulars.html"
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#circulars"))
        )
        
        print("Extracting PDF links from CBIC...")
        logger.info("Starting CBIC PDF extraction")
        
        # Extract PDFs from rows 1 to 175
        pdf_count = 0
        for i in range(1, 176):  # 1 to 175
            try:
                # Construct CSS selector for each row
                selector = f"#circulars > table:nth-child(2) > tbody:nth-child(2) > tr:nth-child({i}) > td:nth-child(2) > a:nth-child(1)"
                
                # Find the link element
                link_element = driver.find_element(By.CSS_SELECTOR, selector)
                pdf_url = link_element.get_attribute("href")
                
                if pdf_url and pdf_url.endswith('.pdf'):
                    # Extract filename from URL
                    filename = pdf_url.split('/')[-1]
                    if not filename.endswith('.pdf'):
                        filename += '.pdf'
                    
                    # Download the PDF
                    if download_pdf(pdf_url, f"cbic_{pdf_count+1}_{filename}", download_dir):
                        pdf_count += 1
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing row {i}: {str(e)}")
                logger.error(f"Error processing row {i}: {str(e)}")
                continue
        
        print(f"CBIC fetch completed. Downloaded {pdf_count} PDFs.")
        logger.success(f"CBIC fetch completed. Downloaded {pdf_count} PDFs.")
        
    except Exception as e:
        print(f"Error during CBIC fetch: {str(e)}")
        logger.error(f"Error during CBIC fetch: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_cbic_pdfs()
