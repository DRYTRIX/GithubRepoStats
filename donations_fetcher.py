"""Fetcher for donation statistics from PayPal and Buy Me a Coffee."""

import requests
import base64
import re
from typing import Dict, Any, Optional
from cache_manager import CacheManager


class DonationsFetcher:
    """Fetches donation statistics from PayPal and Buy Me a Coffee."""
    
    def __init__(
        self,
        paypal_client_id: Optional[str] = None,
        paypal_client_secret: Optional[str] = None,
        buymeacoffee_username: Optional[str] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        """
        Initialize donations fetcher.
        
        Args:
            paypal_client_id: PayPal API client ID
            paypal_client_secret: PayPal API client secret
            buymeacoffee_username: Buy Me a Coffee username
            cache_manager: Optional cache manager instance
        """
        self.paypal_client_id = paypal_client_id
        self.paypal_client_secret = paypal_client_secret
        self.buymeacoffee_username = buymeacoffee_username
        self.cache = cache_manager
        self.session = requests.Session()
    
    def _get_paypal_access_token(self) -> Optional[str]:
        """
        Get PayPal OAuth access token.
        
        Returns:
            Access token or None if authentication fails
        """
        if not self.paypal_client_id or not self.paypal_client_secret:
            return None
        
        # Use sandbox or production endpoint
        # For production: https://api.paypal.com
        # For sandbox: https://api.sandbox.paypal.com
        base_url = "https://api.paypal.com"
        
        auth_string = f"{self.paypal_client_id}:{self.paypal_client_secret}"
        auth_bytes = auth_string.encode("ascii")
        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {"grant_type": "client_credentials"}
        
        try:
            response = self.session.post(
                f"{base_url}/v1/oauth2/token",
                headers=headers,
                data=data,
                timeout=10
            )
            response.raise_for_status()
            token_data = response.json()
            return token_data.get("access_token")
        except Exception:
            return None
    
    def get_paypal_donations(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get PayPal donation totals.
        
        Note: This requires PayPal API credentials and appropriate permissions.
        The Transaction Search API can be used to find donation transactions.
        
        Args:
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            
        Returns:
            Dictionary with donation statistics
        """
        if not self.paypal_client_id or not self.paypal_client_secret:
            return {
                "total": 0,
                "currency": "USD",
                "error": "PayPal credentials not configured"
            }
        
        access_token = self._get_paypal_access_token()
        if not access_token:
            return {
                "total": 0,
                "currency": "USD",
                "error": "Failed to authenticate with PayPal"
            }
        
        base_url = "https://api.paypal.com"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Use Transaction Search API
        # Note: This is a simplified example. Full implementation would need
        # to handle pagination and filter for donation transactions specifically
        params = {
            "transaction_status": "S",
            "transaction_type": "T1107",  # Donation transaction type
        }
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        try:
            # Note: Actual implementation would need to handle the full
            # Transaction Search API which may require different endpoints
            # This is a placeholder structure
            response = self.session.get(
                f"{base_url}/v1/reporting/transactions",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Process transactions and sum donation amounts
                # This is simplified - actual implementation would need
                # to parse the transaction details properly
                total = 0
                currency = "USD"
                
                return {
                    "total": total,
                    "currency": currency,
                    "transaction_count": 0
                }
            else:
                return {
                    "total": 0,
                    "currency": "USD",
                    "error": f"API error: {response.status_code}"
                }
        
        except Exception as e:
            return {
                "total": 0,
                "currency": "USD",
                "error": str(e)
            }
    
    def get_buymeacoffee_donations(self) -> Dict[str, Any]:
        """
        Get Buy Me a Coffee donation totals by scraping the public page.
        
        Note: Buy Me a Coffee doesn't have a public API for donation totals.
        This scrapes the public profile page to extract total donations.
        
        Args:
            username: Buy Me a Coffee username
            
        Returns:
            Dictionary with donation statistics
        """
        if not self.buymeacoffee_username:
            return {
                "total": 0,
                "currency": "USD",
                "error": "Buy Me a Coffee username not configured"
            }
        
        # Set headers to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        try:
            url = f"https://www.buymeacoffee.com/{self.buymeacoffee_username}"
            response = self.session.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                # Try multiple patterns to find total donations
                # Pattern 1: Look for "Total earned" or similar text with amount
                # Common patterns in BMC HTML
                patterns = [
                    r'total[_\s]*(?:earned|raised|donations?)[\s:]*\$?([\d,]+\.?\d*)',
                    r'\$([\d,]+\.?\d*)[\s]*total',
                    r'([\d,]+\.?\d*)[\s]*(?:coffees?|donations?)',
                    r'data-total=["\']([\d,]+\.?\d*)["\']',
                    r'"total":\s*([\d,]+\.?\d*)',
                    r'Total[:\s]+\$?([\d,]+\.?\d*)',
                ]
                
                total_amount = 0
                currency = "USD"
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    if matches:
                        # Try to extract the largest number (likely the total)
                        amounts = []
                        for match in matches:
                            try:
                                # Remove commas and convert to float
                                amount_str = match.replace(',', '').strip()
                                amount = float(amount_str)
                                amounts.append(amount)
                            except ValueError:
                                continue
                        
                        if amounts:
                            # Take the largest amount as it's likely the total
                            total_amount = max(amounts)
                            break
                
                # Pattern 2: Look for JSON data in script tags
                if total_amount == 0:
                    script_pattern = r'<script[^>]*>(.*?)</script>'
                    scripts = re.findall(script_pattern, html, re.DOTALL | re.IGNORECASE)
                    
                    for script in scripts:
                        # Look for JSON with donation/earnings data
                        json_patterns = [
                            r'"totalEarned":\s*([\d,]+\.?\d*)',
                            r'"total":\s*([\d,]+\.?\d*)',
                            r'"earnings":\s*([\d,]+\.?\d*)',
                            r'"amount":\s*([\d,]+\.?\d*)',
                        ]
                        
                        for json_pattern in json_patterns:
                            matches = re.findall(json_pattern, script, re.IGNORECASE)
                            if matches:
                                try:
                                    amounts = [float(m.replace(',', '')) for m in matches]
                                    if amounts:
                                        total_amount = max(amounts)
                                        break
                                except ValueError:
                                    continue
                        
                        if total_amount > 0:
                            break
                
                # Pattern 3: Look for specific BMC widget data
                if total_amount == 0:
                    widget_pattern = r'bmc-widget[^>]*data-total=["\']([\d,]+\.?\d*)["\']'
                    widget_matches = re.findall(widget_pattern, html, re.IGNORECASE)
                    if widget_matches:
                        try:
                            total_amount = float(widget_matches[0].replace(',', ''))
                        except ValueError:
                            pass
                
                if total_amount > 0:
                    return {
                        "total": total_amount,
                        "currency": currency,
                        "source": "scraped"
                    }
                else:
                    return {
                        "total": 0,
                        "currency": "USD",
                        "error": "Could not find donation total on page. The page structure may have changed."
                    }
            else:
                return {
                    "total": 0,
                    "currency": "USD",
                    "error": f"Failed to fetch page: {response.status_code}"
                }
        
        except Exception as e:
            return {
                "total": 0,
                "currency": "USD",
                "error": str(e)
            }
    
    def get_all_donations(self) -> Dict[str, Any]:
        """
        Get total donations from all sources.
        
        Returns:
            Dictionary with combined donation statistics
        """
        paypal = self.get_paypal_donations()
        buymeacoffee = self.get_buymeacoffee_donations()
        
        # Sum totals (assuming same currency for simplicity)
        total = 0
        currency = "USD"
        
        if "error" not in paypal:
            total += paypal.get("total", 0)
            currency = paypal.get("currency", "USD")
        
        if "error" not in buymeacoffee:
            total += buymeacoffee.get("total", 0)
        
        return {
            "total": total,
            "currency": currency,
            "paypal": paypal,
            "buymeacoffee": buymeacoffee
        }
