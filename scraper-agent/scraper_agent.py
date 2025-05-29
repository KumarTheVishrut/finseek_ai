import datetime
import logging
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from sec_cik_mapper import StockMapper
from typing import Optional, Dict, Any
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SEC 10-K Content Scraper")

# Initialize CIK mapper
mapper = StockMapper()

class FilingContent(BaseModel):
    symbol: str
    cik: str
    accession_number: str
    filing_date: str
    filing_type: str
    content: str
    document_url: str
    metadata: Dict[str, Any] = {}

def random_delay():
    """Add random delay to avoid rate limiting"""
    delay = random.uniform(2.0, 4.0)  # Increased delay
    logger.info(f"Waiting {delay:.2f} seconds...")
    time.sleep(delay)

def get_headers():
    """Return realistic browser headers with proper SEC compliance"""
    return {
        "User-Agent": "YourCompany YourName your.email@company.com",  # SEC requires contact info
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

@app.get("/10k-content", response_model=FilingContent)
async def get_10k_content(
    symbol: str = Query(..., min_length=1, max_length=10, regex="^[A-Z]+$"),
    year: int = Query(None, ge=1990, le=datetime.datetime.now().year)
):
    """
    Retrieve full 10-K filing content as text blob
    Example: /10k-content?symbol=AAPL&year=2023
    """
    try:
        logger.info(f"Processing request for {symbol}, year: {year}")
        random_delay()
        
        # Get CIK using sec-cik-mapper
        cik = mapper.ticker_to_cik.get(symbol.upper())
        if not cik:
            logger.error(f"CIK not found for {symbol}")
            raise HTTPException(
                status_code=404,
                detail=f"CIK not found for {symbol}. Try full company name or check symbol."
            )
        
        logger.info(f"Found CIK {cik} for {symbol}")
        
        # Try multiple approaches to find the filing
        filing_url, filing_metadata = await get_10k_filing_url_robust(cik, symbol, year)
        if not filing_url:
            raise HTTPException(
                status_code=404,
                detail=f"No 10-K filing found for {symbol} in {year or 'most recent year'}. Check if the company files 10-K reports or try a different year."
            )
        
        logger.info(f"Found filing URL: {filing_url}")
        
        # Retrieve the full filing content
        content = await get_filing_content(filing_url)
        
        return FilingContent(
            symbol=symbol,
            cik=cik,
            accession_number=filing_metadata['accession_number'],
            filing_date=filing_metadata['filing_date'],
            filing_type="10-K",
            content=content,
            document_url=filing_url,
            metadata=filing_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

async def get_10k_filing_url_robust(cik: str, symbol: str, year: Optional[int]) -> tuple:
    """Get the URL for the 10-K filing document with multiple fallback methods"""
    
    # Method 1: Try the classic EDGAR search
    try:
        result = await try_edgar_search(cik, symbol, year)
        if result[0]:
            logger.info("Found filing using EDGAR search")
            return result
    except Exception as e:
        logger.warning(f"EDGAR search failed: {e}")
    
    # Method 2: Try the JSON API approach
    try:
        result = await try_json_api_search(cik, symbol, year)
        if result[0]:
            logger.info("Found filing using JSON API")
            return result
    except Exception as e:
        logger.warning(f"JSON API search failed: {e}")
    
    # Method 3: Try direct CIK-based search
    try:
        result = await try_direct_cik_search(cik, symbol, year)
        if result[0]:
            logger.info("Found filing using direct CIK search")
            return result
    except Exception as e:
        logger.warning(f"Direct CIK search failed: {e}")
    
    logger.error(f"All search methods failed for {symbol}")
    return None, None

async def try_edgar_search(cik: str, symbol: str, year: Optional[int]) -> tuple:
    """Original EDGAR search method"""
    try:
        # Build SEC filing search URL
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K&count=40"
        if year:
            url += f"&dateb={year}1231"
        
        logger.info(f"Searching EDGAR: {url}")
        
        response = requests.get(url, headers=get_headers(), timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for both possible table classes
        table = soup.find('table', class_='tableFile2') or soup.find('table', {'summary': 'Results'})
        if not table:
            logger.warning("No results table found in EDGAR search")
            return None, None
        
        # Find the correct filing row
        rows = table.find_all('tr')[1:]  # Skip header
        logger.info(f"Found {len(rows)} rows in results table")
        
        for i, row in enumerate(rows):
            cols = row.find_all('td')
            if len(cols) >= 4:
                filing_type = cols[0].text.strip()
                filing_date = cols[3].text.strip()
                
                logger.info(f"Row {i}: Type='{filing_type}', Date='{filing_date}'")
                
                if filing_type == "10-K":
                    if year and not filing_date.startswith(str(year)):
                        continue
                    
                    # Get the document link
                    doc_link_elem = cols[1].find('a')
                    if not doc_link_elem:
                        continue
                        
                    doc_link = doc_link_elem['href']
                    
                    # Extract accession number more robustly
                    accession_match = re.search(r'data/(\d+)/(\d{18})', doc_link)
                    if accession_match:
                        accession_number = accession_match.group(2)
                    else:
                        accession_number = "unknown"
                    
                    # Get the actual 10-K document URL
                    filing_url = await get_document_url(doc_link)
                    if filing_url:
                        return filing_url, {
                            'accession_number': accession_number,
                            'filing_date': filing_date,
                            'search_method': 'edgar_search'
                        }
        
        return None, None
        
    except Exception as e:
        logger.error(f"EDGAR search error: {e}")
        return None, None

async def try_json_api_search(cik: str, symbol: str, year: Optional[int]) -> tuple:
    """Try using SEC's JSON API"""
    try:
        # Pad CIK to 10 digits
        padded_cik = str(cik).zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
        
        logger.info(f"Trying JSON API: {url}")
        
        headers = get_headers()
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        # Look through recent filings
        recent_filings = data.get('filings', {}).get('recent', {})
        forms = recent_filings.get('form', [])
        dates = recent_filings.get('filingDate', [])
        accession_numbers = recent_filings.get('accessionNumber', [])
        primary_docs = recent_filings.get('primaryDocument', [])
        
        for i, form in enumerate(forms):
            if form == '10-K':
                filing_date = dates[i]
                if year and not filing_date.startswith(str(year)):
                    continue
                
                accession = accession_numbers[i]
                primary_doc = primary_docs[i] if i < len(primary_docs) else None
                
                # Try to get the primary document (usually .htm file)
                if primary_doc and primary_doc.endswith('.htm'):
                    accession_clean = accession.replace('-', '')
                    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_doc}"
                    
                    return doc_url, {
                        'accession_number': accession_clean,
                        'filing_date': filing_date,
                        'search_method': 'json_api',
                        'primary_document': primary_doc
                    }
                else:
                    # Fallback to the filing index page
                    accession_clean = accession.replace('-', '')
                    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{accession}-index.htm"
                    
                    # This would need further processing to find the right document
                    logger.info(f"Found 10-K but need to parse index: {index_url}")
        
        return None, None
        
    except Exception as e:
        logger.error(f"JSON API search error: {e}")
        return None, None

async def try_direct_cik_search(cik: str, symbol: str, year: Optional[int]) -> tuple:
    """Try direct access to filings by CIK"""
    try:
        # Try browsing the CIK directory directly
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/"
        
        logger.info(f"Trying direct CIK search: {url}")
        
        response = requests.get(url, headers=get_headers(), timeout=20)
        response.raise_for_status()
        
        # This would require parsing directory listings
        # For now, return None as this is more complex
        return None, None
        
    except Exception as e:
        logger.error(f"Direct CIK search error: {e}")
        return None, None

async def get_document_url(doc_link: str) -> Optional[str]:
    """Extract the actual document URL from the filing page with better error handling"""
    try:
        url = f"https://www.sec.gov{doc_link}"
        logger.info(f"Getting document URL from: {url}")
        
        response = requests.get(url, headers=get_headers(), timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the documents table
        table = soup.find('table', class_='tableFile') or soup.find('table', {'summary': 'Document Format Files'})
        
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            logger.info(f"Found {len(rows)} document rows")
            
            # Priority order for document selection
            preferred_docs = []
            fallback_docs = []
            
            for i, row in enumerate(rows):
                cols = row.find_all('td')
                if len(cols) >= 4:
                    seq = cols[0].text.strip()
                    description = cols[1].text.strip()
                    document_link = cols[2].find('a')
                    doc_type = cols[3].text.strip()
                    
                    if not document_link:
                        continue
                        
                    doc_path = document_link['href']
                    doc_name = document_link.text.strip()
                    
                    logger.info(f"Row {i}: seq={seq}, doc={doc_name}, type={doc_type}, desc={description}")
                    
                    # Skip XBRL viewer links and XML files
                    if ('ix?doc=' in doc_path or 'ixviewer' in doc_path or 
                        doc_name.endswith('.xml') or doc_name.endswith('.xsd')):
                        logger.info(f"Skipping XBRL/XML document: {doc_name}")
                        continue
                    
                    full_url = f"https://www.sec.gov{doc_path}"
                    
                    # Prioritize based on document characteristics
                    if (doc_type == "10-K" and doc_name.endswith('.htm')):
                        preferred_docs.append((0, full_url))  # Highest priority
                    elif (seq == "1" and doc_name.endswith('.htm')):
                        preferred_docs.append((1, full_url))  # Second priority
                    elif doc_name.endswith('.htm'):
                        fallback_docs.append((2, full_url))  # Lower priority
                    elif doc_name.endswith('.txt'):
                        fallback_docs.append((3, full_url))  # Text fallback
            
            # Return the best available document
            all_docs = preferred_docs + fallback_docs
            if all_docs:
                all_docs.sort(key=lambda x: x[0])  # Sort by priority
                selected_url = all_docs[0][1]
                logger.info(f"Selected document URL: {selected_url}")
                return selected_url
        
        # Fallback: look for any .htm link that's not an XBRL viewer
        for link in soup.find_all('a', href=True):
            href = link['href']
            if (href.endswith('.htm') and not href.startswith('http') and 
                'ix?doc=' not in href and 'ixviewer' not in href):
                full_url = f"https://www.sec.gov{href}"
                logger.info(f"Fallback document URL: {full_url}")
                return full_url
        
        logger.warning("No suitable document URL found")
        return None
        
    except Exception as e:
        logger.error(f"Error getting document URL: {e}")
        return None

async def get_filing_content(url: str) -> str:
    """Retrieve the full content of the filing with better error handling"""
    try:
        logger.info(f"Retrieving filing content from: {url}")
        
        response = requests.get(url, headers=get_headers(), timeout=30)
        response.raise_for_status()
        
        # Check for XBRL viewer response
        if 'XBRL Viewer' in response.text or 'ixviewer' in response.text:
            logger.error("Retrieved XBRL viewer page instead of document content")
            raise Exception("Retrieved XBRL viewer page instead of actual document. The document may be in XBRL format only.")
        
        # Check if it's an HTML document or plain text
        content_type = response.headers.get('content-type', '').lower()
        
        if 'html' in content_type:
            # Extract just the text content (no HTML tags)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if this is actually a 10-K document by looking for key sections
            text_content = soup.get_text().lower()
            if not any(keyword in text_content for keyword in [
                'form 10-k', 'annual report', 'item 1.', 'business', 'risk factors', 
                'management discussion', 'financial statements'
            ]):
                logger.warning("Document doesn't appear to contain typical 10-K content")
            
            # Remove unwanted elements but keep some structure
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            # Get clean text with reasonable spacing
            text = soup.get_text(separator='\n', strip=True)
        else:
            # Plain text document
            text = response.text
        
        # Clean up the text more intelligently
        lines = []
        for line in text.splitlines():
            line = line.strip()
            # Keep lines that have substantial content
            if line and (len(line) > 3 or line.isdigit()):
                lines.append(line)
        
        cleaned_text = '\n'.join(lines)
        
        # Remove excessive blank lines
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        # Limit content size to prevent memory issues
        if len(cleaned_text) > 2000000:  # 2MB limit (increased)
            cleaned_text = cleaned_text[:2000000] + "\n\n[Content truncated at 2MB limit]"
        
        logger.info(f"Retrieved {len(cleaned_text)} characters of content")
        
        # More lenient content check
        if len(cleaned_text) < 500:
            raise Exception("Retrieved content is too short, likely an error page")
        
        # Final validation - check for common error indicators
        error_indicators = [
            'access denied', 'not found', 'error occurred', 'please try again',
            'temporarily unavailable', 'maintenance mode'
        ]
        
        lower_content = cleaned_text.lower()
        for indicator in error_indicators:
            if indicator in lower_content and len(cleaned_text) < 5000:
                raise Exception(f"Retrieved content appears to be an error page: contains '{indicator}'")
        
        return cleaned_text
        
    except Exception as e:
        logger.error(f"Error retrieving filing content: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to retrieve filing content: {str(e)}"
        )

@app.get("/debug-filing")
async def debug_filing(
    symbol: str = Query(..., min_length=1, max_length=10, regex="^[A-Z]+$"),
    year: int = Query(None, ge=1990, le=datetime.datetime.now().year)
):
    """Debug endpoint to see what filings are available"""
    try:
        # Get CIK
        cik = mapper.ticker_to_cik.get(symbol.upper())
        if not cik:
            return {"error": f"CIK not found for {symbol}"}
        
        # Try EDGAR search
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K&count=10"
        if year:
            url += f"&dateb={year}1231"
        
        response = requests.get(url, headers=get_headers(), timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = {
            "symbol": symbol,
            "cik": cik,
            "search_url": url,
            "filings": []
        }
        
        table = soup.find('table', class_='tableFile2')
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    filing_type = cols[0].text.strip()
                    if filing_type == "10-K":
                        doc_link = cols[1].find('a')['href'] if cols[1].find('a') else None
                        filing_date = cols[3].text.strip()
                        
                        filing_info = {
                            "filing_type": filing_type,
                            "filing_date": filing_date,
                            "doc_link": doc_link,
                            "documents": []
                        }
                        
                        # Get document details
                        if doc_link:
                            try:
                                doc_url = f"https://www.sec.gov{doc_link}"
                                doc_response = requests.get(doc_url, headers=get_headers(), timeout=15)
                                doc_soup = BeautifulSoup(doc_response.text, 'html.parser')
                                
                                doc_table = doc_soup.find('table', class_='tableFile')
                                if doc_table:
                                    doc_rows = doc_table.find_all('tr')[1:]
                                    for doc_row in doc_rows:
                                        doc_cols = doc_row.find_all('td')
                                        if len(doc_cols) >= 4:
                                            seq = doc_cols[0].text.strip()
                                            desc = doc_cols[1].text.strip()
                                            doc_name = doc_cols[2].text.strip()
                                            doc_type = doc_cols[3].text.strip()
                                            
                                            filing_info["documents"].append({
                                                "sequence": seq,
                                                "description": desc,
                                                "document": doc_name,
                                                "type": doc_type
                                            })
                            except Exception as e:
                                filing_info["document_error"] = str(e)
                        
                        results["filings"].append(filing_info)
        
        return results
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "scraper-agent"}

@app.get("/earnings-surprises")
async def get_earnings_surprises(symbol: str = Query(..., description="Stock symbol to get earnings data for")):
    """Get earnings surprise data for a given symbol"""
    try:
        logger.info(f"Getting earnings surprises for {symbol}")
        
        # Mock earnings data - in production would scrape from earnings calendars
        # Asia tech stocks earnings patterns
        earnings_data = {
            "2330": {"surprise_pct": 8.5, "expected": 1.2, "actual": 1.3, "period": "Q4 2024"},
            "005930.KS": {"surprise_pct": -2.1, "expected": 0.95, "actual": 0.93, "period": "Q4 2024"},
            "9988.HK": {"surprise_pct": 12.3, "expected": 2.1, "actual": 2.36, "period": "Q4 2024"},
            "ASML": {"surprise_pct": 5.7, "expected": 4.5, "actual": 4.76, "period": "Q4 2024"},
            "TSM": {"surprise_pct": 6.2, "expected": 1.8, "actual": 1.91, "period": "Q4 2024"}
        }
        
        # Default data for unknown symbols
        default_data = {"surprise_pct": 3.2, "expected": 1.0, "actual": 1.032, "period": "Q4 2024"}
        
        # Get data for the symbol, fallback to default
        result = earnings_data.get(symbol, earnings_data.get(symbol.replace(".TW", "").replace(".KS", "").replace(".HK", ""), default_data))
        
        return {
            "symbol": symbol,
            "surprise_pct": result["surprise_pct"],
            "expected_eps": result["expected"],
            "actual_eps": result["actual"],
            "reporting_period": result["period"],
            "surprise_direction": "positive" if result["surprise_pct"] > 0 else "negative",
            "data_source": "mock_earnings_calendar"
        }
        
    except Exception as e:
        logger.error(f"Earnings surprises error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting earnings data: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with usage instructions"""
    return {
        "message": "SEC 10-K Content Scraper API",
        "usage": "GET /10k-content?symbol=AAPL&year=2023",
        "docs": "/docs",
        "health": "/health",
        "debug": "/debug-filing?symbol=AAPL&year=2023"
    }