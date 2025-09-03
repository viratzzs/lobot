# open firefox webdriver and go to https://indiankanoon.org/search/?formInput=fromdate%3A%2001-01-2015%20todate%3A%2001-08-2025%20doctypes%3Atreaties%2Cirdai%2Crbi%2Csebi%2Cclb%2Cdrat%2Cnclat%2Cdebates%2C
# each page has 10 records
# from 
# div.result:nth-child(4) > div:nth-child(1) > a:nth-child(1)
# upto
# div.result:nth-child(13) > div:nth-child(1) > a:nth-child(1)
# extract pdf from form object's post method .docoptions > form:nth-child(2)
# once done with all records on the page, go to the next page by clicking on css link html body div.results_content div.results_middle div.bottom a

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
from urllib.parse import urljoin

def setup_driver(download_dir):
    """Setup Firefox WebDriver with options"""
    options = Options()
    options.add_argument("--headless")
    
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf,application/octet-stream")
    options.set_preference("pdfjs.disabled", True)
    
    service = Service()
    driver = webdriver.Firefox(service=service, options=options)
    return driver


def extract_pdf_from_form(driver, result_link, doc_id, download_dir):
    """Extract PDF from the form's post method with improved timeout handling"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Click on the result link
            result_link.click()
            time.sleep(3)  # Increased wait time
            
            # Wait for the page to load and find the form with longer timeout
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".docoptions > form:nth-child(2)"))
            )
            
            # Find the form and submit it to get PDF
            form = driver.find_element(By.CSS_SELECTOR, ".docoptions > form:nth-child(2)")
            pdf_url = form.get_attribute("action")
            
            if pdf_url:
                form.submit()
                time.sleep(5)  # Increased wait for form submission
                logger.info(f"Successfully extracted PDF for {doc_id} on attempt {attempt + 1}")
                return True
            
            logger.warning(f"No PDF URL found for {doc_id} on attempt {attempt + 1}")
            return False
            
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {doc_id}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(5)  # Wait before retry
                # Go back to try again
                try:
                    driver.back()
                    time.sleep(2)
                except:
                    pass
            else:
                print(f"Error extracting PDF for doc {doc_id}: {str(e)}")
                logger.error(f"Error extracting PDF for doc {doc_id}: {str(e)}")
                return False
    
    return False

def fetch_sc_pdfs():
    """Fetch PDFs from Supreme Court (Indian Kanoon) website"""
    download_dir = os.path.join(os.path.dirname(__file__), "sc")
    os.makedirs(download_dir, exist_ok=True)
    
    driver = setup_driver(download_dir)
    
    try:
        #base_url = "https://indiankanoon.org/search/?formInput=fromdate%3A%2001-01-2015%20todate%3A%2001-08-2025%20doctypes%3Atreaties%2Cirdai%2Crbi%2Csebi%2Cclb%2Cdrat%2Cnclat%2Cdebates%2C"
        base_url = "https://indiankanoon.org/search/?formInput=doctypes%3A%20treaties%2Cirdai%2Crbi%2Csebi%2Cclb%2Cnclat%2Cdrat%2Cdebates%20fromdate%3A%201-1-2015%20todate%3A%201-8-2025&pagenum=40"
        print("Extracting PDF links from Supreme Court (Indian Kanoon)...")
        logger.info("Starting Supreme Court PDF extraction")
        
        page_count = 41
        total_pdfs = 0

        for i in range(150):  # Increased limit, removed arbitrary break
            try:
                # Navigate to the current page
                if page_count == 1:
                    driver.get(base_url)
                    next_button_selector = ".bottom > a:nth-child(10)"
                else:
                    # Click next page link with better error handling
                    try:
                        next_link = driver.find_element(By.CSS_SELECTOR, next_button_selector)
                        next_link.click()
                        next_button_selector = ".bottom > a:nth-child(11)"
                    except Exception as e:
                        logger.warning(f"Could not find next page link with selector {next_button_selector}: {str(e)}")
                        # Try alternative selectors
                        alternative_selectors = [
                            ".bottom > a:last-child",
                            ".bottom a[href*='Start=']",
                            ".bottom a:contains('Next')",
                            "a[title='Next']"
                        ]
                        next_clicked = False
                        for alt_selector in alternative_selectors:
                            try:
                                next_link = driver.find_element(By.CSS_SELECTOR, alt_selector)
                                next_link.click()
                                logger.info(f"Used alternative selector: {alt_selector}")
                                next_clicked = True
                                break
                            except:
                                continue
                        
                        if not next_clicked:
                            logger.warning(f"No next page link found, stopping at page {page_count}")
                            break
                
                # Wait for page to load with increased timeout
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.result"))
                )
                
                print(f"Processing page {page_count}...")
                logger.info(f"Processing page {page_count}...")
                
                page_pdfs = 0
                for i in range(4, 14):  # div.result:nth-child(4) to div.result:nth-child(13)
                    try:
                        selector = f"div.result:nth-child({i}) > div:nth-child(1) > a:nth-child(1)"
                        result_links = driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        if result_links:
                            result_link = result_links[0]
                            doc_id = f"page{page_count}_record{i-3}"
                            
                            
                            if extract_pdf_from_form(driver, result_link, doc_id, download_dir):
                                page_pdfs += 1
                                total_pdfs += 1
                            
                            driver.back()
                            time.sleep(1)
                    
                    except Exception as e:
                        error_msg = str(e)
                        print(f"Error processing record {i} on page {page_count}: {error_msg}")
                        logger.error(f"Error processing record {i} on page {page_count}: {error_msg}")
                        
                        # On any error (including timeout), just move to next record
                        if "timeout" in error_msg.lower() or "read timed out" in error_msg.lower():
                            logger.warning(f"Timeout on record {i}, page {page_count} - moving to next record")
                        
                        continue  # Simply continue to next record
                
                print(f"Page {page_count} completed. Downloaded {page_pdfs} PDFs.")
                logger.info(f"Page {page_count} completed. Downloaded {page_pdfs} PDFs.")
                
                # Check if there's a next page with improved logic
                try:
                    # First check if we have more results to process
                    current_results = driver.find_elements(By.CSS_SELECTOR, "div.result")
                    if len(current_results) < 10:  # Fewer than expected results might mean last page
                        logger.info(f"Found only {len(current_results)} results on page {page_count}, might be last page")
                    
                    # Try to find next page link
                    next_links = driver.find_elements(By.CSS_SELECTOR, next_button_selector)
                    
                    if not next_links:
                        # Try alternative selectors for next page
                        alternative_selectors = [
                            ".bottom > a:last-child",
                            ".bottom a[href*='Start=']",
                            "a[title='Next']",
                            ".bottom a:contains('>')"
                        ]
                        
                        found_next = False
                        for alt_selector in alternative_selectors:
                            try:
                                alt_links = driver.find_elements(By.CSS_SELECTOR, alt_selector)
                                if alt_links:
                                    next_links = alt_links
                                    next_button_selector = alt_selector
                                    found_next = True
                                    logger.info(f"Found next page using alternative selector: {alt_selector}")
                                    break
                            except:
                                continue
                        
                        if not found_next:
                            logger.info(f"No more pages found after page {page_count}")
                            break
                    
                    # Verify the next link is actually clickable and leads to next page
                    if next_links:
                        next_link = next_links[0]
                        href = next_link.get_attribute("href")
                        if href and "Start=" in href:
                            logger.info(f"Next page link found: {href}")
                        else:
                            logger.warning(f"Next page link might not be valid: {href}")
                            
                except Exception as e:
                    logger.error(f"Error checking for next page: {str(e)}")
                    break
                
                page_count += 1
                time.sleep(2)  # Delay between pages
                
            except Exception as e:
                error_msg = str(e)
                print(f"Error on page {page_count}: {error_msg}")
                logger.error(f"Error on page {page_count}: {error_msg}")
                
                # On timeout, just move to next page
                if "timeout" in error_msg.lower() or "read timed out" in error_msg.lower():
                    logger.warning(f"Timeout on page {page_count} - moving to next page")
                    page_count += 1
                    time.sleep(3)  # Brief pause before next page
                    continue
                else:
                    # For other errors, break as before
                    break
        
        print(f"SC fetch completed. Downloaded {total_pdfs} PDFs across {page_count} pages.")
        logger.success(f"SC fetch completed. Downloaded {total_pdfs} PDFs across {page_count} pages.")
        
    except Exception as e:
        print(f"Error during SC fetch: {str(e)}")
        logger.error(f"Error during SC fetch: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_sc_pdfs()