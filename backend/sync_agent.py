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
                    # Try clicking the checkbox
                    await entry["no_bill_checkbox"].click()
                    await self.page.wait_for_timeout(500)
                    
                    # Verify it was checked
                    is_now_checked = await entry["no_bill_checkbox"].is_checked()
                    if not is_now_checked:
                        # Try using check() method as fallback
                        await entry["no_bill_checkbox"].check()
                        await self.page.wait_for_timeout(300)
                        
                logger.info(f"Marked No Bill: {entry['name']}")
                return True
            else:
                # Try to find the checkbox in the row again
                logger.warning(f"No Bill checkbox not found for: {entry['name']}, attempting re-search...")
                
                if entry.get("row"):
                    # Look for any checkbox that might be the "No Bill" one
                    checkboxes = await entry["row"].query_selector_all('input[type="checkbox"]')
                    if len(checkboxes) >= 2:
                        # Second checkbox is typically "No Bill" in this portal
                        no_bill_cb = checkboxes[1]
                        is_checked = await no_bill_cb.is_checked()
                        if not is_checked:
                            await no_bill_cb.click()
                            await self.page.wait_for_timeout(500)
                        logger.info(f"Marked No Bill (fallback): {entry['name']}")
                        return True
                    elif len(checkboxes) == 1:
                        # Only one checkbox, try it
                        await checkboxes[0].click()
                        await self.page.wait_for_timeout(500)
                        logger.info(f"Marked checkbox (single): {entry['name']}")
                        return True
                
                logger.warning(f"Could not find No Bill checkbox for: {entry['name']}")
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


async def collect_employees_from_portal(username: str, password: str) -> dict:
    """
    Collect all employee names and IDs from the Sign-in Report.
    Goes to Sign-in Sheets → Sign-in Report → iterates through multiple billing periods.
    Extracts Crew Id and Crew Name from the report tables.
    """
    agent = APIGlobalSyncAgent(username, password)
    employees = []
    seen_ids = set()
    
    try:
        await agent.start()
        
        # Step 1: Login
        logger.info("="*50)
        logger.info("EMPLOYEE COLLECTION: Step 1 - Logging in...")
        logger.info("="*50)
        if not await agent.login():
            return {
                "success": False,
                "message": "Login failed - check credentials",
                "employees": []
            }
        logger.info("Login successful!")
        
        # Step 2: Navigate to Sign-in Report
        logger.info("="*50)
        logger.info("EMPLOYEE COLLECTION: Step 2 - Navigating to Sign-in Report...")
        logger.info("="*50)
        try:
            await agent.page.wait_for_timeout(2000)
            current_url = agent.page.url
            logger.info(f"Current URL after login: {current_url}")
            
            # Click Sign-in Sheets menu
            signin_menu = None
            for selector in ["a:has-text('Sign-in Sheets')", "span:has-text('Sign-in Sheets')", "text=Sign-in Sheets"]:
                try:
                    elem = agent.page.locator(selector).first
                    if await elem.count() > 0:
                        signin_menu = elem
                        logger.info(f"Found Sign-in Sheets menu with selector: {selector}")
                        break
                except:
                    continue
            
            if signin_menu:
                await signin_menu.click()
                await agent.page.wait_for_timeout(1500)
                logger.info("Clicked Sign-in Sheets menu")
            
            # Click Sign-in Report
            signin_report = None
            for selector in ["a:has-text('Sign-in Report')", "span:has-text('Sign-in Report')", "text=Sign-in Report"]:
                try:
                    elem = agent.page.locator(selector).first
                    if await elem.count() > 0:
                        signin_report = elem
                        logger.info(f"Found Sign-in Report with selector: {selector}")
                        break
                except:
                    continue
            
            if signin_report:
                await signin_report.click()
                await agent.page.wait_for_load_state("networkidle", timeout=30000)
                await agent.page.wait_for_timeout(2000)
                logger.info("Clicked on Sign-in Report - page loaded")
            else:
                return {"success": False, "message": "Failed to navigate to Sign-in Report", "employees": []}
                
        except Exception as e:
            logger.error(f"Failed to navigate to Sign-in Report: {e}")
            return {"success": False, "message": f"Navigation failed: {str(e)}", "employees": []}
        
        # Step 3: Get all available billing periods and process each
        logger.info("="*50)
        logger.info("EMPLOYEE COLLECTION: Step 3 - Processing billing periods...")
        logger.info("="*50)
        
        try:
            await agent.page.wait_for_timeout(1000)
            
            # Find the billing period dropdown
            billing_dropdown = agent.page.locator("select[id*='billingPeriod'], select[name*='billingPeriod']").first
            if await billing_dropdown.count() == 0:
                # Fallback to second select (first is usually client)
                selects = agent.page.locator("select")
                if await selects.count() > 1:
                    billing_dropdown = selects.nth(1)
                else:
                    billing_dropdown = selects.first
            
            options = await billing_dropdown.locator("option").all()
            logger.info(f"Found {len(options)} billing period options")
            
            # List all options
            billing_periods = []
            for idx, opt in enumerate(options):
                opt_text = await opt.inner_text()
                opt_value = await opt.get_attribute("value") or ""
                if opt_value and opt_value != "" and "-Select-" not in opt_text:
                    billing_periods.append((opt_value, opt_text))
                    logger.info(f"  Period {idx}: {opt_text}")
            
            # Process up to 6 months of data (to get comprehensive employee list)
            max_periods = min(len(billing_periods), 6)
            logger.info(f"Will process {max_periods} billing periods")
            
            for period_idx, (period_value, period_text) in enumerate(billing_periods[:max_periods]):
                logger.info(f"\n--- Processing period {period_idx + 1}/{max_periods}: {period_text} ---")
                
                try:
                    # First, make sure we're on the Sign-in Report page
                    # Check if billing dropdown is available
                    current_url = agent.page.url
                    if "viewSignInReport" not in current_url:
                        logger.info("Navigating back to Sign-in Report page...")
                        # Navigate to Sign-in Report page again
                        signin_menu = agent.page.locator("a:has-text('Sign-in Sheets')").first
                        if await signin_menu.count() > 0:
                            await signin_menu.click()
                            await agent.page.wait_for_timeout(1000)
                        signin_report = agent.page.locator("a:has-text('Sign-in Report')").first
                        if await signin_report.count() > 0:
                            await signin_report.click()
                            await agent.page.wait_for_load_state("networkidle", timeout=30000)
                            await agent.page.wait_for_timeout(1500)
                    
                    # Re-find the billing dropdown after potential navigation
                    billing_dropdown = agent.page.locator("select[id*='billingPeriod'], select[name*='billingPeriod']").first
                    if await billing_dropdown.count() == 0:
                        selects = agent.page.locator("select")
                        if await selects.count() > 1:
                            billing_dropdown = selects.nth(1)
                        elif await selects.count() > 0:
                            billing_dropdown = selects.first
                        else:
                            logger.warning(f"Could not find billing dropdown for period {period_text}")
                            continue
                    
                    # Select the billing period
                    await billing_dropdown.select_option(value=period_value, timeout=10000)
                    await agent.page.wait_for_timeout(500)
                    
                    # Click Create button
                    create_btn = agent.page.locator("button:has-text('Create'), input[value='Create']").first
                    if await create_btn.count() > 0:
                        await create_btn.click()
                        await agent.page.wait_for_load_state("networkidle", timeout=60000)
                        await agent.page.wait_for_timeout(2000)
                        logger.info(f"Report loaded for {period_text}")
                    
                    # Extract employees from this period's report
                    period_employees = await extract_employees_from_report_table(agent.page, seen_ids)
                    employees.extend(period_employees)
                    logger.info(f"Found {len(period_employees)} new employees in {period_text}")
                    
                except Exception as period_err:
                    logger.warning(f"Error processing period {period_text}: {period_err}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing billing periods: {e}")
        
        logger.info("="*50)
        logger.info(f"EMPLOYEE COLLECTION COMPLETE: Found {len(employees)} unique employees")
        logger.info("="*50)
        
        return {
            "success": len(employees) > 0,
            "message": f"Found {len(employees)} unique employees" if employees else "No employees found",
            "employees": employees
        }
        
    except Exception as e:
        logger.error(f"Error collecting employees: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"Error: {str(e)}", "employees": []}
    finally:
        await agent.stop()


async def extract_employees_from_report_table(page, seen_ids: set) -> list:
    """Extract employee data from the Sign-in Report table or by clicking View Details links."""
    employees = []
    
    try:
        # First, try to find direct employee data in summary table
        tables = await page.locator("table").all()
        
        for table in tables:
            header_row = table.locator("tr").first
            header_text = await header_row.inner_text()
            header_lower = header_text.lower()
            
            if "crewid" not in header_lower and "crew id" not in header_lower:
                continue
            
            logger.info(f"Found employee data table with header: {header_text[:80]}...")
            
            rows = await table.locator("tr").all()
            header_cells = await header_row.locator("th, td").all()
            
            # Find column positions
            crew_id_col = -1
            crew_name_col = -1
            
            for idx, cell in enumerate(header_cells):
                cell_text = (await cell.inner_text()).strip().lower()
                if "crewid" in cell_text or "crew id" in cell_text:
                    crew_id_col = idx
                elif "crew name" in cell_text or "crewname" in cell_text or ("name" in cell_text and crew_name_col == -1):
                    crew_name_col = idx
            
            if crew_id_col >= 0:
                logger.info(f"CrewId column: {crew_id_col}, Crew Name column: {crew_name_col}")
                
                for row_idx, row in enumerate(rows[1:], start=1):
                    try:
                        cells = await row.locator("td").all()
                        if len(cells) <= crew_id_col:
                            continue
                        
                        crew_id = (await cells[crew_id_col].inner_text()).strip()
                        
                        # Skip if ID is empty or invalid
                        if not crew_id or crew_id == "" or crew_id == "NO ID":
                            continue
                        if crew_id in seen_ids:
                            continue
                        if ":" in crew_id or len(crew_id) > 15:
                            continue
                        if not crew_id.replace('-', '').replace(' ', '').replace('.', '').isalnum():
                            continue
                        
                        # Get crew name
                        crew_name = ""
                        if crew_name_col >= 0 and len(cells) > crew_name_col:
                            crew_name = (await cells[crew_name_col].inner_text()).strip()
                        elif len(cells) > 1:
                            crew_name = (await cells[1].inner_text()).strip()
                        
                        # Skip if name is empty or too short
                        if not crew_name or crew_name == "" or len(crew_name) < 2:
                            logger.info(f"  Skipping row {row_idx}: ID={crew_id} has no valid name")
                            continue
                        
                        # Valid employee found
                        seen_ids.add(crew_id)
                        formatted_name = format_crew_name(crew_name)
                        employees.append({
                            "employee_number": crew_id,
                            "name": formatted_name,
                            "original_name": crew_name
                        })
                        logger.info(f"  Employee: ID={crew_id}, Name={formatted_name}")
                            
                    except Exception as row_err:
                        continue
            break
        
        # If no employees found in summary table, try View Details links
        if len(employees) == 0:
            logger.info("No employees in summary table - looking for View Details links...")
            
            view_links = page.locator("a:has-text('View Details'), a:has-text('View'), [class*='view']")
            link_count = await view_links.count()
            logger.info(f"Found {link_count} View Details links")
            
            if link_count > 0:
                # Process each View Details link
                max_links = min(link_count, 15)  # Limit to avoid timeout
                
                for i in range(max_links):
                    try:
                        # Re-find links (DOM may have changed)
                        view_links = page.locator("a:has-text('View Details'), a:has-text('View')")
                        current_count = await view_links.count()
                        
                        if i >= current_count:
                            break
                        
                        link = view_links.nth(i)
                        link_text = await link.inner_text()
                        logger.info(f"Clicking View Details link {i+1}/{max_links}: {link_text[:30]}...")
                        
                        await link.click()
                        await page.wait_for_load_state("networkidle", timeout=30000)
                        await page.wait_for_timeout(1500)
                        
                        # Extract from detail page
                        detail_employees = await extract_from_detail_page(page, seen_ids)
                        employees.extend(detail_employees)
                        logger.info(f"  Found {len(detail_employees)} employees from View Details")
                        
                        # Go back - this may put us on a different page after multiple periods
                        await page.go_back()
                        await page.wait_for_load_state("networkidle", timeout=30000)
                        await page.wait_for_timeout(1000)
                        
                    except Exception as link_err:
                        logger.warning(f"Error processing View Details link {i}: {link_err}")
                        try:
                            await page.go_back()
                            await page.wait_for_timeout(1000)
                        except:
                            pass
                        continue
            
    except Exception as e:
        logger.error(f"Error extracting from report table: {e}")
    
    return employees


async def extract_from_detail_page(page, seen_ids: set) -> list:
    """Extract employee data from a View Details page."""
    employees = []
    
    try:
        # Wait for content to load
        await page.wait_for_timeout(500)
        
        # Find tables with employee data
        tables = await page.locator("table").all()
        
        for table in tables:
            # Check header for crew data indicators
            try:
                header_row = table.locator("tr").first
                header_text = await header_row.inner_text()
                header_lower = header_text.lower()
                
                # Look for tables with Crew Id / Employee ID columns
                if "crew" in header_lower or "employee" in header_lower or "id" in header_lower:
                    rows = await table.locator("tr").all()
                    logger.info(f"  Detail table has {len(rows)} rows, header: {header_text[:60]}...")
                    
                    for row in rows[1:]:  # Skip header
                        try:
                            cells = await row.locator("td").all()
                            if len(cells) < 2:
                                continue
                            
                            # Get cell texts
                            cell_texts = []
                            for cell in cells:
                                text = (await cell.inner_text()).strip()
                                cell_texts.append(text)
                            
                            # Try to identify crew_id and crew_name
                            crew_id = None
                            crew_name = None
                            
                            # Usually first column is ID, second is name
                            if len(cell_texts) >= 2:
                                potential_id = cell_texts[0].strip()
                                potential_name = cell_texts[1].strip()
                                
                                # Skip if both are empty
                                if not potential_id and not potential_name:
                                    continue
                                
                                # Skip if ID is empty or invalid
                                if not potential_id or potential_id == "NO ID" or potential_id == "":
                                    continue
                                    
                                # Validate ID format (alphanumeric, reasonable length)
                                if len(potential_id) <= 15 and potential_id.replace('-', '').replace('.', '').replace(' ', '').isalnum():
                                    if potential_id not in seen_ids and ":" not in potential_id:
                                        # Only add if we have a valid name too
                                        if potential_name and potential_name != "" and len(potential_name) > 1:
                                            crew_id = potential_id
                                            crew_name = potential_name
                            
                            if crew_id and crew_name:
                                seen_ids.add(crew_id)
                                formatted_name = format_crew_name(crew_name)
                                employees.append({
                                    "employee_number": crew_id,
                                    "name": formatted_name,
                                    "original_name": crew_name
                                })
                                
                        except Exception as row_err:
                            continue
                            
            except Exception as table_err:
                continue
                
    except Exception as e:
        logger.error(f"Error extracting from detail page: {e}")
    
    return employees


def format_crew_name(crew_name: str) -> str:
    """Parse and format crew name from portal format to readable format."""
    if not crew_name:
        return ""
    
    # Parse name format: LASTNAME,(FIRSTNAME)SUFFIX or LASTNAME/FIRSTNAME/SUFFIX
    # Example: ABERNATHY,(JOHN)HBW E or SMITH/JOHN/BMR
    
    # Try format: LASTNAME,(FIRSTNAME)SUFFIX
    name_match = re.match(r'([A-Z]+),\(([A-Z]+)\)', crew_name.upper())
    if name_match:
        last_name = name_match.group(1).title()
        first_name = name_match.group(2).title()
        return f"{first_name} {last_name}"
    
    # Try format: LASTNAME/FIRSTNAME or LASTNAME/FIRSTNAME/SUFFIX
    parts = crew_name.replace(',', '/').split('/')
    if len(parts) >= 2:
        last_name = parts[0].strip().title()
        # Remove suffix from firstname (e.g., "JOHN*BMR" -> "JOHN")
        first_name = re.sub(r'[^A-Za-z\s].*', '', parts[1]).strip().title()
        if first_name and last_name:
            return f"{first_name} {last_name}"
    
    # Fallback: just title case the whole thing
    return crew_name.title()
