"""
API Global Portal Sync Agent
Automates verification of railroad crew sign-in sheets
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_name(name: str) -> str:
    """Normalize name for matching - remove suffixes, lowercase, etc."""
    if not name:
        return ""
    # Remove common suffixes like BMR, HBW, MBW, etc.
    name = re.sub(r'/[A-Z]{2,4}\s*$', '', name.strip())
    # Convert LASTNAME/FIRSTNAME format to "firstname lastname"
    parts = name.split('/')
    if len(parts) >= 2:
        # Format: LASTNAME/FIRSTNAME or LASTNAME/FIRSTNAME/SUFFIX
        lastname = parts[0].strip()
        firstname = parts[1].strip()
        return f"{firstname} {lastname}".lower()
    return name.lower().strip()


def match_names(api_name: str, hodler_name: str, threshold: float = 0.7) -> bool:
    """Check if two names match using fuzzy matching."""
    norm_api = normalize_name(api_name)
    norm_hodler = normalize_name(hodler_name)
    
    # Exact match
    if norm_api == norm_hodler:
        return True
    
    # Check if one contains the other
    if norm_api in norm_hodler or norm_hodler in norm_api:
        return True
    
    # Fuzzy match using sequence matcher
    ratio = SequenceMatcher(None, norm_api, norm_hodler).ratio()
    return ratio >= threshold


class APIGlobalSyncAgent:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.portal_url = "https://providerrail.apps-apiglobalsolutions.com/ACESSUPPLIER/faces/login.xhtml"
        self.browser = None
        self.page = None
        self.results = {
            "verified": [],
            "no_bill": [],
            "missing_in_hodler": [],
            "errors": []
        }
    
    async def start(self):
        """Initialize browser."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        logger.info("Browser started")
    
    async def stop(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
    
    async def login(self) -> bool:
        """Login to API Global portal."""
        try:
            logger.info(f"Navigating to {self.portal_url}")
            await self.page.goto(self.portal_url, wait_until="networkidle", timeout=30000)
            
            # Wait for login form
            await self.page.wait_for_selector('input[id*="username"]', timeout=10000)
            
            # Fill credentials
            await self.page.fill('input[id*="username"]', self.username)
            await self.page.fill('input[id*="password"]', self.password)
            
            # Click login button
            await self.page.click('input[type="submit"], button[type="submit"]')
            
            # Wait for navigation
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            
            # Check if login successful by looking for menu or dashboard elements
            try:
                await self.page.wait_for_selector('[id*="menu"], [class*="menu"], [id*="dashboard"]', timeout=5000)
                logger.info("Login successful")
                return True
            except:
                logger.error("Login failed - could not find dashboard elements")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            self.results["errors"].append(f"Login failed: {str(e)}")
            return False
    
    async def navigate_to_signin_sheets(self) -> bool:
        """Navigate to Online Sign-In Sheets."""
        try:
            # Click on Sign In Sheets menu
            await self.page.click('text=Sign In Sheets', timeout=10000)
            await self.page.wait_for_timeout(1000)
            
            # Click on Online Sign In Sheets
            await self.page.click('text=Online Sign In Sheets', timeout=10000)
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            
            logger.info("Navigated to Online Sign In Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            self.results["errors"].append(f"Navigation failed: {str(e)}")
            return False
    
    async def select_date_and_load(self, target_date: datetime = None) -> bool:
        """Select the target date and load sign-in sheets."""
        try:
            if target_date is None:
                # Auto-select date based on current time
                now = datetime.now()
                if now.hour >= 18:  # After 6 PM
                    target_date = now - timedelta(days=1)
                elif now.hour < 15:  # Before 3 PM
                    target_date = now
                else:
                    target_date = now
            
            date_str = target_date.strftime("%m/%d/%Y")
            logger.info(f"Selecting date: {date_str}")
            
            # Find and fill date input
            date_input = await self.page.query_selector('input[id*="date"], input[type="date"]')
            if date_input:
                await date_input.fill(date_str)
            
            # Click Load button
            await self.page.click('text=Load', timeout=10000)
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            await self.page.wait_for_timeout(2000)  # Extra wait for data to load
            
            logger.info("Sign-in sheets loaded")
            return True
            
        except Exception as e:
            logger.error(f"Date selection error: {str(e)}")
            self.results["errors"].append(f"Failed to load sign-in sheets: {str(e)}")
            return False
    
    async def get_signin_sheet_entries(self) -> list:
        """Extract all sign-in sheet entries from the page."""
        entries = []
        try:
            # Find all rows in the sign-in sheet table
            rows = await self.page.query_selector_all('tr[id*="row"], tr[class*="row"], tbody tr')
            
            for row in rows:
                try:
                    # Get name cell
                    name_cell = await row.query_selector('td:nth-child(4), [id*="name"]')
                    if name_cell:
                        name = await name_cell.inner_text()
                        
                        # Get employee ID input
                        emp_input = await row.query_selector('input[id*="employee"], input[id*="empId"]')
                        
                        # Get room number input
                        room_input = await row.query_selector('input[id*="room"]')
                        
                        # Get no bill checkbox
                        no_bill_checkbox = await row.query_selector('input[type="checkbox"][id*="noBill"]')
                        
                        # Get status element
                        status = await row.query_selector('[class*="status"], [id*="status"]')
                        status_text = await status.inner_text() if status else ""
                        
                        entries.append({
                            "name": name.strip(),
                            "emp_input": emp_input,
                            "room_input": room_input,
                            "no_bill_checkbox": no_bill_checkbox,
                            "row": row,
                            "verified": "check" in status_text.lower() or "blue" in status_text.lower()
                        })
                except Exception as e:
                    continue
            
            logger.info(f"Found {len(entries)} sign-in sheet entries")
            return entries
            
        except Exception as e:
            logger.error(f"Error extracting entries: {str(e)}")
            self.results["errors"].append(f"Failed to extract entries: {str(e)}")
            return []
    
    async def verify_entry(self, entry: dict, employee_id: str, room_number: str) -> bool:
        """Fill in employee ID and room number for an entry."""
        try:
            if entry["emp_input"]:
                await entry["emp_input"].fill(employee_id)
            
            if entry["room_input"]:
                await entry["room_input"].fill(room_number)
            
            # Tab out to trigger validation
            await self.page.keyboard.press("Tab")
            await self.page.wait_for_timeout(500)
            
            logger.info(f"Verified: {entry['name']} -> EmpID: {employee_id}, Room: {room_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying entry: {str(e)}")
            return False
    
    async def mark_no_bill(self, entry: dict) -> bool:
        """Mark an entry as No Bill."""
        try:
            if entry["no_bill_checkbox"]:
                await entry["no_bill_checkbox"].check()
                await self.page.wait_for_timeout(500)
                logger.info(f"Marked No Bill: {entry['name']}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error marking no bill: {str(e)}")
            return False
    
    async def run_sync(self, hodler_records: list) -> dict:
        """
        Run the full sync process.
        
        Args:
            hodler_records: List of dicts with 'employee_name', 'employee_number', 'room_number'
        
        Returns:
            Results dict with verified, no_bill, missing entries
        """
        try:
            await self.start()
            
            if not await self.login():
                return self.results
            
            if not await self.navigate_to_signin_sheets():
                return self.results
            
            if not await self.select_date_and_load():
                return self.results
            
            entries = await self.get_signin_sheet_entries()
            
            for entry in entries:
                if entry["verified"]:
                    continue  # Skip already verified entries
                
                api_name = entry["name"]
                matched = False
                
                # Try to match with Hodler Inn records
                for record in hodler_records:
                    if match_names(api_name, record.get("employee_name", "")):
                        # Found a match - fill in the details
                        success = await self.verify_entry(
                            entry,
                            record.get("employee_number", ""),
                            record.get("room_number", "")
                        )
                        if success:
                            self.results["verified"].append({
                                "api_name": api_name,
                                "hodler_name": record.get("employee_name"),
                                "employee_id": record.get("employee_number"),
                                "room": record.get("room_number")
                            })
                        matched = True
                        break
                
                if not matched:
                    # No match found - mark as No Bill
                    if await self.mark_no_bill(entry):
                        self.results["no_bill"].append({"name": api_name})
                    else:
                        self.results["missing_in_hodler"].append({"name": api_name})
            
            # Check for Hodler records not in API Global
            api_names = [normalize_name(e["name"]) for e in entries]
            for record in hodler_records:
                hodler_norm = normalize_name(record.get("employee_name", ""))
                found = any(match_names(api_name, record.get("employee_name", "")) 
                           for api_name in [e["name"] for e in entries])
                if not found:
                    self.results["missing_in_hodler"].append({
                        "name": record.get("employee_name"),
                        "note": "In Hodler Inn but not in API Global - needs to be added"
                    })
            
            return self.results
            
        except Exception as e:
            logger.error(f"Sync error: {str(e)}")
            self.results["errors"].append(str(e))
            return self.results
            
        finally:
            await self.stop()


async def test_connection(username: str, password: str) -> dict:
    """Test connection to API Global portal."""
    agent = APIGlobalSyncAgent(username, password)
    try:
        await agent.start()
        login_success = await agent.login()
        return {
            "success": login_success,
            "message": "Connection successful" if login_success else "Login failed - check credentials"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection error: {str(e)}"
        }
    finally:
        await agent.stop()
