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


SYNC_AGENT_VERSION = "2026-03-05-v6"  # Added detailed name comparison logging

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
                # Search for row at current scroll position
                rows = self.page.locator('tr')
                row_count = await rows.count()
                
                for i in range(row_count):
                    row = rows.nth(i)
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
            
            # Wait longer for auto-save to complete
            logger.info("Waiting 5 seconds for Employee ID to save...")
            await self.page.wait_for_timeout(5000)
            
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
                
                # Wait longer for Room Number to save and blue checkmark to appear
                logger.info("Waiting 5 seconds for Room Number to save...")
                await self.page.wait_for_timeout(5000)
                
                # === Step 6: Check for blue checkmark (verify save was successful) ===
                logger.info("Step 6: Checking for blue checkmark...")
                
                # Re-find the row and check status
                try:
                    rows = self.page.locator('tr')
                    for i in range(await rows.count()):
                        row = rows.nth(i)
                        row_text = await row.inner_text()
                        if search_name.upper() in row_text.upper():
                            row_html = await row.inner_html()
                            if 'color:blue' in row_html.lower() or 'ui-icon-check' in row_html or 'checkmark' in row_html.lower() or 'color:green' in row_html.lower():
                                logger.info("✓ Blue checkmark detected - save successful!")
                                break
                            elif 'color:red' in row_html.lower() or 'ui-icon-alert' in row_html:
                                logger.warning("✗ Red status still showing - save may have failed")
                                break
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
            
            # Wait for page to stabilize before processing next entry
            await self.page.wait_for_timeout(2000)
            
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
    
    async def run_sync(self, hodler_records: list, target_date: str = None, name_aliases: list = None) -> dict:
        """
        Run the full sync process.
        
        Args:
            hodler_records: List of dicts with 'employee_name', 'employee_number', 'room_number'
            target_date: Optional date in format 'YYYY-MM-DD' to sync for a specific date
            name_aliases: Optional list of name mappings from portal names to employee IDs
        
        Returns:
            Results dict with verified, no_bill, missing entries
        """
        if name_aliases is None:
            name_aliases = []
        
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
                
                if len(entries_needing_work) == 0 and len(red_entries) == 0:
                    if len(blue_entries) == len(entries):
                        logger.info("All entries have blue checkmarks - sync complete!")
                    else:
                        logger.info("No entries need verification - all have employee IDs filled")
                    break
                
                # Step 5: Process each entry that needs verification
                entries_processed_this_pass = 0
                for entry in entries:
                    api_name = entry["name"]
                    
                    # Check if entry is already verified on the portal (BLUE ✓ checkmark)
                    already_verified_on_portal = entry.get("verified") or entry.get("has_blue_status")
                    
                    if already_verified_on_portal:
                        # Entry is already verified on portal - check if it matches a Hodler Inn record
                        # If so, count it as verified without re-processing
                        logger.info(f"ALREADY VERIFIED ON PORTAL: {api_name} - checking if matches Hodler Inn record...")
                        
                        matched_hodler = False
                        for record in hodler_records:
                            hodler_name = record.get("employee_name", "")
                            if match_names(api_name, hodler_name):
                                logger.info(f"*** MATCH FOUND (already verified): {api_name} <-> {hodler_name} ***")
                                self.results["verified"].append({
                                    "api_name": api_name,
                                    "hodler_name": hodler_name,
                                    "employee_id": record.get("employee_number"),
                                    "room": record.get("room_number"),
                                    "portal_name": api_name,
                                    "update_name": api_name != hodler_name,
                                    "pre_verified": True  # Mark that it was already verified on portal
                                })
                                matched_hodler = True
                                break
                        
                        if not matched_hodler:
                            logger.info(f"Already verified on portal but no Hodler match: {api_name}")
                        
                        continue  # Skip to next entry - no portal interaction needed
                    
                    # Entry is NOT verified on portal - needs processing
                    # Process entries that:
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
                            # Found a match - fill in the details
                            logger.info(f"*** MATCH FOUND: {api_name} <-> {hodler_name} ***")
                            try:
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
                        
                        # Mark as No Bill
                        logger.info(f"Marking {api_name} as No Bill")
                        if await self.mark_no_bill(entry):
                            self.results["no_bill"].append({
                                "name": api_name,
                                "best_matches": best_matches
                            })
                        else:
                            self.results["missing_in_hodler"].append({
                                "name": api_name,
                                "reason": "Could not find matching employee and No Bill failed",
                                "best_matches": best_matches
                            })
                    
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
            await self.page.evaluate('window.scrollTo(0, 0)')
            await self.page.wait_for_timeout(1000)
            
            # Load all entries one more time
            while True:
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await self.page.wait_for_timeout(1000)
                load_more = self.page.get_by_text('Load More', exact=False).first
                try:
                    if await load_more.count() > 0 and await load_more.is_visible():
                        await load_more.click()
                        await self.page.wait_for_timeout(2000)
                    else:
                        break
                except:
                    break
            
            final_entries = await self.get_signin_sheet_entries()
            final_red = len([e for e in final_entries if e.get("has_red_status") and not e.get("verified")])
            final_blue = len([e for e in final_entries if e.get("has_blue_status") or e.get("verified")])
            logger.info(f"Final count: Total={len(final_entries)}, Red={final_red}, Blue={final_blue}")
            
            # Check for Hodler records not found in API Global
            for record in hodler_records:
                hodler_name = record.get("employee_name", "")
                found = any(match_names(e["name"], hodler_name) for e in final_entries)
                if not found:
                    self.results["missing_in_hodler"].append({
                        "name": hodler_name,
                        "employee_id": record.get("employee_number"),
                        "room": record.get("room_number"),
                        "note": "Guest checked in at Hodler Inn but not listed in API Global portal"
                    })
            
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
