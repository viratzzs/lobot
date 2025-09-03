# open firefox webdriver and go to https://www.rbi.org.in/commonman/English/scripts/mastercircular.aspx
# get all pdfs residing in the anchor tags at selector starting from  
# tr.tablecontent1:nth-child(2) > td:nth-child(3) > a:nth-child(1)
# and upto
# tr.tablecontent1:nth-child(783) > td:nth-child(3) > a:nth-child(1)

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

def fetch_rbi_pdfs():
    """Fetch PDFs from RBI website"""
    # Create download directory first
    download_dir = os.path.join(os.path.dirname(__file__), "rbi")
    os.makedirs(download_dir, exist_ok=True)
    
    driver = setup_driver(download_dir)
    
    try:
        # Download directory already created above
        
        # Navigate to the page
        url = "https://www.rbi.org.in/commonman/English/scripts/mastercircular.aspx"
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, "tr.tablecontent1")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "tr.tablecontent2"))
            )
        )
        
        print("Extracting PDF links from RBI...")
        logger.info("Starting RBI PDF extraction")
        
        # Extract PDFs from rows 2 to 783
        pdf_count = 0
        for i in range(2, 784):  # 2 to 783
            try:
                # Try both tablecontent1 and tablecontent2 selectors
                selectors = [
                    f"tr.tablecontent1:nth-child({i}) > td:nth-child(3) > a:nth-child(1)",
                    f"tr.tablecontent2:nth-child({i}) > td:nth-child(3) > a:nth-child(1)"
                ]
                
                link_element = None
                pdf_url = None
                
                for selector in selectors:
                    try:
                        link_element = driver.find_element(By.CSS_SELECTOR, selector)
                        pdf_url = link_element.get_attribute("href")
                        if pdf_url:
                            logger.debug(f"Found link using selector: {selector}")
                            break
                    except:
                        continue
                
                if not link_element or not pdf_url:
                    continue  # Skip this row if no link found
                
                if pdf_url and ('.pdf' in pdf_url.lower() or 'pdf' in pdf_url.lower()):
                    # Extract filename from URL or link text
                    filename = link_element.text.strip()
                    if not filename:
                        filename = pdf_url.split('/')[-1]
                    
                    # Ensure proper filename
                    if not filename.endswith('.pdf'):
                        filename += '.pdf'
                    
                    # Clean filename
                    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                    
                    # Download the PDF
                    if download_pdf(pdf_url, f"rbi_{pdf_count+1}_{filename}", download_dir):
                        pdf_count += 1
                
                # Small delay to avoid overwhelming the server
                time.sleep(2)
                
            except Exception as e:
                print(f"Error processing row {i}: {str(e)}")
                logger.error(f"Error processing row {i}: {str(e)}")
                continue
        
        print(f"RBI fetch completed. Downloaded {pdf_count} PDFs.")
        logger.success(f"RBI fetch completed. Downloaded {pdf_count} PDFs.")
        
    except Exception as e:
        print(f"Error during RBI fetch: {str(e)}")
        logger.error(f"Error during RBI fetch: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_rbi_pdfs()