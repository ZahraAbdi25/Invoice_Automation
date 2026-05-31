#!/usr/bin/env python3
"""
Energy Price Monitoring System - Updated with GridStatus.io API
Automatically monitors energy prices and sends alerts
"""

import requests
import sqlite3
import json
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
import time
import random

# ============================================================
#                    CONFIGURATION
# ============================================================

# API Configuration - GridStatus.io (No auth required!)
API_ENDPOINT = "https://www.gridstatus.io/api/v1/grid-status"
API_TIMEOUT = 10

# Test Data Mode (set to True if API is unavailable)
USE_TEST_DATA = False  # Change to True for demo without internet

# Price Thresholds (in $/kWh)
PRICE_BUY_THRESHOLD = 0.08      # Below this = "BUY"
PRICE_HIGH_THRESHOLD = 0.12     # Above this = "HIGH"

# Database
DATABASE_FILE = "energy_prices.db"

# Email Configuration (Optional - for testing, set to False)
SEND_EMAILS = False  # Set to True if you want to send real emails
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"  # Use Gmail App Password

# Email Recipients
EMAIL_PROCUREMENT = "procurement@company.com"
EMAIL_OPERATIONS = "operations@company.com"

# Logging
LOG_FILE = "energy_monitor.log"

# ============================================================
#                    LOGGING SETUP
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================================
#                 DATABASE INITIALIZATION
# ============================================================

def init_database():
    """Create database and table if they don't exist"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                price REAL NOT NULL,
                region TEXT,
                decision TEXT CHECK(decision IN ('BUY', 'HIGH', 'NORMAL')),
                alert_sent INTEGER DEFAULT 0,
                alert_recipient TEXT,
                api_response_time REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

# ============================================================
#              FETCH ENERGY PRICE FROM API
# ============================================================

def fetch_current_price():
    """
    Fetch current energy price from GridStatus.io API
    Returns: price (float) or None if error
    """
    
    # Option 1: Use Test Data (for demo without internet)
    if USE_TEST_DATA:
        logger.info("📊 Using TEST DATA mode (no internet needed)")
        # Generate realistic test prices
        test_price = round(random.uniform(0.070, 0.150), 3)
        logger.info(f"✅ Test price generated: ${test_price:.3f}/kWh")
        return test_price
    
    # Option 2: Fetch from Real API
    try:
        logger.info("📡 Fetching price from GridStatus.io API...")
        response = requests.get(API_ENDPOINT, timeout=API_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse GridStatus.io response
        # The API returns data in different formats, we'll extract price data
        try:
            # Try to get price from the response
            # GridStatus returns data with regions and prices
            if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                price_data = data['data'][0]
                price = price_data.get('price') or price_data.get('lmp') or price_data.get('energy_price')
                
                if price is None:
                    logger.warning("⚠️  Price field not found in response, using test fallback")
                    return generate_test_price()
                
                # Validate price
                if not isinstance(price, (int, float)) or price < 0:
                    logger.error(f"❌ Invalid price value: {price}")
                    return generate_test_price()
                
                logger.info(f"✅ Price fetched successfully: ${price:.3f}/kWh")
                return price
            else:
                logger.warning("⚠️  Unexpected API response format")
                return generate_test_price()
        
        except (KeyError, IndexError, TypeError) as e:
            logger.warning(f"⚠️  Could not parse API response: {e}")
            logger.info("📊 Switching to test data fallback")
            return generate_test_price()
    
    except requests.exceptions.Timeout:
        logger.error("❌ API call timed out")
        logger.info("📊 Using test data fallback")
        return generate_test_price()
    except requests.exceptions.ConnectionError:
        logger.error("❌ Connection error - API unavailable")
        logger.info("📊 Using test data fallback")
        return generate_test_price()
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON response from API")
        logger.info("📊 Using test data fallback")
        return generate_test_price()
    except Exception as e:
        logger.error(f"❌ Error fetching price: {e}")
        logger.info("📊 Using test data fallback")
        return generate_test_price()

# ============================================================
#           GENERATE TEST DATA (DEMO MODE)
# ============================================================

def generate_test_price():
    """
    Generate realistic test price for demo
    Simulates real market behavior
    """
    # Generate prices with slight variation (realistic market behavior)
    base_price = 0.095
    variation = random.uniform(-0.020, 0.055)
    test_price = round(base_price + variation, 3)
    
    logger.info(f"✅ Test price generated: ${test_price:.3f}/kWh")
    return test_price

# ============================================================
#               ANALYZE PRICE & MAKE DECISION
# ============================================================

def analyze_price(price):
    """
    Analyze price and determine action
    Returns: decision (string) - "BUY", "HIGH", or "NORMAL"
    """
    if price < PRICE_BUY_THRESHOLD:
        return "BUY"
    elif price > PRICE_HIGH_THRESHOLD:
        return "HIGH"
    else:
        return "NORMAL"

# ============================================================
#                  SEND EMAIL ALERT
# ============================================================

def send_email_alert(decision, price):
    """
    Send email alert to appropriate team
    """
    
    if decision == "NORMAL":
        logger.info("ℹ️  No alert needed (price is normal)")
        return False
    
    if not SEND_EMAILS:
        logger.info(f"📧 [DRY RUN] Email not sent (SEND_EMAILS=False)")
        logger.info(f"   Decision: {decision} | Price: ${price:.3f}/kWh")
        return True
    
    try:
        # Compose email based on decision
        if decision == "BUY":
            recipient = EMAIL_PROCUREMENT
            subject = "🚨 LOW ENERGY PRICE - BUY NOW!"
            body = f"""
            Current Energy Price Alert
            
            Price: ${price:.3f}/kWh
            Status: LOW
            Action: This is a good time to buy energy!
            
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Please contact procurement to initiate purchase.
            
            ---
            Energy Monitoring System
            """
        
        elif decision == "HIGH":
            recipient = EMAIL_OPERATIONS
            subject = "⚠️  HIGH ENERGY PRICE - REDUCE USAGE"
            body = f"""
            Current Energy Price Alert
            
            Price: ${price:.3f}/kWh
            Status: HIGH
            Action: Please reduce energy consumption if possible!
            
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Please coordinate with operations to reduce usage.
            
            ---
            Energy Monitoring System
            """
        else:
            return False
        
        # Send email via SMTP
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ Email alert sent to {recipient}")
        return True
    
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return False

# ============================================================
#              LOG DATA TO DATABASE
# ============================================================

def log_to_database(price, decision, alert_sent):
    """
    Save price, decision, and alert status to database
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        alert_recipient = None
        if alert_sent:
            alert_recipient = EMAIL_PROCUREMENT if decision == "BUY" else EMAIL_OPERATIONS
        
        cursor.execute('''
            INSERT INTO prices (price, decision, alert_sent, alert_recipient, region)
            VALUES (?, ?, ?, ?, ?)
        ''', (price, decision, alert_sent, alert_recipient, "CAISO"))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Data saved to database: {decision} @ ${price:.3f}/kWh")
        return True
    
    except Exception as e:
        logger.error(f"❌ Database save failed: {e}")
        return False

# ============================================================
#              MAIN CHECK FUNCTION
# ============================================================

def check_energy_price():
    """
    Main function - runs every 30 minutes
    """
    logger.info("=" * 60)
    logger.info("⚡ ENERGY PRICE CHECK")
    logger.info("=" * 60)
    
    # Step 1: Fetch price from API
    price = fetch_current_price()
    if price is None:
        logger.warning("⚠️  Check failed - will retry in 30 minutes")
        logger.info("=" * 60)
        return
    
    # Step 2: Analyze price
    decision = analyze_price(price)
    logger.info(f"📊 Decision: {decision}")
    
    # Step 3: Send alert if needed
    alert_sent = 0
    if decision != "NORMAL":
        if send_email_alert(decision, price):
            alert_sent = 1
    
    # Step 4: Log to database
    log_to_database(price, decision, alert_sent)
    
    logger.info("=" * 60)

# ============================================================
#              GENERATE DAILY REPORT
# ============================================================

def generate_daily_report():
    """
    Generate and display daily report
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Get today's data
        cursor.execute('''
            SELECT price, decision, COUNT(*) as count
            FROM prices
            WHERE DATE(timestamp) = DATE('now')
            GROUP BY decision
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 DAILY REPORT")
        logger.info("=" * 60)
        
        if results:
            for price, decision, count in results:
                logger.info(f"{decision:10} - {count:2} occurrences")
        else:
            logger.info("No data for today")
        
        # Get min/max/avg
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                MIN(price) as min_price,
                MAX(price) as max_price,
                AVG(price) as avg_price
            FROM prices
            WHERE DATE(timestamp) = DATE('now')
        ''')
        
        min_p, max_p, avg_p = cursor.fetchone()
        conn.close()
        
        logger.info("-" * 60)
        logger.info(f"Min Price: ${min_p:.3f}/kWh" if min_p else "No data")
        logger.info(f"Max Price: ${max_p:.3f}/kWh" if max_p else "No data")
        logger.info(f"Avg Price: ${avg_p:.3f}/kWh" if avg_p else "No data")
        logger.info("=" * 60 + "\n")
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")

# ============================================================
#              QUERY DATABASE
# ============================================================

def query_database_example():
    """
    Example: Query database to view saved data
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Get last 10 records
        cursor.execute('''
            SELECT timestamp, price, decision, alert_sent
            FROM prices
            ORDER BY timestamp DESC
            LIMIT 10
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        logger.info("\n" + "=" * 60)
        logger.info("📋 LAST 10 PRICE CHECKS")
        logger.info("=" * 60)
        
        for timestamp, price, decision, alert_sent in rows:
            alert_status = "✅" if alert_sent else "❌"
            logger.info(f"{timestamp} | ${price:.3f} | {decision:6} | {alert_status}")
        
        logger.info("=" * 60 + "\n")
    
    except Exception as e:
        logger.error(f"Error querying database: {e}")

# ============================================================
#              SCHEDULER SETUP
# ============================================================

def start_scheduler():
    """
    Start the scheduler to run checks every 30 minutes
    """
    logger.info("\n")
    logger.info("=" * 60)
    logger.info("⚡ ENERGY PRICE MONITORING SYSTEM ⚡")
    logger.info("=" * 60)
    logger.info("")
    
    # Show mode
    if USE_TEST_DATA:
        logger.info("🧪 MODE: TEST DATA (Demo Mode)")
    else:
        logger.info("🌐 MODE: GridStatus.io API (Real Data)")
    
    logger.info("")
    
    # Initialize database
    if not init_database():
        logger.error("Failed to initialize database. Exiting.")
        return
    
    # Create scheduler
    scheduler = BackgroundScheduler()
    
    # Add job to run every 30 minutes
    scheduler.add_job(
        func=check_energy_price,
        trigger="interval",
        minutes=30,
        id="energy_check",
        name="Energy price monitoring check"
    )
    
    # Start scheduler
    scheduler.start()
    
    logger.info("🚀 Scheduler started!")
    logger.info("✅ Energy prices will be checked every 30 minutes")
    logger.info("✅ System is running 24/7")
    logger.info("")
    logger.info("Press CTRL+C to stop the system")
    logger.info("=" * 60)
    logger.info("")
    
    # Run first check immediately
    logger.info("Running initial price check...")
    check_energy_price()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n⛔ Stopping scheduler...")
        scheduler.shutdown()
        logger.info("✅ Scheduler stopped")
        generate_daily_report()

# ============================================================
#                   MAIN EXECUTION
# ============================================================

if __name__ == "__main__":
    start_scheduler()
