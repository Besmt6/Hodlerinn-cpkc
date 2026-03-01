"""
API Global Portal Sync Agent
Automates verification of railroad crew sign-in sheets
Portal: providerrail.apps-apiglobalsolutions.com
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
    # Remove common suffixes like BMR, HBW, MBW, HUB R E, etc.
    name = re.sub(r'[/*][A-Z\s]{2,10}\s*$', '', name.strip())
    name = re.sub(r'/[A-Z]{2,4}\s*$', '', name.strip())
    # Convert LASTNAME/FIRSTNAME format to "firstname lastname"
    parts = name.split('/')
    if len(parts) >= 2:
        # Format: LASTNAME/FIRSTNAME or LASTNAME/FIRSTNAME/SUFFIX
        lastname = parts[0].strip()
        firstname = parts[1].strip()
        # Remove any remaining suffix from firstname
        firstname = re.sub(r'[/*].*$', '', firstname).strip()
        return f"{firstname} {lastname}".lower()
    return name.lower().strip()


def match_names(api_name: str, hodler_name: str, threshold: float = 0.6) -> bool:
    """Check if two names match using fuzzy matching."""
    norm_api = normalize_name(api_name)
    norm_hodler = normalize_name(hodler_name)
    
    if not norm_api or not norm_hodler:
        return False
    
    # Exact match
    if norm_api == norm_hodler:
        return True
    
    # Check if one contains the other
    if norm_api in norm_hodler or norm_hodler in norm_api:
        return True
    
    # Check individual name parts
    api_parts = set(norm_api.split())
    hodler_parts = set(norm_hodler.split())
    if api_parts and hodler_parts:
        # If both first and last name match (in any order)
        if len(api_parts & hodler_parts) >= 2:
            return True
        # If at least one significant name part matches
        if len(api_parts & hodler_parts) >= 1:
            # Use fuzzy match for additional confirmation
            ratio = SequenceMatcher(None, norm_api, norm_hodler).ratio()
            if ratio >= 0.5:
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
        self.context = None
        self.page = None
        self.playwright = None
        self.results = {
            "verified": [],
            "no_bill": [],
            "missing_in_hodler": [],
            "errors": []
        }
    
    async def start(self):
        """Initialize browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await self.context.new_page()
        logger.info("Browser started")
    
    async def stop(self):
        """Close browser."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    async def login(self) -> bool:
        """Login to API Global portal."""
        try:
            logger.info(f"Navigating to {self.portal_url}")
            await self.page.goto(self.portal_url, wait_until="networkidle", timeout=30000)
            
            # Wait for login form - look for username input
            await self.page.wait_for_selector('input[type="text"]', timeout=10000)
            
            # Fill credentials - the form has simple text/password inputs
            username_input = self.page.locator('input[type="text"]').first
            password_input = self.page.locator('input[type="password"]').first
            
            await username_input.fill(self.username)
            await password_input.fill(self.password)
            
            # Click Login button
            login_button = self.page.locator('input[type="submit"][value="Login"], button:has-text("Login")').first
            await login_button.click()
            
            # Wait for navigation to complete
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            await self.page.wait_for_timeout(2000)
            
            # Check if login successful by looking for the welcome message or menu
            try:
                # After login, we should see "Welcome" text or the sidebar menu
                await self.page.wait_for_selector('text=Welcome, text=Sign-in Sheets, text=Home', timeout=8000)
                logger.info("Login successful")
                return True
            except:
                # Check if we're still on login page (login failed)
                current_url = self.page.url
                if "login" in current_url.lower():
                    logger.error("Login failed - still on login page")
                    return False
                # Might have succeeded anyway
                logger.info("Login appears successful (navigated away from login)")
                return True
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            self.results["errors"].append(f"Login failed: {str(e)}")
            return False
    
    async def navigate_to_signin_sheets(self) -> bool:
        """Navigate to Online Sign-In Sheets page."""
        try:
            logger.info("Navigating to Sign-in Sheets...")
            
            # Wait for page to be ready
            await self.page.wait_for_timeout(1000)
            
            # Click on "Sign-in Sheets" in the left sidebar menu (it's expandable)
            signin_menu = self.page.locator('text=Sign-in Sheets').first
            await signin_menu.click()
            await self.page.wait_for_timeout(1500)
            
            logger.info("Clicked Sign-in Sheets menu")
            
            # Now click on "Online Sign-in Sheets" submenu
            online_signin = self.page.locator('text=Online Sign-in Sheets').first
            await online_signin.click()
            
            # Wait for the page to load
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            await self.page.wait_for_timeout(2000)
            
            # Verify we're on the right page by checking for "Enter Online Sign-In Sheets" header
            try:
                await self.page.wait_for_selector('text=Enter Online Sign-In Sheets', timeout=5000)
                logger.info("Navigated to Online Sign-In Sheets page")
                return True
            except:
                logger.info("Navigation completed (page loaded)")
                return True
            
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            self.results["errors"].append(f"Navigation failed: {str(e)}")
            return False
    
    async def load_signin_sheet(self) -> bool:
        """Click Load button to load the sign-in sheet data."""
        try:
            logger.info("Loading sign-in sheet data...")
            
            # The page should show:
            # - Select Client: Canadian Pacific (dropdown)
            # - City: HEAVENER-OK
            # - Supplier: Hodler Inn - Heavener
            # - Reservation Date: [date] (auto-set to previous day)
            # - Load button
            
            # Just click the Load button - date should already be correct (previous day before 3pm)
            load_button = self.page.locator('input[type="submit"][value="Load"], button:has-text("Load")').first
            await load_button.click()
            
            # Wait for data to load
            await self.page.wait_for_load_state("networkidle", timeout=20000)
            await self.page.wait_for_timeout(3000)
            
            # Check if "Scheduled Arrivals" section appeared
            try:
                await self.page.wait_for_selector('text=Scheduled Arrivals', timeout=10000)
                logger.info("Sign-in sheet data loaded successfully")
                return True
            except:
                logger.warning("Could not find Scheduled Arrivals - page may be empty or different structure")
                return True
            
        except Exception as e:
            logger.error(f"Load error: {str(e)}")
            self.results["errors"].append(f"Failed to load sign-in sheet: {str(e)}")
            return False
    
    async def get_signin_sheet_entries(self) -> list:
        """Extract all sign-in sheet entries from the Scheduled Arrivals section."""
        entries = []
        try:
            logger.info("Extracting sign-in sheet entries...")
            
            # The page structure shows multiple arrival blocks, each with a data table
            # Each block has: Name, Employee ID input, No Show/No Bill checkboxes, Room Number input
            
            # Find all table rows that contain employee data
            # Looking for rows with Name column and Employee ID input
            
            # Get all tables in the Scheduled Arrivals section
            tables = await self.page.query_selector_all('table')
            
            for table in tables:
                rows = await table.query_selector_all('tr')
                for row in rows:
                    try:
                        # Look for rows that have a Name cell and Employee ID input
                        cells = await row.query_selector_all('td')
                        if len(cells) < 4:
                            continue
                        
                        # Try to find the name - it's usually in format LASTNAME/FIRSTNAME/SUFFIX
                        name_text = None
                        emp_input = None
                        room_input = None
                        no_bill_checkbox = None
                        
                        for cell in cells:
                            cell_text = await cell.inner_text()
                            cell_text = cell_text.strip()
                            
                            # Check if this looks like a name (contains /)
                            if '/' in cell_text and len(cell_text) > 3:
                                # This is likely the name column
                                name_text = cell_text
                        
                        # Find Employee ID input in this row
                        emp_input = await row.query_selector('input[id*="employeeId"], input[id*="empId"], input[name*="employee"]')
                        if not emp_input:
                            # Try finding any text input that might be for employee ID
                            inputs = await row.query_selector_all('input[type="text"]')
                            for inp in inputs:
                                placeholder = await inp.get_attribute('placeholder') or ''
                                value = await inp.get_attribute('value') or ''
                                inp_id = await inp.get_attribute('id') or ''
                                if 'employee' in inp_id.lower() or 'emp' in inp_id.lower() or value == 'NO ID':
                                    emp_input = inp
                                    break
                        
                        # Find Room Number input
                        room_input = await row.query_selector('input[id*="room"], input[name*="room"]')
                        if not room_input:
                            inputs = await row.query_selector_all('input[type="text"]')
                            for inp in inputs:
                                inp_id = await inp.get_attribute('id') or ''
                                inp_name = await inp.get_attribute('name') or ''
                                if 'room' in inp_id.lower() or 'room' in inp_name.lower():
                                    room_input = inp
                                    break
                        
                        # Find No Bill checkbox - look for checkbox near "No Bill" label text
                        # The portal uses JSF so checkbox IDs may be dynamically generated
                        no_bill_checkbox = await row.query_selector('input[type="checkbox"][id*="noBill"], input[type="checkbox"][name*="noBill"]')
                        if not no_bill_checkbox:
                            # Try finding by looking for cell with "No Bill" text and nearby checkbox
                            for cell in cells:
                                cell_text = await cell.inner_text()
                                if 'no bill' in cell_text.lower():
                                    # Found the No Bill cell, look for checkbox in this cell or nearby
                                    no_bill_checkbox = await cell.query_selector('input[type="checkbox"]')
                                    if no_bill_checkbox:
                                        break
                        
                        if not no_bill_checkbox:
                            # Try finding all checkboxes and match by position/context
                            checkboxes = await row.query_selector_all('input[type="checkbox"]')
                            # In the portal structure, "No Show" is first, "No Bill" is second checkbox
                            if len(checkboxes) >= 2:
                                no_bill_checkbox = checkboxes[1]  # Second checkbox is typically "No Bill"
                            elif len(checkboxes) == 1:
                                # If only one checkbox, check its ID/name
                                cb_id = await checkboxes[0].get_attribute('id') or ''
                                cb_name = await checkboxes[0].get_attribute('name') or ''
                                if 'nobill' in cb_id.lower() or 'nobill' in cb_name.lower() or 'bill' in cb_id.lower():
                                    no_bill_checkbox = checkboxes[0]
                        
                        if name_text:
                            # Check if already verified (has employee ID filled in)
                            emp_value = ""
                            if emp_input:
                                emp_value = await emp_input.get_attribute('value') or ''
                            
                            is_verified = emp_value and emp_value != 'NO ID' and len(emp_value) > 2
                            
                            entries.append({
                                "name": name_text,
                                "emp_input": emp_input,
                                "room_input": room_input,
                                "no_bill_checkbox": no_bill_checkbox,
                                "row": row,
                                "verified": is_verified,
                                "current_emp_value": emp_value
                            })
                            logger.info(f"Found entry: {name_text} (verified: {is_verified})")
                    
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
                await entry["emp_input"].clear()
                await entry["emp_input"].fill(str(employee_id))
                await self.page.wait_for_timeout(300)
            
            if entry["room_input"]:
                await entry["room_input"].clear()
                await entry["room_input"].fill(str(room_number))
                await self.page.wait_for_timeout(300)
            
            # Tab out to trigger any validation
            await self.page.keyboard.press("Tab")
            await self.page.wait_for_timeout(500)
            
            logger.info(f"Verified: {entry['name']} -> EmpID: {employee_id}, Room: {room_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying entry {entry['name']}: {str(e)}")
            return False
    
    async def mark_no_bill(self, entry: dict) -> bool:
        """Mark an entry as No Bill (guest didn't stay)."""
        try:
            if entry["no_bill_checkbox"]:
                # Check if already checked
                is_checked = await entry["no_bill_checkbox"].is_checked()
                if not is_checked:
                    await entry["no_bill_checkbox"].check()
                    await self.page.wait_for_timeout(500)
                logger.info(f"Marked No Bill: {entry['name']}")
                return True
            else:
                logger.warning(f"No Bill checkbox not found for: {entry['name']}")
                return False
            
        except Exception as e:
            logger.error(f"Error marking no bill for {entry['name']}: {str(e)}")
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
            
            # Step 1: Login
            if not await self.login():
                return self.results
            
            # Step 2: Navigate to Sign-in Sheets > Online Sign-in Sheets
            if not await self.navigate_to_signin_sheets():
                return self.results
            
            # Step 3: Click Load to get the data
            if not await self.load_signin_sheet():
                return self.results
            
            # Step 4: Get all entries from the table
            entries = await self.get_signin_sheet_entries()
            
            if not entries:
                logger.info("No entries found to process")
                self.results["errors"].append("No entries found on the sign-in sheet")
                return self.results
            
            # Step 5: Process each entry
            for entry in entries:
                if entry["verified"]:
                    logger.info(f"Skipping already verified: {entry['name']}")
                    continue
                
                api_name = entry["name"]
                matched = False
                
                # Try to match with Hodler Inn records
                for record in hodler_records:
                    hodler_name = record.get("employee_name", "")
                    if match_names(api_name, hodler_name):
                        # Found a match - fill in the details
                        logger.info(f"Match found: {api_name} <-> {hodler_name}")
                        success = await self.verify_entry(
                            entry,
                            record.get("employee_number", ""),
                            record.get("room_number", "")
                        )
                        if success:
                            self.results["verified"].append({
                                "api_name": api_name,
                                "hodler_name": hodler_name,
                                "employee_id": record.get("employee_number"),
                                "room": record.get("room_number")
                            })
                        matched = True
                        break
                
                if not matched:
                    # No match found in Hodler Inn records - mark as No Bill
                    logger.info(f"No match for {api_name} - marking No Bill")
                    if await self.mark_no_bill(entry):
                        self.results["no_bill"].append({"name": api_name})
                    else:
                        self.results["missing_in_hodler"].append({"name": api_name})
            
            # Check for Hodler records not found in API Global (guests who stayed but not in system)
            for record in hodler_records:
                hodler_name = record.get("employee_name", "")
                found = any(match_names(e["name"], hodler_name) for e in entries)
                if not found:
                    self.results["missing_in_hodler"].append({
                        "name": hodler_name,
                        "employee_id": record.get("employee_number"),
                        "room": record.get("room_number"),
                        "note": "Guest checked in at Hodler Inn but not listed in API Global portal"
                    })
            
            logger.info(f"Sync completed. Verified: {len(self.results['verified'])}, No Bill: {len(self.results['no_bill'])}")
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
