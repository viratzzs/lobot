# PDF Scraping Scripts

This directory contains Selenium-based scripts to extract PDFs from various regulatory websites.

## Scripts Overview

### 1. CBIC Fetch (`cbic_fetch.py`)
- **Source**: CBIC GST Circulars
- **URL**: https://cbic-gst.gov.in/hindi/circulars.html
- **Target**: Extracts PDFs from table rows 1-175
- **Output Directory**: `cbic/`

### 2. RBI Fetch (`rbi_fetch.py`)
- **Source**: RBI Master Circulars
- **URL**: https://www.rbi.org.in/commonman/English/scripts/mastercircular.aspx
- **Target**: Extracts PDFs from table rows 2-783
- **Output Directory**: `rbi/`

### 3. Supreme Court Fetch (`sc_fetch.py`)
- **Source**: Indian Kanoon Search Results
- **URL**: https://indiankanoon.org/search/?formInput=fromdate%3A%2001-01-2015%20todate%3A%2001-08-2025%20doctypes%3Atreaties%2Cirdai%2Crbi%2Csebi%2Cclb%2Cdrat%2Cnclat%2Cdebates%2C
- **Target**: Extracts PDFs from search results (10 per page)
- **Output Directory**: `sc/`

### 4. SEBI Fetch (`sebi_fetch.py`)
- **Source**: SEBI Regulations
- **URL**: https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=6&smid=0
- **Target**: Extracts PDFs from 125 records (25 per page)
- **Output Directory**: `sebi/`

## Prerequisites

### 1. Python Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```

### 2. Firefox WebDriver (GeckoDriver)
- Download GeckoDriver from: https://github.com/mozilla/geckodriver/releases
- Add it to your system PATH, OR
- Place `geckodriver.exe` in the same directory as the scripts

### 3. Firefox Browser
- Ensure Firefox is installed on your system
- The scripts run in headless mode by default

## Usage

### Running Individual Scripts
```bash
# Run CBIC fetcher
python cbic_fetch.py

# Run RBI fetcher
python rbi_fetch.py

# Run Supreme Court fetcher
python sc_fetch.py

# Run SEBI fetcher
python sebi_fetch.py
```

### Running All Scripts
```bash
python run_all_fetchers.py
```

## Configuration

### Headless Mode
All scripts run in headless mode by default. To see the browser:
```python
# In each script, comment out this line:
options.add_argument("--headless")
```

### Download Delays
Scripts include delays between requests to be respectful to servers:
- 0.5 seconds between individual PDF downloads
- 1-3 seconds between page navigations
- 30 seconds between different fetchers in `run_all_fetchers.py`

### Error Handling
- Scripts continue processing even if individual PDFs fail
- Detailed error logging is provided
- Failed downloads are logged but don't stop the entire process

## Output Structure

```
scraping/
├── cbic/                 # CBIC PDFs
│   ├── cbic_1_...pdf
│   ├── cbic_2_...pdf
│   └── ...
├── rbi/                  # RBI PDFs
│   ├── rbi_1_...pdf
│   ├── rbi_2_...pdf
│   └── ...
├── sc/                   # Supreme Court PDFs
│   ├── sc_doc_page1_record1.pdf
│   ├── sc_doc_page1_record2.pdf
│   └── ...
└── sebi/                 # SEBI PDFs
    ├── sebi_1_...pdf
    ├── sebi_2_...pdf
    └── ...
```

## Troubleshooting

### Common Issues

1. **GeckoDriver not found**
   - Ensure GeckoDriver is in PATH or same directory
   - Download from: https://github.com/mozilla/geckodriver/releases

2. **Timeout errors**
   - Increase WebDriverWait timeout values in scripts
   - Check internet connection

3. **Element not found errors**
   - Website structure may have changed
   - Update CSS selectors in the scripts

4. **Permission errors**
   - Ensure write permissions in the output directories
   - Run with appropriate user permissions

### Debugging
- Remove `--headless` option to see browser actions
- Add `time.sleep()` delays if elements load slowly
- Check browser console for JavaScript errors

## Notes

- These scripts are designed for educational and research purposes
- Be respectful to the target websites and their terms of service
- Consider implementing additional rate limiting for large-scale extractions
- Scripts may need updates if website structures change
