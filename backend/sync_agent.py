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
    """Normalize name for matching - remove suffixes, lowercase, handle various formats."""
    if not name:
        return ""
    
    # Remove common suffixes like BMR, HBW, MBW, HUB R E, *, etc.
    name = re.sub(r'[/*][A-Z\s]{2,10}\s*$', '', name.strip())
    name = re.sub(r'/[A-Z]{2,4}\s*$', '', name.strip())
    name = re.sub(r'\s+[A-Z]{1,2}\s*$', '', name.strip())  # Remove single letter suffixes like " E"
    
    # Handle LASTNAME (FIRSTNAME) format - with space before parentheses (NO COMMA)
    # Example: "SMITH (JOHN)" -> "john smith"
    paren_space_match = re.match(r'^([A-Za-z]+)\s+\(([^)]+)\)', name.strip())
    if paren_space_match:
        lastname = paren_space_match.group(1).strip()
        firstname = paren_space_match.group(2).strip()
        # Remove any suffixes from firstname
        firstname = re.sub(r'[/*].*$', '', firstname).strip()
        firstname = re.sub(r'\s+[A-Z]+$', '', firstname).strip()
        logger.info(f"Normalized '{name}' -> '{firstname} {lastname}' (LASTNAME (FIRSTNAME) format)")
        return f"{firstname} {lastname}".lower()
    
    # Handle LASTNAME,(FIRSTNAME) format with comma and parentheses
    # Example: "SMITH,(JOHN)" -> "john smith"
    paren_match = re.match(r'^([A-Z]+),\s*\(([^)]+)\)', name, re.IGNORECASE)
    if paren_match:
        lastname = paren_match.group(1).strip()
        firstname = paren_match.group(2).strip()
        # Remove any suffixes from firstname
        firstname = re.sub(r'[/*].*$', '', firstname).strip()
        firstname = re.sub(r'\s+[A-Z]+$', '', firstname).strip()
        logger.info(f"Normalized '{name}' -> '{firstname} {lastname}' (LASTNAME,(FIRSTNAME) format)")
        return f"{firstname} {lastname}".lower()
    
    # Handle LASTNAME/FIRSTNAME format with slash
    # Example: "SMITH/JOHN" -> "john smith"
    parts = name.split('/')
    if len(parts) >= 2:
        # Format: LASTNAME/FIRSTNAME or LASTNAME/FIRSTNAME/SUFFIX
        lastname = parts[0].strip()
        firstname = parts[1].strip()
        # Remove any remaining suffix from firstname
        firstname = re.sub(r'[/*].*$', '', firstname).strip()
        logger.info(f"Normalized '{name}' -> '{firstname} {lastname}' (LASTNAME/FIRSTNAME format)")
        return f"{firstname} {lastname}".lower()
    
    # Handle "Firstname Lastname" format (already normal)
    return name.lower().strip()


def match_names(api_name: str, hodler_name: str, threshold: float = 0.6) -> bool:
    """Check if two names match using strict matching to avoid wrong employee ID assignment."""
    norm_api = normalize_name(api_name)
    norm_hodler = normalize_name(hodler_name)
    
    logger.info(f"Normalized: '{api_name}' -> '{norm_api}' | '{hodler_name}' -> '{norm_hodler}'")
    
    if not norm_api or not norm_hodler:
        return False
    
    # Exact match
    if norm_api == norm_hodler:
        logger.info(f"EXACT MATCH: {norm_api}")
        return True
    
    # Split into parts for comparison
    api_parts = norm_api.split()
    hodler_parts = norm_hodler.split()
    
    if len(api_parts) < 2 or len(hodler_parts) < 2:
        # If either name has less than 2 parts, require exact match
        return norm_api == norm_hodler
    
    # Get first and last names (first word = first name, last word = last name after normalization)
    api_first = api_parts[0]
    api_last = api_parts[-1]
    hodler_first = hodler_parts[0]
    hodler_last = hodler_parts[-1]
    
    # STRICT MATCHING: Both first AND last name must match closely
    # Last names must match exactly or be very similar
    last_name_match = (api_last == hodler_last) or (
        SequenceMatcher(None, api_last, hodler_last).ratio() >= 0.85
    )
    
    # First names must match exactly or be very similar
    first_name_match = (api_first == hodler_first) or (
        SequenceMatcher(None, api_first, hodler_first).ratio() >= 0.80
    )
    
    if last_name_match and first_name_match:
        logger.info(f"STRICT MATCH: first='{api_first}'=='{hodler_first}', last='{api_last}'=='{hodler_last}'")
        return True
    
    # FALLBACK: Try comparing with last name first, first name second (reverse order)
    # This handles cases where portal shows "Last First" and DB has "First Last"
    reversed_first_match = (api_first == hodler_last) or (
        SequenceMatcher(None, api_first, hodler_last).ratio() >= 0.80
    )
    reversed_last_match = (api_last == hodler_first) or (
        SequenceMatcher(None, api_last, hodler_first).ratio() >= 0.85
    )
    
    if reversed_first_match and reversed_last_match:
        logger.info(f"REVERSED MATCH: '{api_first}'=='{hodler_last}', '{api_last}'=='{hodler_first}'")
        return True
    
    # FALLBACK 2: Overall string similarity (for edge cases)
    overall_ratio = SequenceMatcher(None, norm_api, norm_hodler).ratio()
    if overall_ratio >= 0.85:
        logger.info(f"OVERALL SIMILARITY MATCH: {overall_ratio:.2f}")
        return True
    
    # Log why it didn't match
    if last_name_match and not first_name_match:
        logger.info(f"NO MATCH: Last name matched but first name didn't: '{api_first}' != '{hodler_first}'")
    elif first_name_match and not last_name_match:
        logger.info(f"NO MATCH: First name matched but last name didn't: '{api_last}' != '{hodler_last}'")
    
    return False


def find_best_matches(api_name: str, hodler_employees: list, top_n: int = 3) -> list:
    """Find the best possible matches for a name, even if they don't meet threshold."""
    norm_api = normalize_name(api_name)
    if not norm_api:
        return []
    
    scores = []
    for emp in hodler_employees:
        hodler_name = emp.get("name", "")
        norm_hodler = normalize_name(hodler_name)
        if not norm_hodler:
            continue
        
        # Calculate overall similarity
        overall = SequenceMatcher(None, norm_api, norm_hodler).ratio()
        
        # Also check part-by-part matching
        api_parts = norm_api.split()
        hodler_parts = norm_hodler.split()
        
        first_score = 0
        last_score = 0
        if len(api_parts) >= 2 and len(hodler_parts) >= 2:
            first_score = SequenceMatcher(None, api_parts[0], hodler_parts[0]).ratio()
            last_score = SequenceMatcher(None, api_parts[-1], hodler_parts[-1]).ratio()
        
        scores.append({
            "employee_number": emp.get("employee_number"),
            "name": hodler_name,
            "normalized": norm_hodler,
            "overall_score": overall,
            "first_name_score": first_score,
            "last_name_score": last_score,
            "combined_score": (first_score + last_score) / 2
        })
    
    # Sort by combined score (first + last name matching)
    scores.sort(key=lambda x: x["combined_score"], reverse=True)
    return scores[:top_n]


SYNC_AGENT_VERSION = "2026-03-08-v14"  # Fixed Playwright timeout - use .all() instead of .nth() in loops

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
        try:
            self.playwright = await async_playwright().start()
            # Use headless mode with additional flags
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox', 
                    '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security'
                ]
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            self.page = await self.context.new_page()
            logger.info("Browser started successfully")
        except Exception as e:
            logger.error(f"Failed to start browser: {str(e)}")
            raise Exception(f"Browser initialization failed: {str(e)}. Make sure Playwright browsers are installed.")
    
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
    
    async def load_signin_sheet(self, target_date: str = None) -> bool:
        """Click Load button to load the sign-in sheet data.
        
        Args:
            target_date: Optional date in format 'MM/DD/YYYY' or 'YYYY-MM-DD'. 
                        If not provided, uses the portal's default (previous day).
        """
        try:
            logger.info("Loading sign-in sheet data...")
            
            # The page should show:
            # - Select Client: Canadian Pacific (dropdown)
            # - City: HEAVENER-OK
            # - Supplier: Hodler Inn - Heavener
            # - Reservation Date: [date] (auto-set to previous day)
            # - Load button
            
            # If a target date is provided, set it before clicking Load
            if target_date:
                # Convert YYYY-MM-DD to "DD Mon YYYY" format (e.g., "01 Mar 2026")
                # PrimeFaces date picker expects this format
                if '-' in target_date and len(target_date) == 10:
                    from datetime import datetime as dt
                    date_obj = dt.strptime(target_date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%d %b %Y")  # e.g., "01 Mar 2026"
                else:
                    formatted_date = target_date
                
                logger.info(f"Setting date to: {formatted_date}")
                
                # Find the date input field - look for common patterns in JSF/PrimeFaces
                date_selectors = [
                    'input[id*="reservationDate"]',
                    'input[id*="date"]',
                    'input[class*="ui-inputfield"]',
                    'input[type="text"][size="10"]',
                    'input.hasDatepicker',
                    'span.ui-calendar input'
                ]
                
                date_input = None
                date_input_selector = None
                for selector in date_selectors:
                    try:
                        date_input = self.page.locator(selector).first
                        if await date_input.count() > 0:
                            logger.info(f"Found date input with selector: {selector}")
                            date_input_selector = selector
                            break
                    except:
                        continue
                
                if date_input:
                    try:
                        # === CRITICAL FIX: Use JavaScript to properly set date and trigger events ===
                        # PrimeFaces/JSF date pickers require JavaScript events to be triggered
                        # Simply using fill() doesn't trigger the necessary change events
                        
                        # Get the input element's ID for JavaScript interaction
                        input_id = await date_input.get_attribute('id')
                        logger.info(f"Date input ID: {input_id}")
                        
                        # First, click on the input to focus it
                        await date_input.click()
                        await self.page.wait_for_timeout(300)
                        
                        # Clear the field first
                        await date_input.fill('')
                        await self.page.wait_for_timeout(200)
                        
                        # Method 1: Try using JavaScript to set value and trigger all necessary events
                        date_set_success = await self.page.evaluate('''
                            (args) => {
                                const { selector, inputId, formattedDate } = args;
                                
                                // Try to find the input element
                                let input = document.querySelector(selector);
                                if (!input && inputId) {
                                    input = document.getElementById(inputId);
                                }
                                
                                if (!input) {
                                    console.log('Date input not found');
                                    return { success: false, error: 'Input not found' };
                                }
                                
                                console.log('Found date input:', input.id, 'Current value:', input.value);
                                
                                // Focus the input first
                                input.focus();
                                
                                // Clear and set the value
                                input.value = '';
                                input.value = formattedDate;
                                
                                // Create and dispatch events with all necessary properties
                                const focusEvent = new FocusEvent('focus', { bubbles: true, cancelable: true });
                                const inputEvent = new InputEvent('input', { bubbles: true, cancelable: true, data: formattedDate });
                                const changeEvent = new Event('change', { bubbles: true, cancelable: true });
                                const blurEvent = new FocusEvent('blur', { bubbles: true, cancelable: true });
                                
                                input.dispatchEvent(focusEvent);
                                input.dispatchEvent(inputEvent);
                                input.dispatchEvent(changeEvent);
                                input.dispatchEvent(blurEvent);
                                
                                // For PrimeFaces, also try to trigger the dateSelect event and AJAX behavior
                                if (typeof PrimeFaces !== 'undefined') {
                                    try {
                                        // Find the calendar widget
                                        const widgetVarAttr = input.getAttribute('data-widget') || 
                                                            input.closest('.ui-calendar')?.getAttribute('data-widget');
                                        
                                        // Try to find widget by ID pattern
                                        const inputIdBase = input.id.replace('_input', '');
                                        const possibleWidgetNames = [inputIdBase, inputIdBase.replace(/:/g, '_')];
                                        
                                        for (const widgetName of possibleWidgetNames) {
                                            if (PrimeFaces.widgets && PrimeFaces.widgets[widgetName]) {
                                                const widget = PrimeFaces.widgets[widgetName];
                                                if (widget.setDate) {
                                                    widget.setDate(new Date(formattedDate));
                                                    console.log('Set date via PrimeFaces widget:', widgetName);
                                                }
                                                if (widget.fireDateSelectEvent) {
                                                    widget.fireDateSelectEvent();
                                                    console.log('Fired dateSelect event');
                                                }
                                                break;
                                            }
                                        }
                                        
                                        // Also trigger any AJAX behavior attached to the input
                                        if (input.onchange) {
                                            input.onchange();
                                        }
                                        
                                        // Try triggering PrimeFaces AJAX directly
                                        const ajaxBehavior = input.getAttribute('onchange');
                                        if (ajaxBehavior && ajaxBehavior.includes('PrimeFaces.ab')) {
                                            eval(ajaxBehavior);
                                            console.log('Executed PrimeFaces AJAX behavior');
                                        }
                                    } catch(e) {
                                        console.log('PrimeFaces widget trigger failed:', e.message);
                                    }
                                }
                                
                                // Final check
                                console.log('Final input value:', input.value);
                                return { success: true, finalValue: input.value };
                            }
                        ''', {'selector': date_input_selector, 'inputId': input_id, 'formattedDate': formatted_date})
                        
                        logger.info(f"JavaScript date set result: {date_set_success}")
                        await self.page.wait_for_timeout(1500)  # Longer wait for AJAX
                        
                        # Verify the value was actually set - THIS IS CRITICAL
                        current_value = await date_input.input_value()
                        logger.info("=" * 50)
                        logger.info(f"DATE VERIFICATION: Expected '{formatted_date}', Got '{current_value}'")
                        logger.info("=" * 50)
                        
                        if current_value and formatted_date.lower() in current_value.lower():
                            logger.info("SUCCESS: Date input contains expected date value")
                        else:
                            logger.warning(f"WARNING: Date input value '{current_value}' does not match expected '{formatted_date}'")
                        
                        # If JavaScript method didn't work, try clicking the calendar button
                        if not current_value or formatted_date not in current_value:
                            logger.info("JavaScript date set may not have worked, trying calendar UI interaction...")
                            
                            # Look for calendar button/icon next to the input
                            calendar_button_selectors = [
                                'button[class*="ui-datepicker-trigger"]',
                                'span[class*="ui-datepicker-trigger"]',
                                'button[class*="calendar"]',
                                '.ui-calendar button',
                                '.ui-calendar .ui-button',
                                '[id*="reservationDate"] + button',
                                '[id*="date"] ~ button'
                            ]
                            
                            for cal_selector in calendar_button_selectors:
                                try:
                                    cal_btn = self.page.locator(cal_selector).first
                                    if await cal_btn.count() > 0:
                                        logger.info(f"Found calendar button with: {cal_selector}")
                                        await cal_btn.click()
                                        await self.page.wait_for_timeout(500)
                                        
                                        # Now try to select the date from the calendar popup
                                        # Parse the target date
                                        from datetime import datetime as dt
                                        if '-' in target_date:
                                            tgt_date = dt.strptime(target_date, "%Y-%m-%d")
                                        else:
                                            tgt_date = dt.strptime(formatted_date, "%d %b %Y")
                                        
                                        day = tgt_date.day
                                        month = tgt_date.strftime("%B")  # Full month name
                                        year = tgt_date.year
                                        
                                        logger.info(f"Selecting date: {day} {month} {year}")
                                        
                                        # Click the day in the calendar
                                        day_selector = f'td[data-month] a:text-is("{day}")'
                                        day_link = self.page.locator(day_selector).first
                                        if await day_link.count() > 0:
                                            await day_link.click()
                                            logger.info(f"Clicked day {day} in calendar")
                                        else:
                                            # Try alternative day selector
                                            day_links = self.page.locator(f'a:text-is("{day}")').all()
                                            for dl in await day_links:
                                                parent_class = await dl.evaluate('el => el.parentElement.className')
                                                if 'ui-datepicker' in parent_class or 'calendar' in parent_class.lower():
                                                    await dl.click()
                                                    logger.info(f"Clicked day {day} via alternative selector")
                                                    break
                                        
                                        await self.page.wait_for_timeout(500)
                                        break
                                except Exception as cal_err:
                                    logger.info(f"Calendar button selector {cal_selector} failed: {cal_err}")
                                    continue
                            
                            # Final fallback: Triple-click, clear, type, and tab out
                            logger.info("Trying final fallback: direct input with Tab key...")
                            await date_input.click(click_count=3)
                            await self.page.wait_for_timeout(200)
                            await date_input.fill(formatted_date)
                            await self.page.wait_for_timeout(300)
                            await date_input.press('Tab')  # Tab triggers blur event
                            await self.page.wait_for_timeout(1000)
                            
                            # Also try pressing Enter which often triggers form submission/AJAX
                            await date_input.click()
                            await self.page.wait_for_timeout(100)
                            await self.page.keyboard.press('Enter')
                            await self.page.wait_for_timeout(500)
                        
                        # Final verification - CRITICAL CHECK
                        final_value = await date_input.input_value()
                        logger.info("=" * 50)
                        logger.info(f"FINAL DATE VERIFICATION:")
                        logger.info(f"  Target date: {target_date}")
                        logger.info(f"  Formatted date: {formatted_date}")
                        logger.info(f"  Input field value: '{final_value}'")
                        logger.info("=" * 50)
                        
                        if not final_value or formatted_date.lower() not in final_value.lower():
                            logger.error(f"DATE SET FAILED: Input shows '{final_value}' but expected '{formatted_date}'")
                        else:
                            logger.info(f"DATE SET SUCCESS: Input correctly shows '{final_value}'")
                        
                    except Exception as date_err:
                        logger.error(f"Failed to set date input: {date_err}")
                        # Don't just warn - this is critical, but we'll check after Load click
                else:
                    logger.warning("Could not find date input field - will use portal default date")
            
            # Click the Load button
            logger.info(f"Current URL before Load: {self.page.url}")
            load_button = self.page.locator('input[type="submit"][value="Load"], button:has-text("Load")').first
            
            # Check if Load button exists
            button_count = await load_button.count()
            logger.info(f"Found {button_count} Load button(s)")
            
            if button_count > 0:
                await load_button.click()
                logger.info("Clicked Load button")
            else:
                logger.error("Load button not found!")
                # Try alternative selectors
                alt_load = self.page.locator('input[value="Load"], button:text("Load"), .ui-button:has-text("Load")').first
                if await alt_load.count() > 0:
                    await alt_load.click()
                    logger.info("Clicked Load via alternative selector")
            
            # Wait for data to load
            logger.info(f"Current URL after Load click: {self.page.url}")
            await self.page.wait_for_load_state("networkidle", timeout=20000)
            await self.page.wait_for_timeout(5000)  # Extra wait for AJAX content
            
            # Debug: Take screenshot and log page content
            try:
                await self.page.screenshot(path="/tmp/sync_debug.png")
                logger.info("Debug screenshot saved to /tmp/sync_debug.png")
            except:
                pass
            
            # Log what's visible on the page
            page_text = await self.page.inner_text('body')
            logger.info(f"Page text length: {len(page_text)}")
            logger.info(f"Page text preview: {page_text[:500]}")
            if 'Scheduled' in page_text:
                logger.info("Found 'Scheduled' in page text")
            if 'Arrivals' in page_text:
                logger.info("Found 'Arrivals' in page text")
            if 'No records' in page_text or 'no records' in page_text.lower():
                logger.info("Page shows 'No records'")
            if 'error' in page_text.lower():
                logger.warning("Page might contain an error")
            
            # === CRITICAL ERROR CHECK: Verify data actually loaded ===
            # Check for portal error message that indicates data load failure
            # This is the EXACT error message the portal shows when date selection fails
            portal_error_patterns = [
                'Unable to enter sign-in sheets for current or future res',
                'Unable to enter sign-in sheets',
                'Unable to enter sign in sheets',
                'No sign-in sheets available',
                'Error loading',
                'Access denied',
                'Session expired',
                'Invalid date',
                'current or future res'
            ]
            
            logger.info("=== CHECKING FOR PORTAL ERROR MESSAGES ===")
            for error_pattern in portal_error_patterns:
                if error_pattern.lower() in page_text.lower():
                    error_msg = f"PORTAL ERROR DETECTED: '{error_pattern}' found in page. The date picker interaction FAILED. Portal did not load data for the requested date. This sync will be aborted."
                    logger.error("!" * 50)
                    logger.error(error_msg)
                    logger.error("!" * 50)
                    self.results["errors"].append(error_msg)
                    # Take screenshot of the error state
                    try:
                        await self.page.screenshot(path="/tmp/sync_portal_error.png")
                        logger.info("Error screenshot saved to /tmp/sync_portal_error.png")
                    except:
                        pass
                    raise Exception(error_msg)
            logger.info("No portal error messages detected - proceeding with sync")
            
            # Check if "Scheduled Arrivals" section appeared
            try:
                await self.page.wait_for_selector('text=Scheduled Arrivals', timeout=10000)
                logger.info("Sign-in sheet data loaded successfully")
                
                # === STEP 1: Record first employee name on page ===
                first_employee = None
                try:
                    # Find the first employee name in the table
                    first_row = self.page.locator('tr').filter(has=self.page.locator('input[type="text"]')).first
                    if await first_row.count() > 0:
                        first_text = await first_row.inner_text()
                        logger.info(f"First employee row text: {first_text[:100]}")
                        # Extract name from the row
                        for part in first_text.split('\t'):
                            part = part.strip()
                            if ('/' in part or '(' in part) and len(part) > 5:
                                first_employee = part
                                break
                        logger.info(f"First employee name: {first_employee}")
                except Exception as e:
                    logger.warning(f"Could not get first employee name: {e}")
                
                # === STEP 2: Click "Load More" until no more entries ===
                logger.info("Looking for 'Load More' button (blue tab on left side below records)...")
                load_more_clicks = 0
                max_load_more = 20  # Maximum number of "Load More" clicks
                
                while load_more_clicks < max_load_more:
                    # Scroll to bottom to see if there's a "Load More" button
                    await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await self.page.wait_for_timeout(1000)
                    
                    # Look for "Load More" button - blue tab on left side
                    # Try multiple selectors for blue button/tab with "Load More" text
                    load_more_selectors = [
                        'a:has-text("Load More")',
                        'button:has-text("Load More")',
                        'span:has-text("Load More")',
                        'div:has-text("Load More")',
                        '[class*="blue"]:has-text("Load More")',
                        '[class*="load"]:has-text("More")',
                        '[style*="blue"]:has-text("Load More")',
                        '.ui-button:has-text("Load More")',
                        'input[value*="Load More"]',
                        '[class*="tab"]:has-text("Load More")',
                        # PrimeNG/Angular specific selectors
                        '.ui-paginator-next',
                        '.p-paginator-next',
                        '[class*="paginator"]:has-text("Load")',
                        '[class*="more"]',
                    ]
                    
                    load_more_button = None
                    for selector in load_more_selectors:
                        try:
                            btn = self.page.locator(selector).first
                            if await btn.count() > 0 and await btn.is_visible():
                                load_more_button = btn
                                logger.info(f"Found Load More with selector: {selector}")
                                break
                        except:
                            continue
                    
                    if load_more_button:
                        try:
                            logger.info(f"Clicking 'Load More' button (attempt {load_more_clicks + 1})")
                            await load_more_button.scroll_into_view_if_needed()
                            await self.page.wait_for_timeout(500)
                            await load_more_button.click()
                            await self.page.wait_for_timeout(2000)  # Wait for new content to load
                            load_more_clicks += 1
                        except Exception as e:
                            logger.info(f"Could not click Load More button: {e} - may have reached end")
                            break
                    else:
                        # Check if "Load More" text exists anywhere on page
                        page_text = await self.page.inner_text('body')
                        if 'Load More' in page_text:
                            logger.info("Found 'Load More' text but couldn't click it, trying to scroll and find...")
                            # Try clicking by coordinates - left side, bottom of records
                            try:
                                # Find the element containing "Load More" text
                                load_more_element = self.page.get_by_text('Load More', exact=False).first
                                if await load_more_element.count() > 0:
                                    await load_more_element.scroll_into_view_if_needed()
                                    await self.page.wait_for_timeout(500)
                                    await load_more_element.click()
                                    await self.page.wait_for_timeout(2000)
                                    load_more_clicks += 1
                                    logger.info("Clicked Load More using text search")
                                else:
                                    logger.info("Could not find clickable Load More element")
                                    break
                            except:
                                logger.info("Failed to click Load More via text search")
                                break
                        else:
                            logger.info("No 'Load More' text found on page - all entries loaded")
                            break
                
                logger.info(f"Clicked 'Load More' {load_more_clicks} times")
                
                # === STEP 3: Record last employee name on page ===
                last_employee = None
                try:
                    # Scroll to bottom to find last employee
                    await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await self.page.wait_for_timeout(1000)
                    
                    # Find all rows with inputs and get the last one
                    all_data_rows = self.page.locator('tr').filter(has=self.page.locator('input[type="text"]'))
                    row_count = await all_data_rows.count()
                    logger.info(f"Total data rows found: {row_count}")
                    
                    if row_count > 0:
                        last_row = all_data_rows.nth(row_count - 1)
                        last_text = await last_row.inner_text()
                        logger.info(f"Last employee row text: {last_text[:100]}")
                        # Extract name from the row
                        for part in last_text.split('\t'):
                            part = part.strip()
                            if ('/' in part or '(' in part) and len(part) > 5:
                                last_employee = part
                                break
                        logger.info(f"Last employee name: {last_employee}")
                except Exception as e:
                    logger.warning(f"Could not get last employee name: {e}")
                
                # Log summary of what was found
                logger.info(f"=== LOAD SUMMARY ===")
                logger.info(f"First employee: {first_employee}")
                logger.info(f"Last employee: {last_employee}")
                logger.info(f"Total Load More clicks: {load_more_clicks}")
                
                # Scroll back to top to start processing
                await self.page.evaluate('window.scrollTo(0, 0)')
                await self.page.wait_for_timeout(1000)
                
                return True
            except Exception as e:
                # === CRITICAL FIX: DO NOT mask this error! ===
                # If "Scheduled Arrivals" is not found, the date selection failed
                # and we should NOT proceed as if everything is fine
                error_msg = f"CRITICAL: 'Scheduled Arrivals' table not found on page. This means the date picker interaction failed and the portal did not load data for the requested date. The page may be showing a different date's data or an error. Original error: {str(e)}"
                logger.error(error_msg)
                self.results["errors"].append(error_msg)
                
                # Take a debug screenshot
                try:
                    await self.page.screenshot(path="/tmp/sync_scheduled_arrivals_missing.png")
                    logger.info("Debug screenshot saved to /tmp/sync_scheduled_arrivals_missing.png")
                except:
                    pass
                
                # RAISE the exception instead of silently continuing
                raise Exception(error_msg)
            
        except Exception as e:
            logger.error(f"Load error: {str(e)}")
            self.results["errors"].append(f"Failed to load sign-in sheet: {str(e)}")
            return False
    
    async def get_signin_sheet_entries(self) -> list:
        """Extract all sign-in sheet entries from the Scheduled Arrivals section."""
        entries = []
        try:
            logger.info("Extracting sign-in sheet entries...")
            
            # Debug: Print page content summary
            page_text = await self.page.inner_text('body')
            logger.info(f"Page contains 'Scheduled Arrivals': {'Scheduled Arrivals' in page_text}")
            logger.info(f"Page contains 'BEARDEN': {'BEARDEN' in page_text}")
            
            # Find all table rows in the data tables
            all_rows = await self.page.query_selector_all('tr')
            logger.info(f"Found {len(all_rows)} total rows")
            
            for row in all_rows:
                try:
                    row_text = await row.inner_text()
                    
                    # Skip header rows and empty rows
                    if not row_text or len(row_text.strip()) < 5:
                        continue
                    if 'Name' in row_text and 'Employee ID' in row_text and 'Room Number' in row_text:
                        continue
                    if 'Undo Change' in row_text or 'Select All' in row_text:
                        continue
                    if 'Reservation Date' in row_text and 'Billing Date' in row_text:
                        continue
                    
                    # Look for name patterns:
                    # 1. LASTNAME/FIRSTNAME format (e.g., BEARDEN/WILLIAM/OT I E)
                    # 2. LASTNAME,(FIRSTNAME) format (e.g., HESS,(BERNARD) DT/2 E)
                    # Both are uppercase and contain either "/" or "("
                    
                    cells = await row.query_selector_all('td')
                    if len(cells) < 3:
                        continue
                    
                    name_text = None
                    
                    for cell in cells:
                        cell_text = await cell.inner_text()
                        cell_text = cell_text.strip()
                        
                        if len(cell_text) < 5:
                            continue
                        
                        # Skip date patterns
                        if any(month in cell_text for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                            if len(cell_text) < 15:  # Short date strings
                                continue
                        
                        # Check for name patterns (uppercase with / or ()
                        has_slash = '/' in cell_text
                        has_paren = '(' in cell_text and ')' in cell_text
                        is_mostly_upper = sum(1 for c in cell_text if c.isupper()) > len(cell_text) * 0.5
                        
                        if (has_slash or has_paren) and is_mostly_upper:
                            # Additional check: not a date
                            if not (cell_text[0:2].isdigit() or cell_text[-4:].isdigit()):
                                name_text = cell_text
                                break
                            # Or if it's long enough to be a name
                            if len(cell_text) > 12:
                                name_text = cell_text
                                break
                    
                    if not name_text:
                        continue
                    
                    logger.info(f"Found name: {name_text}")
                    
                    # Find inputs in this row
                    text_inputs = await row.query_selector_all('input[type="text"]')
                    checkboxes = await row.query_selector_all('input[type="checkbox"]')
                    
                    emp_input = text_inputs[0] if len(text_inputs) >= 1 else None
                    room_input = text_inputs[1] if len(text_inputs) >= 2 else None
                    no_bill_checkbox = checkboxes[1] if len(checkboxes) >= 2 else (checkboxes[0] if checkboxes else None)
                    
                    # Check if already verified - needs non-empty Employee ID with actual digits
                    emp_value = ""
                    if emp_input:
                        emp_value = await emp_input.get_attribute('value') or ''
                        emp_value = emp_value.strip()
                    
                    # Log the value for debugging
                    logger.info(f"Employee ID field value for {name_text}: '{emp_value}' (len={len(emp_value)})")
                    
                    # Check for RED status indicator (unfilled) vs BLUE checkmark (filled)
                    # The status column has an icon - red exclamation (!) for unfilled, blue checkmark for filled
                    has_red_status = False
                    has_blue_status = False
                    
                    try:
                        # Look for status indicators in the row
                        row_html = await row.inner_html()
                        # Red status usually has 'ui-icon-alert' or red color, blue has 'ui-icon-check' or checkmark
                        if 'color:red' in row_html.lower() or 'ui-icon-alert' in row_html or 'status-red' in row_html.lower():
                            has_red_status = True
                        if 'color:blue' in row_html.lower() or 'ui-icon-check' in row_html or 'checkmark' in row_html.lower() or 'color:green' in row_html.lower():
                            has_blue_status = True
                        
                        # Also check for specific icon elements
                        status_icons = await row.query_selector_all('span[class*="ui-icon"], img[src*="status"], .status-icon')
                        for icon in status_icons:
                            icon_class = await icon.get_attribute('class') or ''
                            icon_style = await icon.get_attribute('style') or ''
                            if 'red' in icon_class.lower() or 'red' in icon_style.lower() or 'alert' in icon_class.lower():
                                has_red_status = True
                            if 'blue' in icon_class.lower() or 'green' in icon_class.lower() or 'check' in icon_class.lower():
                                has_blue_status = True
                    except:
                        pass
                    
                    # Only consider verified if it has actual numbers (employee IDs are numeric)
                    # OR if blue status is detected
                    is_verified = (emp_value and len(emp_value) >= 4 and any(c.isdigit() for c in emp_value)) or has_blue_status
                    
                    entry = {
                        "name": name_text,
                        "emp_input": emp_input,
                        "room_input": room_input,
                        "no_bill_checkbox": no_bill_checkbox,
                        "verified": is_verified,
                        "has_red_status": has_red_status,
                        "has_blue_status": has_blue_status,
                        "current_emp_id": emp_value,
                        "row": row
                    }
                    entries.append(entry)
                    logger.info(f"Entry added: {name_text}, verified={is_verified}, red_status={has_red_status}, blue_status={has_blue_status}")
                    
                except Exception as row_err:
                    continue
            
            logger.info(f"Found {len(entries)} sign-in sheet entries")
            return entries
            
        except Exception as e:
            logger.error(f"Error extracting entries: {str(e)}")
            self.results["errors"].append(f"Failed to extract entries: {str(e)}")
            return []
    
    async def load_entries_for_date(self, target_date: str) -> list:
        """Load and extract entries for a specific date.
        
        Combines load_signin_sheet and get_signin_sheet_entries for date range scanning.
        
        Args:
            target_date: Date in YYYY-MM-DD format
            
        Returns:
            List of entry dicts with name, current_emp_id, room_number
        """
        try:
            # Load the sign-in sheet for this date
            success = await self.load_signin_sheet(target_date)
            if not success:
                logger.warning(f"Failed to load sign-in sheet for {target_date}")
                return []
            
            # Extract entries from the loaded page
            entries = await self.get_signin_sheet_entries()
            return entries
            
        except Exception as e:
            logger.error(f"Error loading entries for {target_date}: {str(e)}")
            return []
    
    async def verify_entry(self, entry: dict, employee_id: str, room_number: str) -> bool:
        """Fill in employee ID and room number for an entry.
        
        Based on video observation:
        1. Click directly on Employee ID input field in the row
        2. Type/paste the Employee ID
        3. Click away on empty space (near HEAVENER-OK header) to trigger auto-save
        4. Click on Room Number input field
        5. Type the Room Number
        6. Click away again to save
        7. Status changes from red ! to blue checkmark
        """
        try:
            name = entry.get("name", "")
            
            # Extract last name for searching
            if ',' in name:
                search_name = name.split(',')[0]
            elif '/' in name:
                search_name = name.split('/')[0]
            else:
                search_name = name.split()[0] if ' ' in name else name
            
            logger.info(f"Verifying {name}, searching for: {search_name}")
            
            # === Step 1: Find the row and input fields by scrolling through entire page ===
            logger.info("Step 1: Finding input fields in table row (with scroll search)...")
            
            target_row = None
            max_scroll_searches = 30  # Maximum scroll attempts to find the entry
            
            # First scroll to top
            await self.page.evaluate('window.scrollTo(0, 0)')
            await self.page.wait_for_timeout(500)
            
            # Get page height for scrolling
            page_height = await self.page.evaluate('document.body.scrollHeight')
            viewport_height = await self.page.evaluate('window.innerHeight')
            scroll_step = viewport_height * 0.7  # Scroll 70% of viewport at a time
            current_scroll = 0
            
            logger.info(f"Searching for '{search_name}' - page height: {page_height}, viewport: {viewport_height}")
            
            # Scroll through page to find the entry
            for scroll_attempt in range(max_scroll_searches):
                # Search for row at current scroll position - use .all() to get snapshot
                rows = await self.page.locator('tr').all()
                
                for row in rows:
                    try:
                        row_text = await row.inner_text()
                        if search_name.upper() in row_text.upper():
                            # Check if this row has input fields
                            inputs = row.locator('input[type="text"]')
                            if await inputs.count() >= 2:
                                # Check if row is visible
                                is_visible = await row.is_visible()
                                if is_visible:
                                    target_row = row
                                    logger.info(f"Found target row for {search_name} at scroll position {current_scroll}")
                                    break
                    except:
                        continue
                
                if target_row:
                    break
                
                # Scroll down
                current_scroll += scroll_step
                if current_scroll >= page_height:
                    # Reached bottom, scroll back to top and try once more
                    logger.info("Reached bottom, scrolling back to top...")
                    await self.page.evaluate('window.scrollTo(0, 0)')
                    current_scroll = 0
                    await self.page.wait_for_timeout(500)
                    
                    # If we've already done a full pass, stop
                    if scroll_attempt > max_scroll_searches / 2:
                        break
                else:
                    await self.page.evaluate(f'window.scrollTo(0, {current_scroll})')
                    await self.page.wait_for_timeout(300)
                    logger.info(f"Scroll search {scroll_attempt + 1}: position {current_scroll}/{page_height}")
            
            if not target_row:
                logger.warning(f"Could not find row for: {search_name} after scrolling entire page")
                return False
            
            # === Scroll row into view before interacting ===
            logger.info(f"Scrolling row into view for {search_name}...")
            try:
                # Use JavaScript scrollIntoView for more reliable scrolling
                await self.page.evaluate('arguments[0].scrollIntoView({block: "center", inline: "nearest"})', await target_row.element_handle())
            except:
                await target_row.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(1000)  # Increased wait for scroll to complete
            
            # Verify the row is now visible
            is_visible = await target_row.is_visible()
            if not is_visible:
                logger.warning(f"Row still not visible after scrolling for {search_name}, trying again...")
                await self.page.evaluate(f'window.scrollBy(0, -200)')  # Scroll up a bit
                await self.page.wait_for_timeout(500)
            
            # Find Employee ID and Room Number inputs by their position or ID
            emp_input = None
            room_input = None
            
            row_inputs = target_row.locator('input[type="text"]')
            input_count = await row_inputs.count()
            logger.info(f"Found {input_count} text inputs in row")
            
            for i in range(input_count):
                inp = row_inputs.nth(i)
                inp_id = await inp.get_attribute('id') or ''
                inp_value = await inp.input_value()
                logger.info(f"  Input {i}: id='{inp_id}', value='{inp_value}'")
                
                if 'employeeid' in inp_id.lower() and not emp_input:
                    emp_input = inp
                    logger.info(f"Identified Employee ID input at index {i}")
                elif 'roomnumber' in inp_id.lower() and not room_input:
                    room_input = inp
                    logger.info(f"Identified Room Number input at index {i}")
            
            if not emp_input:
                logger.warning("Could not find Employee ID input field")
                return False
            
            # === Step 2: Enter Employee ID ===
            logger.info(f"Step 2: Entering Employee ID '{employee_id}'...")
            
            # Click to focus
            await emp_input.click()
            await self.page.wait_for_timeout(500)
            
            # Select all and delete existing content
            await self.page.keyboard.press('Control+a')
            await self.page.wait_for_timeout(100)
            await self.page.keyboard.press('Backspace')
            await self.page.wait_for_timeout(100)
            
            # Type character by character
            await self.page.keyboard.type(str(employee_id), delay=50)
            await self.page.wait_for_timeout(500)
            
            # Verify value was entered
            emp_val = await emp_input.input_value()
            logger.info(f"Employee ID value after type: '{emp_val}'")
            
            # === Step 3: Click OUTSIDE the row to trigger save ===
            logger.info("Step 3: Clicking OUTSIDE the row to trigger auto-save...")
            
            # Click on body area far from the table (outside the row)
            await self.page.mouse.click(100, 100)
            logger.info("Clicked at (100, 100) - outside the row")
            
            # Wait for auto-save to complete (reduced from 5s to 2s)
            logger.info("Waiting 2 seconds for Employee ID to save...")
            await self.page.wait_for_timeout(2000)
            
            # === Step 4: Enter Room Number ===
            if room_input:
                logger.info(f"Step 4: Entering Room Number '{room_number}'...")
                
                # Click to focus
                await room_input.click()
                await self.page.wait_for_timeout(500)
                
                # Select all and delete
                await self.page.keyboard.press('Control+a')
                await self.page.wait_for_timeout(100)
                await self.page.keyboard.press('Backspace')
                await self.page.wait_for_timeout(100)
                
                # Type room number character by character
                await self.page.keyboard.type(str(room_number), delay=50)
                await self.page.wait_for_timeout(500)
                
                # Verify
                room_val = await room_input.input_value()
                logger.info(f"Room Number value after type: '{room_val}'")
                
                # === Step 5: Click OUTSIDE the row to save Room Number ===
                logger.info("Step 5: Clicking OUTSIDE the row to save Room Number...")
                
                # Click on body area far from the table
                await self.page.mouse.click(100, 100)
                logger.info("Clicked at (100, 100) - outside the row")
                
                # Wait for Room Number to save and blue checkmark to appear (reduced from 5s to 2s)
                logger.info("Waiting 2 seconds for Room Number to save...")
                await self.page.wait_for_timeout(2000)
                
                # === Step 6: Check for blue checkmark (verify save was successful) ===
                logger.info("Step 6: Checking for blue checkmark...")
                
                # Re-find the row and check status - use .all() to get snapshot
                try:
                    rows = await self.page.locator('tr').all()
                    for row in rows:
                        try:
                            row_text = await row.inner_text()
                            if search_name.upper() in row_text.upper():
                                row_html = await row.inner_html()
                                if 'color:blue' in row_html.lower() or 'ui-icon-check' in row_html or 'checkmark' in row_html.lower() or 'color:green' in row_html.lower():
                                    logger.info("✓ Blue checkmark detected - save successful!")
                                    break
                                elif 'color:red' in row_html.lower() or 'ui-icon-alert' in row_html:
                                    logger.warning("✗ Red status still showing - save may have failed")
                                    break
                        except:
                            continue
                except Exception as status_err:
                    logger.info(f"Could not verify status: {status_err}")
            else:
                logger.warning("Room Number input not found, only entered Employee ID")
            
            # Take screenshot to verify final state
            try:
                await self.page.screenshot(path=f"/tmp/sync_final_{search_name}.png")
                logger.info(f"Screenshot saved: /tmp/sync_final_{search_name}.png")
            except:
                pass
            
            # Wait for page to stabilize before processing next entry (reduced from 2s to 1s)
            await self.page.wait_for_timeout(1000)
            
            logger.info(f"Completed: {name} -> EmpID: {employee_id}, Room: {room_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying {entry.get('name', 'unknown')}: {str(e)}")
            return False
    
    async def mark_no_bill(self, entry: dict) -> bool:
        """Mark an entry as No Bill (guest didn't stay)."""
        try:
            name = entry.get("name", "")
            
            # Extract just the last name for searching (more reliable)
            # Names are like "OLDHAM,(DWIGHT)BHW RC" or "BEARDEN/WILLIAM/OT I E"
            if ',' in name:
                search_name = name.split(',')[0]  # Get "OLDHAM"
            elif '/' in name:
                search_name = name.split('/')[0]  # Get "BEARDEN"
            else:
                search_name = name.split()[0] if ' ' in name else name
            
            logger.info(f"Searching for row with name containing: {search_name}")
            
            # === Scroll-based search to find the row ===
            target_row = None
            max_scroll_searches = 30
            
            # First scroll to top
            await self.page.evaluate('window.scrollTo(0, 0)')
            await self.page.wait_for_timeout(500)
            
            page_height = await self.page.evaluate('document.body.scrollHeight')
            viewport_height = await self.page.evaluate('window.innerHeight')
            scroll_step = viewport_height * 0.7
            current_scroll = 0
            
            for scroll_attempt in range(max_scroll_searches):
                # Search for row at current scroll position
                all_rows = await self.page.query_selector_all('tr')
                
                for row in all_rows:
                    try:
                        row_text = await row.inner_text()
                        if search_name in row_text:
                            # Verify this is a data row (has checkboxes)
                            checkboxes = await row.query_selector_all('.ui-chkbox, input[type="checkbox"]')
                            if len(checkboxes) > 0:
                                # Check if visible
                                is_visible = await row.is_visible()
                                if is_visible:
                                    target_row = row
                                    logger.info(f"Found row for {search_name} at scroll position {current_scroll}")
                                    break
                    except:
                        continue
                
                if target_row:
                    break
                
                # Scroll down
                current_scroll += scroll_step
                if current_scroll >= page_height:
                    logger.info("Reached bottom while searching for No Bill row")
                    break
                else:
                    await self.page.evaluate(f'window.scrollTo(0, {current_scroll})')
                    await self.page.wait_for_timeout(300)
            
            if not target_row:
                logger.warning(f"Could not find row for: {name} (searched: {search_name})")
                return False
            
            # Scroll row into view
            try:
                await self.page.evaluate('arguments[0].scrollIntoView({block: "center"})', target_row)
                await self.page.wait_for_timeout(500)
            except:
                pass
            
            # Find checkboxes in this row - No Bill is typically the second checkbox
            # PrimeFaces checkboxes have a wrapper div
            checkbox_wrappers = await target_row.query_selector_all('.ui-chkbox')
            
            if len(checkbox_wrappers) >= 2:
                # Second checkbox wrapper is "No Bill"
                no_bill_wrapper = checkbox_wrappers[1]
                # Click the wrapper box (the visible clickable element)
                no_bill_box = await no_bill_wrapper.query_selector('.ui-chkbox-box')
                if no_bill_box:
                    await no_bill_box.click()
                    logger.info(f"Clicked No Bill checkbox for: {name}")
                else:
                    await no_bill_wrapper.click()
                    logger.info(f"Clicked No Bill wrapper for: {name}")
            elif len(checkbox_wrappers) == 1:
                no_bill_box = await checkbox_wrappers[0].query_selector('.ui-chkbox-box')
                if no_bill_box:
                    await no_bill_box.click()
                else:
                    await checkbox_wrappers[0].click()
                logger.info(f"Clicked single checkbox for: {name}")
            else:
                # Fallback: try finding input checkboxes directly
                checkboxes = await target_row.query_selector_all('input[type="checkbox"]')
                if len(checkboxes) >= 2:
                    await checkboxes[1].click(force=True)
                    logger.info(f"Clicked checkbox input for: {name}")
                elif len(checkboxes) == 1:
                    await checkboxes[0].click(force=True)
                    logger.info(f"Clicked single checkbox input for: {name}")
                else:
                    logger.warning(f"No checkboxes found for: {name}")
                    return False
            
            # Wait for auto-save to trigger (portal auto-refreshes after 2-3 seconds)
            await self.page.wait_for_timeout(3500)
            
            logger.info(f"Marked No Bill: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking no bill for {entry.get('name', 'unknown')}: {str(e)}")
            return False
    
    async def save_changes(self) -> bool:
        """Click the Save button to persist all changes."""
        try:
            logger.info("Looking for Save button...")
            
            # Try multiple selectors for the Save button
            save_selectors = [
                'input[type="submit"][value="Save"]',
                'button:has-text("Save")',
                'input[value="Save"]',
                '.ui-button:has-text("Save")',
                'input[type="button"][value="Save"]',
                'a:has-text("Save")',
                'span:has-text("Save")'
            ]
            
            save_button = None
            for selector in save_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if await btn.count() > 0:
                        save_button = btn
                        logger.info(f"Found Save button with selector: {selector}")
                        break
                except:
                    continue
            
            if save_button:
                await save_button.click(force=True)
                logger.info("Clicked Save button")
                
                # Wait for save to complete
                await self.page.wait_for_load_state("networkidle", timeout=15000)
                await self.page.wait_for_timeout(2000)
                
                # Check for success message or confirmation
                page_text = await self.page.inner_text('body')
                if 'success' in page_text.lower() or 'saved' in page_text.lower():
                    logger.info("Changes saved successfully")
                else:
                    logger.info("Save completed (no confirmation message found)")
                
                return True
            else:
                logger.warning("Save button not found - changes may not be persisted!")
                
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="/tmp/sync_no_save_btn.png")
                    logger.info("Screenshot saved to /tmp/sync_no_save_btn.png")
                except:
                    pass
                
                return False
                
        except Exception as e:
            logger.error(f"Error saving changes: {str(e)}")
            return False
    
    async def run_sync(self, hodler_records: list, target_date: str = None, name_aliases: list = None, progress_callback=None) -> dict:
        """
        Run the full sync process.
        
        Args:
            hodler_records: List of dicts with 'employee_name', 'employee_number', 'room_number'
            target_date: Optional date in format 'YYYY-MM-DD' to sync for a specific date
            name_aliases: Optional list of name mappings from portal names to employee IDs
            progress_callback: Optional async function(entry_num, total, name) to report progress
        
        Returns:
            Results dict with verified, no_bill, missing entries
        """
        if name_aliases is None:
            name_aliases = []
        
        self.progress_callback = progress_callback
        
        # RESET results at the start of each sync run
        self.results = {
            "verified": [],
            "no_bill": [],
            "missing_in_hodler": [],
            "errors": []
        }
        
        try:
            # Log version at start of sync
            logger.info(f"=" * 50)
            logger.info(f"SYNC AGENT VERSION: {SYNC_AGENT_VERSION}")
            logger.info(f"=" * 50)
            
            await self.start()
            
            # Step 1: Login
            if not await self.login():
                return self.results
            
            # Step 2: Navigate to Sign-in Sheets > Online Sign-in Sheets
            if not await self.navigate_to_signin_sheets():
                return self.results
            
            # Step 3: Click Load to get the data (with optional date)
            if not await self.load_signin_sheet(target_date):
                return self.results
            
            # Step 4-6: LOOP until all entries verified (handles page refresh)
            max_sync_passes = 5  # Maximum number of full passes
            sync_pass = 0
            
            while sync_pass < max_sync_passes:
                sync_pass += 1
                logger.info(f"=== SYNC PASS {sync_pass}/{max_sync_passes} ===")
                
                # Step 4a: Click "Load More" until all entries are visible
                logger.info("Loading all entries (clicking Load More if needed)...")
                load_more_clicks = 0
                while load_more_clicks < 20:
                    await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await self.page.wait_for_timeout(1000)
                    
                    # Look for "Load More" button/link
                    load_more = self.page.get_by_text('Load More', exact=False).first
                    try:
                        if await load_more.count() > 0 and await load_more.is_visible():
                            logger.info(f"Clicking 'Load More' (click {load_more_clicks + 1})")
                            await load_more.click()
                            await self.page.wait_for_timeout(2000)
                            load_more_clicks += 1
                        else:
                            break
                    except:
                        break
                
                logger.info(f"Load More clicked {load_more_clicks} times in pass {sync_pass}")
                
                # Scroll back to top
                await self.page.evaluate('window.scrollTo(0, 0)')
                await self.page.wait_for_timeout(1000)
                
                # Step 4b: Get all entries from the table
                entries = await self.get_signin_sheet_entries()
                
                if not entries:
                    logger.info("No entries found to process")
                    if sync_pass == 1:
                        self.results["errors"].append("No entries found on the sign-in sheet")
                    break
                
                # Count red (unverified) entries
                red_entries = [e for e in entries if e.get("has_red_status") and not e.get("verified")]
                blue_entries = [e for e in entries if e.get("has_blue_status") or e.get("verified")]
                unverified_entries = [e for e in entries if not e.get("verified") and not e.get("has_blue_status")]
                entries_without_emp_id = [e for e in entries if not e.get("current_emp_id")]
                
                logger.info(f"Pass {sync_pass}: Total entries={len(entries)}, Red (unverified)={len(red_entries)}, Blue (verified)={len(blue_entries)}, Without employee ID={len(entries_without_emp_id)}")
                
                # Store diagnostic info in results
                if "diagnostics" not in self.results:
                    self.results["diagnostics"] = {
                        "portal_entries_found": len(entries),
                        "hodler_records_provided": len(hodler_records),
                        "portal_entry_names": [e.get("name", "unknown") for e in entries[:10]],  # First 10
                        "hodler_record_names": [r.get("employee_name", "unknown") for r in hodler_records[:10]]  # First 10
                    }
                
                # Determine if we have work to do:
                # - If all entries are verified (blue checkmarks), we're done
                # - But we should also check if there are entries without employee IDs - those need processing
                entries_needing_work = [e for e in entries if 
                    not e.get("verified") and 
                    not e.get("has_blue_status") and 
                    (not e.get("current_emp_id") or e.get("has_red_status"))
                ]
                
                # Track verified employee IDs to detect duplicates
                verified_employee_ids = set()
                
                # FIRST: Match blue (already verified) entries against Hodler records
                # This ensures we count them as verified even if no portal work is needed
                # BUT if they're missing Employee ID or Room, we should still fill it in
                total_entries = len(entries)
                for entry_num, entry in enumerate(entries, 1):
                    api_name = entry["name"]
                    
                    # Report progress for all entries - update UI immediately
                    if self.progress_callback:
                        try:
                            await self.progress_callback(entry_num, total_entries, f"Processing: {api_name}")
                            # Small delay to allow UI update
                            await asyncio.sleep(0.1)
                        except Exception as pe:
                            logger.warning(f"Progress callback error: {pe}")
                    
                    already_verified_on_portal = entry.get("verified") or entry.get("has_blue_status")
                    has_employee_id = entry.get("current_emp_id") and entry.get("current_emp_id") != "NO ID"
                    
                    if already_verified_on_portal:
                        # Track this employee ID as already verified
                        if has_employee_id:
                            current_emp_id = entry.get("current_emp_id")
                            # Check if this employee ID was already verified (DUPLICATE on portal)
                            if current_emp_id in verified_employee_ids:
                                logger.info(f"*** DUPLICATE DETECTED (blue entry): {api_name} - Employee {current_emp_id} already processed ***")
                                # This is a duplicate - mark as No Bill
                                try:
                                    if await self.mark_no_bill(entry):
                                        self.results["no_bill"].append({
                                            "name": api_name,
                                            "reason": f"Duplicate entry - Employee {current_emp_id} already verified on portal",
                                            "employee_id": current_emp_id
                                        })
                                        logger.info(f"Successfully marked duplicate blue entry {api_name} as No Bill")
                                    else:
                                        logger.warning(f"Failed to mark duplicate blue entry {api_name} as No Bill")
                                except Exception as e:
                                    logger.error(f"Error marking duplicate blue entry as No Bill: {e}")
                                continue  # Skip to next entry
                            else:
                                verified_employee_ids.add(current_emp_id)
                        
                        # Check if this already-verified entry matches a Hodler Inn record
                        for record in hodler_records:
                            hodler_name = record.get("employee_name", "")
                            if match_names(api_name, hodler_name):
                                # Track this employee ID
                                emp_id = record.get("employee_number", "")
                                if emp_id:
                                    verified_employee_ids.add(emp_id)
                                
                                # Check if we already counted this one
                                already_counted = any(
                                    v.get("api_name") == api_name or v.get("hodler_name") == hodler_name
                                    for v in self.results["verified"]
                                )
                                
                                # If blue but missing Employee ID or Room, fill it in
                                if not has_employee_id:
                                    logger.info(f"Blue entry missing Employee ID - filling in: {api_name}")
                                    try:
                                        await self.verify_entry(
                                            entry,
                                            record.get("employee_number", ""),
                                            record.get("room_number", "")
                                        )
                                    except Exception as e:
                                        logger.error(f"Failed to fill blue entry: {e}")
                                
                                if not already_counted:
                                    logger.info(f"*** VERIFIED (blue checkmark + Hodler match): {api_name} <-> {hodler_name} ***")
                                    self.results["verified"].append({
                                        "api_name": api_name,
                                        "hodler_name": hodler_name,
                                        "employee_id": record.get("employee_number"),
                                        "room": record.get("room_number"),
                                        "portal_name": api_name,
                                        "update_name": api_name != hodler_name,
                                        "pre_verified": True,
                                        "filled_missing_data": not has_employee_id
                                    })
                                break
                
                if len(entries_needing_work) == 0 and len(red_entries) == 0:
                    if len(blue_entries) == len(entries):
                        logger.info(f"All entries have blue checkmarks - matched {len(self.results['verified'])} with Hodler records")
                    else:
                        logger.info("No entries need verification - all have employee IDs filled")
                    break
                
                # Step 5: Process each entry that needs verification (red/unverified entries only)
                entries_processed_this_pass = 0
                
                for entry in entries:
                    api_name = entry["name"]
                    
                    # Skip already verified entries - they were matched above
                    if entry.get("verified") or entry.get("has_blue_status"):
                        continue
                    
                    # Process entries that need work:
                    # 1. Have red status (definitely unverified)
                    # 2. OR don't have an employee ID filled in yet
                    # 3. OR explicitly marked as not verified
                    needs_processing = (
                        entry.get("has_red_status") or 
                        not entry.get("current_emp_id") or
                        not entry.get("verified")
                    )
                    
                    if not needs_processing:
                        logger.info(f"SKIPPING (appears complete): {api_name}")
                        continue
                    
                    logger.info(f"PROCESSING: {api_name} (red={entry.get('has_red_status')}, emp_id={entry.get('current_emp_id')})")
                    entries_processed_this_pass += 1
                    
                    matched = False
                    
                    # Log all Hodler records we're comparing against
                    logger.info(f"Comparing '{api_name}' against {len(hodler_records)} Hodler records:")
                    for idx, record in enumerate(hodler_records):
                        hodler_name = record.get("employee_name", "")
                        logger.info(f"  [{idx}] Hodler: '{hodler_name}' (ID: {record.get('employee_number')})")
                    
                    # Try to match with Hodler Inn records
                    for record in hodler_records:
                        hodler_name = record.get("employee_name", "")
                        if match_names(api_name, hodler_name):
                            emp_id = record.get("employee_number", "")
                            
                            # Check if this employee was already verified (DUPLICATE ENTRY)
                            if emp_id and emp_id in verified_employee_ids:
                                logger.info(f"*** DUPLICATE DETECTED: {api_name} (Employee {emp_id} already verified) - Marking as No Bill ***")
                                try:
                                    # Click "No Bill" on the duplicate entry
                                    if await self.mark_no_bill(entry):
                                        self.results["no_bill"].append({
                                            "name": api_name,
                                            "reason": f"Duplicate entry - Employee {emp_id} already verified",
                                            "employee_id": emp_id
                                        })
                                        logger.info(f"Successfully marked duplicate {api_name} as No Bill")
                                    else:
                                        logger.warning(f"Failed to mark duplicate {api_name} as No Bill")
                                except Exception as e:
                                    logger.error(f"Error marking duplicate as No Bill: {e}")
                                matched = True
                                break
                            
                            # Found a match - fill in the details
                            logger.info(f"*** MATCH FOUND: {api_name} <-> {hodler_name} ***")
                            
                            # Track this employee ID as verified
                            if emp_id:
                                verified_employee_ids.add(emp_id)
                            
                            try:
                                # Add timeout for verify_entry to prevent hanging
                                success = await asyncio.wait_for(
                                    self.verify_entry(
                                        entry,
                                        emp_id,
                                        record.get("room_number", "")
                                    ),
                                    timeout=60  # 60 second timeout per entry
                                )
                                if success:
                                    self.results["verified"].append({
                                        "api_name": api_name,
                                        "hodler_name": hodler_name,
                                        "employee_id": record.get("employee_number"),
                                        "room": record.get("room_number"),
                                        "portal_name": api_name,
                                        "update_name": api_name != hodler_name
                                    })
                                else:
                                    # verify_entry failed but we found a match - still count as verified
                                    # because the name match is confirmed, even if portal update failed
                                    logger.warning(f"verify_entry returned False for {api_name}, but name match confirmed - adding to verified")
                                    self.results["verified"].append({
                                        "api_name": api_name,
                                        "hodler_name": hodler_name,
                                        "employee_id": record.get("employee_number"),
                                        "room": record.get("room_number"),
                                        "portal_name": api_name,
                                        "update_name": api_name != hodler_name,
                                        "portal_update_failed": True  # Flag that portal wasn't updated
                                    })
                            except asyncio.TimeoutError:
                                logger.error(f"TIMEOUT: verify_entry timed out for {api_name} after 60s")
                                self.results["verified"].append({
                                    "api_name": api_name,
                                    "hodler_name": hodler_name,
                                    "employee_id": record.get("employee_number"),
                                    "room": record.get("room_number"),
                                    "portal_name": api_name,
                                    "update_name": api_name != hodler_name,
                                    "portal_update_timeout": True
                                })
                            except Exception as ve:
                                logger.error(f"Error in verify_entry: {str(ve)}")
                                # Still count as verified since name match was confirmed
                                self.results["verified"].append({
                                    "api_name": api_name,
                                    "hodler_name": hodler_name,
                                    "employee_id": record.get("employee_number"),
                                    "room": record.get("room_number"),
                                    "portal_name": api_name,
                                    "update_name": api_name != hodler_name,
                                    "portal_update_error": str(ve)
                                })
                            matched = True
                            break
                    
                    # If no match, check name aliases
                    if not matched and name_aliases:
                        norm_api = normalize_name(api_name).lower()
                        for alias in name_aliases:
                            alias_name = alias.get("portal_name", "").lower()
                            if norm_api == alias_name or api_name.lower() == alias_name:
                                # Found alias match!
                                employee_id = alias.get("employee_number")
                                # Find the hodler record with this employee ID
                                for record in hodler_records:
                                    if record.get("employee_number") == employee_id:
                                        logger.info(f"*** ALIAS MATCH: {api_name} -> {alias.get('employee_name')} ({employee_id}) ***")
                                        try:
                                            success = await self.verify_entry(
                                                entry,
                                                employee_id,
                                                record.get("room_number", "")
                                            )
                                            if success:
                                                self.results["verified"].append({
                                                    "api_name": api_name,
                                                    "hodler_name": alias.get("employee_name"),
                                                    "employee_id": employee_id,
                                                    "room": record.get("room_number"),
                                                    "matched_via": "alias"
                                                })
                                        except Exception as ve:
                                            logger.error(f"Error in verify_entry (alias): {str(ve)}")
                                        matched = True
                                        break
                                break
                    
                    if not matched:
                        # No match found - try to find closest matches for debugging
                        best_matches = find_best_matches(api_name, hodler_records, top_n=3)
                        logger.info(f"No match for '{api_name}' - Best possible matches:")
                        for bm in best_matches:
                            logger.info(f"  - {bm['name']} (ID: {bm['employee_number']}) - Score: {bm['combined_score']:.2f}")
                        
                        # DO NOT automatically click "No Bill" - just report for manual review
                        # The agent should only verify matched entries, not mark unmatched as No Bill
                        # Check if already in missing list (avoid duplicates across passes)
                        already_in_missing = any(m.get("name") == api_name for m in self.results["missing_in_hodler"])
                        if not already_in_missing:
                            logger.info(f"SKIPPING {api_name} - not found in Hodler Inn records (requires manual review)")
                            self.results["missing_in_hodler"].append({
                                "name": api_name,
                                "reason": "Not found in Hodler Inn records - requires manual review",
                                "best_matches": best_matches
                            })
                        else:
                            logger.info(f"SKIPPING {api_name} - already in missing list")
                    
                    # After each entry, wait a moment for page to stabilize
                    await self.page.wait_for_timeout(500)
                
                logger.info(f"Pass {sync_pass} completed: Processed {entries_processed_this_pass} entries")
                
                # If we didn't process any entries this pass, something's wrong - stop
                if entries_processed_this_pass == 0:
                    logger.info("No entries processed in this pass - stopping")
                    break
                
                # Wait for any page updates/refreshes
                await self.page.wait_for_timeout(2000)
                
                # Scroll to bottom to check if more entries appeared (page may have refreshed)
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await self.page.wait_for_timeout(1000)
            
            # Final check: Scroll through entire page to count blue checkmarks
            logger.info("=== FINAL VERIFICATION ===")
            
            # Update progress to indicate final verification phase
            if self.progress_callback:
                try:
                    final_total = len(hodler_records) if hodler_records else 0
                    await self.progress_callback(final_total, final_total, "Completing final verification...")
                    await asyncio.sleep(0.1)
                except Exception as pe:
                    logger.warning(f"Progress callback error in final phase: {pe}")
            
            await self.page.evaluate('window.scrollTo(0, 0)')
            await self.page.wait_for_timeout(1000)
            
            # Load all entries one more time - with maximum iterations to prevent hanging
            # REDUCED from 20 to 5 to prevent hanging
            max_load_more_clicks = 5
            load_more_count = 0
            while load_more_count < max_load_more_clicks:
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await self.page.wait_for_timeout(500)  # Reduced from 1000
                load_more = self.page.get_by_text('Load More', exact=False).first
                try:
                    if await load_more.count() > 0 and await load_more.is_visible():
                        await load_more.click()
                        load_more_count += 1
                        await self.page.wait_for_timeout(1000)  # Reduced from 2000
                    else:
                        break
                except:
                    break
            
            # Skip the slow final verification - we already processed all entries
            # The results are already accurate from the main processing loop
            logger.info(f"Sync completed. Verified: {len(self.results['verified'])}, No Bill: {len(self.results['no_bill'])}")
            # Add version to results
            self.results["agent_version"] = SYNC_AGENT_VERSION
            return self.results
            
        except Exception as e:
            logger.error(f"Sync error: {str(e)}")
            self.results["errors"].append(str(e))
            self.results["agent_version"] = SYNC_AGENT_VERSION
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
            
            # Process up to 12 months of data (to get comprehensive employee list)
            max_periods = min(len(billing_periods), 12)
            logger.info(f"Will process {max_periods} billing periods")
            
            for period_idx, (period_value, period_text) in enumerate(billing_periods[:max_periods]):
                logger.info(f"\n--- Processing period {period_idx + 1}/{max_periods}: {period_text} ---")
                
                try:
                    # ALWAYS navigate fresh to Sign-in Report page for each period
                    # This ensures the dropdown and form are in a clean state
                    logger.info("Navigating to Sign-in Report page...")
                    
                    # Click Sign-in Sheets menu
                    signin_menu = agent.page.locator("a:has-text('Sign-in Sheets')").first
                    if await signin_menu.count() > 0:
                        await signin_menu.click()
                        await agent.page.wait_for_timeout(1000)
                    
                    # Click Sign-in Report
                    signin_report = agent.page.locator("a:has-text('Sign-in Report')").first
                    if await signin_report.count() > 0:
                        await signin_report.click()
                        await agent.page.wait_for_load_state("networkidle", timeout=30000)
                        await agent.page.wait_for_timeout(1500)
                    
                    # Find the billing dropdown
                    billing_dropdown = agent.page.locator("select").nth(1)  # Second dropdown is billing period
                    if await billing_dropdown.count() == 0:
                        billing_dropdown = agent.page.locator("select").first
                    
                    if await billing_dropdown.count() == 0:
                        logger.warning(f"Could not find billing dropdown for period {period_text}")
                        continue
                    
                    # Select the billing period
                    await billing_dropdown.select_option(value=period_value, timeout=10000)
                    await agent.page.wait_for_timeout(500)
                    
                    # Click Create button
                    create_btn = agent.page.locator("input[value='Create'], button:has-text('Create')").first
                    if await create_btn.count() > 0:
                        await create_btn.click()
                        await agent.page.wait_for_load_state("networkidle", timeout=60000)
                        await agent.page.wait_for_timeout(2000)
                        logger.info(f"Report loaded for {period_text}")
                    else:
                        logger.warning(f"Create button not found for {period_text}")
                        continue
                    
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
    """Extract employee data from the Sign-in Report by clicking View Details for each date."""
    employees = []
    
    try:
        # Based on user video: after generating report, page shows dates on left
        # Each date has "View Detail" link - click it to see employee ID and name
        
        # First log what we see on the page
        page_text = await page.inner_text("body")
        logger.info(f"Page content preview: {page_text[:500]}...")
        
        # Look for "View Detail" links (try multiple patterns)
        view_detail_selectors = [
            "a:has-text('View Detail')",
            "a:has-text('View Details')",
            "a:has-text('view detail')",
            "a:has-text('Details')",
            "[onclick*='detail']",
            "a[href*='detail']",
        ]
        
        view_links = None
        link_count = 0
        
        for selector in view_detail_selectors:
            try:
                view_links = page.locator(selector)
                link_count = await view_links.count()
                if link_count > 0:
                    logger.info(f"Found {link_count} View Detail links with selector: {selector}")
                    break
            except:
                continue
        
        if link_count == 0:
            # Try to find any links that might be detail links
            all_links = page.locator("a")
            all_link_count = await all_links.count()
            logger.info(f"No View Detail links found. Total links on page: {all_link_count}")
            
            # Log first 10 links for debugging
            for i in range(min(10, all_link_count)):
                try:
                    link = all_links.nth(i)
                    link_text = await link.inner_text()
                    link_href = await link.get_attribute("href") or ""
                    logger.info(f"  Link {i}: text='{link_text[:30]}', href='{link_href[:50]}'")
                except:
                    continue
            
            # Fallback: try to extract from any visible table
            return await extract_from_any_visible_table(page, seen_ids)
        
        # Process each View Detail link (process ALL dates, not just 15)
        max_links = min(link_count, 31)  # Up to 31 days in a month
        logger.info(f"Processing {max_links} View Detail links...")
        
        for i in range(max_links):
            try:
                # Re-find links each time (DOM may change after navigation)
                view_links = page.locator(view_detail_selectors[0])  # Use the selector that worked
                current_count = await view_links.count()
                
                if i >= current_count:
                    logger.info(f"Only {current_count} links remaining, stopping at {i}")
                    break
                
                link = view_links.nth(i)
                link_text = await link.inner_text()
                logger.info(f"Clicking View Detail {i+1}/{max_links}: '{link_text}'...")
                
                # Click the link
                await link.click()
                await page.wait_for_load_state("networkidle", timeout=30000)
                await page.wait_for_timeout(1000)
                
                # Extract employees from the detail page
                # Look for table with first two columns being ID and Name
                detail_employees = await extract_from_detail_page(page, seen_ids)
                employees.extend(detail_employees)
                logger.info(f"  Extracted {len(detail_employees)} employees from this date")
                
                # Go back to the main report page
                await page.go_back()
                await page.wait_for_load_state("networkidle", timeout=30000)
                await page.wait_for_timeout(800)
                
            except Exception as link_err:
                logger.warning(f"Error processing View Detail link {i}: {link_err}")
                try:
                    await page.go_back()
                    await page.wait_for_timeout(500)
                except:
                    pass
                continue
        
        logger.info(f"Total employees collected from View Details: {len(employees)}")
        
    except Exception as e:
        logger.error(f"Error extracting from report table: {e}")
    
    return employees


async def extract_from_any_visible_table(page, seen_ids: set) -> list:
    """Fallback: Try to extract employee data from any visible table."""
    employees = []
    
    try:
        tables = await page.locator("table").all()
        logger.info(f"Fallback: Found {len(tables)} tables on page")
        
        for table_idx, table in enumerate(tables):
            try:
                rows = await table.locator("tr").all()
                if len(rows) < 2:
                    continue
                
                # Get header to understand column structure
                header_row = rows[0]
                header_text = await header_row.inner_text()
                logger.info(f"Table {table_idx} header: {header_text[:100]}...")
                
                # Process data rows
                for row in rows[1:]:
                    try:
                        cells = await row.locator("td").all()
                        if len(cells) < 2:
                            continue
                        
                        # Get first two columns (ID and Name per user description)
                        col1 = (await cells[0].inner_text()).strip()
                        col2 = (await cells[1].inner_text()).strip()
                        
                        # Skip invalid entries
                        if not col1 or col1 == "NO ID" or col1 == "":
                            continue
                        if not col2 or len(col2) < 2:
                            continue
                        
                        # Validate ID format
                        if len(col1) > 15 or ":" in col1:
                            continue
                        if not col1.replace('-', '').replace('.', '').replace(' ', '').isalnum():
                            continue
                        
                        if col1 not in seen_ids:
                            seen_ids.add(col1)
                            employees.append({
                                "employee_number": col1,
                                "name": format_crew_name(col2),
                                "original_name": col2
                            })
                            logger.info(f"  Found employee: ID={col1}, Name={col2}")
                    except:
                        continue
            except:
                continue
                
    except Exception as e:
        logger.error(f"Error in fallback extraction: {e}")
    
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



async def collect_employees_by_date_range(username: str, password: str, start_date: str, end_date: str) -> dict:
    """
    Collect all employee names and IDs by scanning the daily sign-in entries.
    Goes through each day in the specified date range.
    
    Args:
        username: Portal username
        password: Portal password
        start_date: Start date YYYY-MM-DD
        end_date: End date YYYY-MM-DD
    
    Returns:
        Dict with success status and list of unique employees
    """
    agent = APIGlobalSyncAgent(username, password)
    employees = []
    seen_ids = set()
    seen_names = set()
    
    try:
        await agent.start()
        
        # Calculate dates
        from datetime import datetime, timedelta
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        total_days = (end_dt - start_dt).days + 1
        
        # Step 1: Login
        logger.info("="*50)
        logger.info(f"EMPLOYEE COLLECTION: Scanning {start_date} to {end_date} ({total_days} days)")
        logger.info("="*50)
        if not await agent.login():
            return {
                "success": False,
                "message": "Login failed - check credentials",
                "employees": []
            }
        logger.info("Login successful!")
        
        current_date = start_dt
        day_num = 0
        
        while current_date <= end_dt:
            day_num += 1
            date_str = current_date.strftime("%Y-%m-%d")
            
            logger.info(f"\n--- Day {day_num}/{total_days}: {date_str} ---")
            
            try:
                # Load entries for this date
                entries = await agent.load_entries_for_date(date_str)
                
                if entries:
                    day_new = 0
                    for entry in entries:
                        emp_name = entry.get("name", "").strip()
                        emp_id = entry.get("current_emp_id", "").strip()
                        
                        if not emp_name:
                            continue
                        
                        # Skip if we've seen this ID or name already
                        if emp_id and emp_id != "NO ID":
                            if emp_id in seen_ids:
                                continue
                            seen_ids.add(emp_id)
                            employees.append({
                                "employee_number": emp_id,
                                "name": emp_name
                            })
                            day_new += 1
                        else:
                            # No valid ID, track by name
                            if emp_name.upper() in seen_names:
                                continue
                            seen_names.add(emp_name.upper())
                            employees.append({
                                "employee_number": "",
                                "name": emp_name
                            })
                            day_new += 1
                    
                    logger.info(f"Found {len(entries)} entries, {day_new} new employees")
                else:
                    logger.info("No entries for this date")
                    
            except Exception as day_err:
                logger.warning(f"Error processing {date_str}: {day_err}")
            
            current_date += timedelta(days=1)
        
        logger.info("="*50)
        logger.info(f"COLLECTION COMPLETE: Found {len(employees)} unique employees")
        logger.info("="*50)
        
        return {
            "success": len(employees) > 0,
            "message": f"Found {len(employees)} unique employees from {total_days} days",
            "employees": employees,
            "days_scanned": total_days,
            "start_date": start_date,
            "end_date": end_date
        }
        
    except Exception as e:
        logger.error(f"Error in date range collection: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"Error: {str(e)}", "employees": []}
    finally:
        await agent.stop()


async def collect_employees_daily(username: str, password: str, days_back: int = 30) -> dict:
    """
    Collect all employee names and IDs by scanning the daily sign-in entries.
    Goes through each day for the specified number of days back.
    
    Args:
        username: Portal username
        password: Portal password
        days_back: Number of days to go back (default 30)
    
    Returns:
        Dict with success status and list of unique employees
    """
    agent = APIGlobalSyncAgent(username, password)
    employees = []
    seen_ids = set()
    
    try:
        await agent.start()
        
        # Step 1: Login
        logger.info("="*50)
        logger.info(f"DAILY EMPLOYEE COLLECTION: Scanning {days_back} days")
        logger.info("="*50)
        if not await agent.login():
            return {
                "success": False,
                "message": "Login failed - check credentials",
                "employees": []
            }
        logger.info("Login successful!")
        
        # Calculate date range
        from datetime import datetime, timedelta
        today = datetime.now()
        
        for day_offset in range(days_back):
            target_date = (today - timedelta(days=day_offset + 1))  # Start from yesterday
            date_str = target_date.strftime("%Y-%m-%d")
            
            logger.info(f"\n--- Day {day_offset + 1}/{days_back}: {date_str} ---")
            
            try:
                # Load entries for this date
                entries = await agent.load_entries_for_date(date_str)
                
                if entries:
                    day_new = 0
                    for entry in entries:
                        emp_name = entry.get("name", "")
                        emp_id = entry.get("current_emp_id", "")
                        
                        # Extract employee ID from the entry if available
                        if emp_id and emp_id != "NO ID" and emp_id not in seen_ids:
                            seen_ids.add(emp_id)
                            employees.append({
                                "employee_number": emp_id,
                                "name": emp_name
                            })
                            day_new += 1
                        elif emp_name and emp_name not in [e["name"] for e in employees]:
                            # If no ID but new name, still track it
                            employees.append({
                                "employee_number": "",
                                "name": emp_name
                            })
                            day_new += 1
                    
                    logger.info(f"Found {len(entries)} entries, {day_new} new employees")
                else:
                    logger.info("No entries for this date")
                    
            except Exception as day_err:
                logger.warning(f"Error processing {date_str}: {day_err}")
                continue
        
        logger.info("="*50)
        logger.info(f"DAILY COLLECTION COMPLETE: Found {len(employees)} unique employees")
        logger.info("="*50)
        
        return {
            "success": len(employees) > 0,
            "message": f"Found {len(employees)} unique employees from {days_back} days",
            "employees": employees,
            "days_scanned": days_back
        }
        
    except Exception as e:
        logger.error(f"Error in daily collection: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"Error: {str(e)}", "employees": []}
    finally:
        await agent.stop()



async def collect_employees_from_portal_v2(username: str, password: str) -> dict:
    """
    Collect employee names and IDs from Sign-in Reports (v2 - improved flow).
    
    Based on user video description:
    1. Login to portal
    2. Navigate to Sign-in Reports page  
    3. Select month date range (e.g., Feb 1 - Feb 28 2026)
    4. Click blue "Create" button
    5. Report table shows dates with "View Detail" links
    6. Click each "View Detail" - opens popup with employee data
    7. Extract Employee ID and Name from first two columns
    8. Go back, select previous month
    9. Repeat until Sep 2025 (oldest available data)
    """
    agent = APIGlobalSyncAgent(username, password)
    employees = []
    seen_ids = set()
    
    try:
        await agent.start()
        page = agent.page
        
        # Step 1: Login
        logger.info("="*60)
        logger.info("EMPLOYEE COLLECTION v2: Starting...")
        logger.info("="*60)
        
        if not await agent.login():
            return {"success": False, "message": "Login failed - check credentials", "employees": []}
        logger.info("✓ Login successful!")
        
        await page.wait_for_timeout(2000)
        
        # Step 2: Navigate to Sign-in Reports
        logger.info("\n--- Step 2: Navigate to Sign-in Reports ---")
        
        # Try clicking Sign-in Sheets menu first
        menu_selectors = [
            "a:has-text('Sign-in Sheets')",
            "span:has-text('Sign-in Sheets')",
            "[class*='menu'] >> text=Sign-in",
            "text=Sign-in Sheets"
        ]
        
        for selector in menu_selectors:
            try:
                menu = page.locator(selector).first
                if await menu.count() > 0:
                    await menu.click()
                    await page.wait_for_timeout(1500)
                    logger.info(f"✓ Clicked Sign-in Sheets menu")
                    break
            except:
                continue
        
        # Click Sign-in Report submenu
        report_selectors = [
            "a:has-text('Sign-in Report')",
            "span:has-text('Sign-in Report')",
            "text=Sign-in Report"
        ]
        
        for selector in report_selectors:
            try:
                report = page.locator(selector).first
                if await report.count() > 0:
                    await report.click()
                    await page.wait_for_load_state("networkidle", timeout=30000)
                    await page.wait_for_timeout(2000)
                    logger.info(f"✓ Clicked Sign-in Report")
                    break
            except:
                continue
        
        # Step 3: Select Billing Period from dropdown and process
        logger.info("\n--- Step 3: Select Billing Period and Process ---")
        
        # The page has a "Billing Period" dropdown, not date inputs
        # We need to click the dropdown and select each billing period
        
        billing_period_dropdown = page.locator("select[id*='billingPeriod'], .ui-selectonemenu:has-text('Select'), div[id*='billingPeriod']").first
        
        # Try to find and click the billing period dropdown
        dropdown_selectors = [
            "label:has-text('Billing Period') + div select",
            "label:has-text('Billing Period') ~ div .ui-selectonemenu",
            "div:has-text('Billing Period') select",
            "[id*='billingPeriod']",
            ".ui-selectonemenu-label:has-text('Select')"
        ]
        
        dropdown_clicked = False
        for selector in dropdown_selectors:
            try:
                dropdown = page.locator(selector).first
                if await dropdown.count() > 0:
                    await dropdown.click()
                    await page.wait_for_timeout(1000)
                    logger.info(f"✓ Clicked Billing Period dropdown with: {selector}")
                    dropdown_clicked = True
                    break
            except Exception as e:
                continue
        
        if not dropdown_clicked:
            # Try clicking on the "-Select-" text directly
            try:
                select_label = page.locator("text=-Select-").first
                if await select_label.count() > 0:
                    await select_label.click()
                    await page.wait_for_timeout(1000)
                    logger.info("✓ Clicked -Select- label")
                    dropdown_clicked = True
            except:
                pass
        
        # Get all billing period options
        billing_periods = []
        try:
            # Look for dropdown options
            options = page.locator(".ui-selectonemenu-item, .ui-selectonemenu-list li, select option")
            option_count = await options.count()
            logger.info(f"Found {option_count} billing period options")
            
            for i in range(option_count):
                opt = options.nth(i)
                text = await opt.inner_text()
                if text and text.strip() != "-Select-" and text.strip() != "":
                    billing_periods.append(text.strip())
            
            logger.info(f"Billing periods to process: {billing_periods[:5]}...")  # Show first 5
        except Exception as e:
            logger.error(f"Error getting billing periods: {e}")
        
        # Close dropdown if open
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)
        
        months_processed = 0
        max_months = 12  # Limit to last 12 billing periods
        
        for billing_period in billing_periods[:max_months]:
            logger.info(f"\n>>> Processing Billing Period: {billing_period}")
            
            try:
                # Click on the Billing Period dropdown to open it
                billing_dropdown_selectors = [
                    "label:has-text('Billing Period') + div",
                    "label:has-text('Billing Period') ~ div .ui-selectonemenu",
                    "[id*='billingPeriod']",
                    ".ui-selectonemenu:has-text('-Select-')",
                    "div.ui-selectonemenu"
                ]
                
                dropdown_opened = False
                for selector in billing_dropdown_selectors:
                    try:
                        dropdown = page.locator(selector).first
                        if await dropdown.count() > 0:
                            await dropdown.click()
                            await page.wait_for_timeout(1000)
                            dropdown_opened = True
                            break
                    except:
                        continue
                
                if not dropdown_opened:
                    # Try clicking on visible "-Select-" text
                    try:
                        select_text = page.locator("span:has-text('-Select-'), label:has-text('-Select-')").first
                        await select_text.click()
                        await page.wait_for_timeout(1000)
                        dropdown_opened = True
                    except:
                        pass
                
                if not dropdown_opened:
                    logger.warning(f"Could not open Billing Period dropdown")
                    continue
                
                # Select the billing period from dropdown options
                option_selectors = [
                    f".ui-selectonemenu-item:has-text('{billing_period}')",
                    f"li:has-text('{billing_period}')",
                    f"option:has-text('{billing_period}')"
                ]
                
                option_selected = False
                for selector in option_selectors:
                    try:
                        option = page.locator(selector).first
                        if await option.count() > 0:
                            await option.click()
                            await page.wait_for_timeout(1000)
                            logger.info(f"✓ Selected billing period: {billing_period}")
                            option_selected = True
                            break
                    except:
                        continue
                
                if not option_selected:
                    # Close dropdown and skip this period
                    await page.keyboard.press("Escape")
                    logger.warning(f"Could not select billing period: {billing_period}")
                    continue
                
                # Click Create button
                create_selectors = [
                    "input[value='Create']",
                    "button:has-text('Create')",
                    "input[type='submit'][value='Create']",
                    ".ui-button:has-text('Create')",
                    "button.btn-primary",
                    "input.ui-button[value='Create']"
                ]
                
                create_clicked = False
                for selector in create_selectors:
                    try:
                        create_btn = page.locator(selector).first
                        if await create_btn.count() > 0:
                            await create_btn.click()
                            await page.wait_for_load_state("networkidle", timeout=60000)
                            await page.wait_for_timeout(2000)
                            logger.info("✓ Clicked Create button")
                            create_clicked = True
                            break
                    except:
                        continue
                
                if not create_clicked:
                    logger.warning(f"Could not click Create button for {billing_period}")
                    months_processed += 1
                    continue
                
                # Process all "View Detail" links for this billing period
                month_employees = await process_view_detail_links_v2(page, seen_ids)
                employees.extend(month_employees)
                logger.info(f"✓ Found {len(month_employees)} new employees in {billing_period}")
                
            except Exception as month_err:
                logger.error(f"Error processing {billing_period}: {month_err}")
            
            months_processed += 1
        
        logger.info("\n" + "="*60)
        logger.info(f"COLLECTION COMPLETE: {len(employees)} unique employees from {months_processed} billing periods")
        logger.info("="*60)
        
        return {
            "success": len(employees) > 0,
            "message": f"Found {len(employees)} unique employees from {months_processed} months",
            "employees": employees,
            "months_processed": months_processed
        }
        
    except Exception as e:
        logger.error(f"Error in collect_employees_from_portal_v2: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "message": f"Error: {str(e)}", "employees": []}
    finally:
        await agent.stop()


async def process_view_detail_links_v2(page, seen_ids: set) -> list:
    """Click each View Detail link and extract employee ID + Name."""
    employees = []
    
    try:
        # Find all View Detail links
        view_detail_selectors = [
            "a:has-text('View Detail')",
            "a:has-text('view detail')",  
            "td a:has-text('View')",
            "a:has-text('Details')",
        ]
        
        view_links = None
        link_count = 0
        working_selector = None
        
        for selector in view_detail_selectors:
            try:
                view_links = page.locator(selector)
                link_count = await view_links.count()
                if link_count > 0:
                    working_selector = selector
                    logger.info(f"Found {link_count} View Detail links")
                    break
            except:
                continue
        
        if link_count == 0:
            logger.info("No View Detail links found")
            page_text = await page.inner_text("body")
            logger.info(f"Page preview: {page_text[:500]}...")
            return employees
        
        # Process each View Detail link
        for i in range(link_count):
            try:
                # Re-find links each time (DOM changes)
                view_links = page.locator(working_selector)
                current_count = await view_links.count()
                
                if i >= current_count:
                    break
                
                link = view_links.nth(i)
                logger.info(f"  Clicking View Detail {i+1}/{link_count}")
                
                await link.click()
                await page.wait_for_timeout(1500)
                
                # Extract employees from detail popup/page
                detail_employees = await extract_id_and_name_from_detail_v2(page, seen_ids)
                employees.extend(detail_employees)
                logger.info(f"    → {len(detail_employees)} employees extracted")
                
                # Close popup or go back
                close_selectors = [
                    "button:has-text('Close')",
                    ".ui-dialog-titlebar-close",
                    "a:has-text('Close')",
                    "[aria-label='Close']"
                ]
                
                closed = False
                for selector in close_selectors:
                    try:
                        close_btn = page.locator(selector).first
                        if await close_btn.count() > 0:
                            await close_btn.click()
                            await page.wait_for_timeout(500)
                            closed = True
                            break
                    except:
                        continue
                
                if not closed:
                    try:
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(500)
                    except:
                        pass
                
            except Exception as link_err:
                logger.warning(f"  Error on link {i}: {link_err}")
                continue
        
    except Exception as e:
        logger.error(f"Error processing View Detail links: {e}")
    
    return employees


async def extract_id_and_name_from_detail_v2(page, seen_ids: set) -> list:
    """Extract Employee ID and Name from first two columns of detail table."""
    employees = []
    
    try:
        await page.wait_for_timeout(500)
        
        tables = await page.locator("table").all()
        logger.info(f"    Found {len(tables)} tables")
        
        for table in tables:
            try:
                rows = await table.locator("tr").all()
                if len(rows) < 2:
                    continue
                
                # Process data rows (skip header)
                for row in rows[1:]:
                    try:
                        cells = await row.locator("td").all()
                        if len(cells) < 2:
                            continue
                        
                        # First two columns: ID and Name
                        col1 = (await cells[0].inner_text()).strip()
                        col2 = (await cells[1].inner_text()).strip()
                        
                        # Validate ID
                        if not col1 or col1 == "" or col1.upper() == "NO ID":
                            continue
                        if len(col1) > 15 or ":" in col1:
                            continue
                        if not col1.replace('-', '').replace('.', '').replace(' ', '').isalnum():
                            continue
                        
                        # Validate Name
                        if not col2 or len(col2) < 2:
                            continue
                        
                        # Skip duplicates
                        if col1 in seen_ids:
                            continue
                        
                        seen_ids.add(col1)
                        formatted_name = format_crew_name(col2)
                        employees.append({
                            "employee_number": col1,
                            "name": formatted_name,
                            "original_name": col2
                        })
                        
                    except:
                        continue
                        
            except:
                continue
                
    except Exception as e:
        logger.error(f"Error extracting ID/Name: {e}")
    
    return employees
