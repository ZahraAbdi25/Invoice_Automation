# STEP 3: DESIGN AN AUTOMATION SOLUTION

## Energy Price Monitoring System - Technical Design

---

## 3.1 System Overview

### **What We're Building**

A computer system that automatically monitors energy prices 24/7 and sends alerts when prices are good or bad.

**Simple explanation:**
```
Public Energy API
    ↓ (feeds data)
Python Script
    ├→ Analyzes prices
    ├→ Makes decisions
    ├→ Sends alerts
    └→ Stores data

This runs automatically every 30 minutes, forever.
```

---

## 3.2 Complete System Architecture

### **Visual Diagram of All Components**

```
┌─────────────────────────────────────────────────────────────┐
│                  ENERGY PRICE MONITORING SYSTEM             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  INPUT LAYER:                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Public Energy Price API                             │  │
│  │  (Gets current prices from online)                   │  │
│  │  Example: api.energy.com/prices                      │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │ (JSON with price data)             │
│                       ▼                                    │
│  PROCESSING LAYER:                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Python Script (energy_monitor.py)                   │  │
│  │                                                      │  │
│  │  ├─ Fetch price from API                           │  │
│  │  ├─ Parse JSON response                            │  │
│  │  ├─ Compare to thresholds                          │  │
│  │  ├─ Make BUY/HIGH/NORMAL decision                  │  │
│  │  ├─ Send email alerts (if needed)                  │  │
│  │  └─ Save data to database                          │  │
│  │                                                      │  │
│  └────────────────┬───────────────────────┬────────────┘  │
│                   │                       │               │
│        ┌──────────▼──┐           ┌────────▼────────┐      │
│        │              │           │                 │      │
│        ▼              ▼           ▼                 ▼      │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  DATABASE    │  │  EMAIL SYSTEM    │  │  SCHEDULER   │ │
│  │              │  │                  │  │              │ │
│  │ SQLite DB    │  │ (SMTP)           │  │ Cron Job     │ │
│  │              │  │                  │  │ or           │ │
│  │ Stores:      │  │ Sends alerts to: │  │ APScheduler  │ │
│  │ ├─Timestamp  │  │ ├─Procurement    │  │              │ │
│  │ ├─Price      │  │ ├─Operations     │  │ Runs every   │ │
│  │ ├─Decision   │  │ └─Management     │  │ 30 minutes   │ │
│  │ └─Alert sent │  │                  │  │              │ │
│  │              │  │                  │  │ 24/7/365     │ │
│  └──────────────┘  └──────────────────┘  └──────────────┘ │
│        │                    │                    │         │
│        └────────────────────┼────────────────────┘         │
│                             ▼                             │
│  OUTPUT LAYER:                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Reports & Dashboards                               │  │
│  │  ├─ Daily email report                              │  │
│  │  ├─ Weekly summary                                  │  │
│  │  └─ Historical data for analysis                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3.3 How the System Works - Step by Step

### **The Complete Workflow (Every 30 Minutes)**

```
TIMER TRIGGERS (e.g., 8:00 AM, 8:30 AM, 9:00 AM, etc.)
    │
    ▼
┌─────────────────────────────────────┐
│ STEP 1: FETCH CURRENT PRICE         │
├─────────────────────────────────────┤
│                                     │
│ What happens:                       │
│ ├─ Python script wakes up           │
│ ├─ Calls Public Energy API          │
│ ├─ API returns JSON with price      │
│ └─ Script receives: price=$0.087    │
│                                     │
│ Time: 0.5 seconds                   │
│ Risk: API might be down (rare)      │
│                                     │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ STEP 2: VALIDATE DATA               │
├─────────────────────────────────────┤
│                                     │
│ What happens:                       │
│ ├─ Check price is a valid number    │
│ ├─ Check price is positive          │
│ ├─ Check timestamp is recent        │
│ ├─ Check no errors in JSON          │
│ └─ Confirmed: price is valid ✓      │
│                                     │
│ Time: 0.05 seconds                  │
│                                     │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ STEP 3: APPLY THRESHOLD LOGIC       │
├─────────────────────────────────────┤
│                                     │
│ What happens:                       │
│ ├─ Compare price to thresholds:     │
│ │                                   │
│ │  IF price ($0.087) < $0.08        │
│ │     → Decision = "BUY"            │
│ │     → Alert = "YES"               │
│ │     → Recipient = Procurement     │
│ │                                   │
│ │  ELSE IF price > $0.12            │
│ │     → Decision = "HIGH"           │
│ │     → Alert = "YES"               │
│ │     → Recipient = Operations      │
│ │                                   │
│ │  ELSE (between $0.08-0.12)        │
│ │     → Decision = "NORMAL"         │
│ │     → Alert = "NO"                │
│ │     → Recipient = None            │
│ │                                   │
│ └─ Result: NORMAL (no alert)        │
│                                     │
│ Time: 0.05 seconds                  │
│                                     │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ STEP 4: SEND ALERT (IF NEEDED)      │
├─────────────────────────────────────┤
│                                     │
│ What happens:                       │
│ ├─ In this case: Decision="NORMAL"  │
│ ├─ So: NO ALERT SENT                │
│ │                                   │
│ │ (If decision was BUY or HIGH:)    │
│ │ ├─ Compose email                  │
│ │ ├─ Set recipient                  │
│ │ ├─ Send via SMTP                  │
│ │ └─ Team receives alert            │
│                                     │
│ Time: 1 second (only if alert)      │
│                                     │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ STEP 5: LOG TO DATABASE             │
├─────────────────────────────────────┤
│                                     │
│ What happens:                       │
│ ├─ Save to SQLite database:         │
│ │  ├─ Timestamp: 2026-05-30 08:00   │
│ │  ├─ Price: 0.087                  │
│ │  ├─ Decision: NORMAL              │
│ │  └─ Alert sent: NO                │
│ │                                   │
│ └─ Confirmed: Data saved ✓          │
│                                     │
│ Time: 0.2 seconds                   │
│                                     │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ STEP 6: WAIT FOR NEXT INTERVAL      │
├─────────────────────────────────────┤
│                                     │
│ What happens:                       │
│ ├─ Script puts itself to sleep      │
│ ├─ Waits 30 minutes                 │
│ └─ Then repeats from STEP 1         │
│                                     │
│ Time: 30 minutes                    │
│                                     │
└────────────────┬────────────────────┘
                 │
                 ▼
         STEP 1 AGAIN (REPEAT FOREVER)

TOTAL TIME PER CHECK: ~2 seconds
THEN: Wait 30 minutes
THEN: Repeat
```

---

## 3.4 Technology Stack - What We Use

### **Programming Language: Python**

**Why Python?**
- ✅ Easy to learn and read
- ✅ Great libraries for our tasks
- ✅ Perfect for automating tasks
- ✅ Works on any computer (Windows, Mac, Linux)
- ✅ Free and open source

**Version:** Python 3.9 or higher

---

### **Data Source: Public Energy API**

**What is an API?**
- API = "Application Programming Interface"
- Think of it like a waiter at a restaurant
- You say: "I want the current energy price"
- API says: "Here you go" and returns JSON data

**Example API Call:**
```
Request to: https://api.energy.com/v1/prices/latest
Response (JSON):
{
    "status": "success",
    "price": 0.087,
    "unit": "$/kWh",
    "timestamp": "2026-05-30T08:00:00Z",
    "region": "northeast"
}
```

**Why this API?**
- ✅ Public (free, no login needed)
- ✅ Real-time prices
- ✅ JSON format (easy to parse)
- ✅ Reliable and fast

---

### **Database: SQLite**

**What is SQLite?**
- A small database that stores data in a file
- No need to install a separate database server
- Perfect for small to medium projects
- File is saved as: `energy_prices.db`

**What we store:**
```
Table: prices

Columns:
├─ id (unique identifier)
├─ timestamp (when we checked)
├─ price (the price we got, e.g., 0.087)
├─ decision (BUY, HIGH, or NORMAL)
└─ alert_sent (YES or NO)
```

**Example data:**
```
id | timestamp              | price | decision | alert_sent
─────────────────────────────────────────────────────────────
1  | 2026-05-30 08:00:00   | 0.087 | BUY      | 1
2  | 2026-05-30 08:30:00   | 0.089 | NORMAL   | 0
3  | 2026-05-30 09:00:00   | 0.135 | HIGH     | 1
```

---

### **Email System: SMTP**

**What is SMTP?**
- SMTP = "Simple Mail Transfer Protocol"
- It's the system for sending emails
- We use Gmail's SMTP server (or company email server)

**How it works:**
1. Script creates email message
2. Connects to Gmail SMTP server
3. Authenticates with email credentials
4. Sends email to recipients
5. Email arrives in their inbox

**Example recipients:**
```
For BUY alerts:  procurement@company.com
For HIGH alerts: operations@company.com
For reports:     director@company.com
```

---

### **Scheduler: Cron or APScheduler**

**What does scheduler do?**
- Runs Python script automatically at regular intervals
- No human needs to click anything
- Runs 24/7

**Two options:**

**Option 1: Cron (Linux/Mac)**
```bash
# Edit crontab
crontab -e

# Add this line to run every 30 minutes:
*/30 * * * * /usr/bin/python3 /home/user/energy_monitor.py

# Cron will execute this automatically
```

**Option 2: APScheduler (Python library)**
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(check_price, 'interval', minutes=30)
scheduler.start()
# Runs check_price() every 30 minutes automatically
```

---

## 3.5 Decision Logic - The Rules

### **How Decisions Are Made**

```python
# PRICE THRESHOLDS (configurable)
LOW_THRESHOLD = $0.08/kWh      # Below this = "BUY"
HIGH_THRESHOLD = $0.12/kWh     # Above this = "HIGH"

# DECISION LOGIC
if current_price < LOW_THRESHOLD:
    decision = "BUY"
    
elif current_price > HIGH_THRESHOLD:
    decision = "HIGH"
    
else:
    decision = "NORMAL"
```

### **Decision Examples**

```
Example 1:
├─ Current price: $0.075/kWh
├─ Compare: 0.075 < 0.08? YES
├─ Decision: BUY ✓
├─ Action: Send alert to procurement team
└─ Message: "Price is LOW! Buy energy NOW!"

Example 2:
├─ Current price: $0.087/kWh
├─ Compare: 0.087 < 0.08? NO
├─ Compare: 0.087 > 0.12? NO
├─ Decision: NORMAL
├─ Action: Do nothing
└─ Message: None (no alert)

Example 3:
├─ Current price: $0.145/kWh
├─ Compare: 0.145 < 0.08? NO
├─ Compare: 0.145 > 0.12? YES
├─ Decision: HIGH
├─ Action: Send alert to operations team
└─ Message: "Price is HIGH! Reduce consumption!"
```

---

## 3.6 Data Model - What Gets Stored

### **Database Schema (Table Structure)**

```sql
CREATE TABLE prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    price REAL NOT NULL,
    unit TEXT DEFAULT '$/kWh',
    decision TEXT CHECK(decision IN ('BUY', 'HIGH', 'NORMAL')),
    alert_sent INTEGER DEFAULT 0,
    alert_recipient TEXT,
    api_response_time REAL,
    processing_time REAL
);
```

**Explanation:**
- `id` - Unique number for each record (1, 2, 3, ...)
- `timestamp` - Date and time when price was checked
- `price` - The actual price (e.g., 0.087)
- `unit` - Unit of measurement ($/kWh)
- `decision` - What we decided (BUY, HIGH, or NORMAL)
- `alert_sent` - Was alert sent? (1=yes, 0=no)
- `alert_recipient` - Who did we send it to?
- `api_response_time` - How long API took to respond
- `processing_time` - How long our script took

---

### **Sample Data Over One Day**

```
id | timestamp              | price | decision | alert_sent | alert_recipient
───┼────────────────────────┼───────┼──────────┼────────────┼──────────────────
1  | 2026-05-30 08:00:00   | 0.087 | BUY      | 1          | procurement@...
2  | 2026-05-30 08:30:00   | 0.089 | NORMAL   | 0          | NULL
3  | 2026-05-30 09:00:00   | 0.091 | NORMAL   | 0          | NULL
4  | 2026-05-30 09:30:00   | 0.135 | HIGH     | 1          | operations@...
5  | 2026-05-30 10:00:00   | 0.088 | NORMAL   | 0          | NULL
6  | 2026-05-30 10:30:00   | 0.075 | BUY      | 1          | procurement@...
7  | 2026-05-30 11:00:00   | 0.092 | NORMAL   | 0          | NULL
8  | 2026-05-30 11:30:00   | 0.093 | NORMAL   | 0          | NULL
... (continues all day and night)
```

---

## 3.7 Configuration Parameters

### **System Settings (stored in config.py or .env file)**

```python
# ============ API CONFIGURATION ============
API_ENDPOINT = "https://api.energy.com/prices/latest"
API_TIMEOUT = 10  # seconds
API_RETRY_COUNT = 3
API_RETRY_DELAY = 5  # seconds

# ============ PRICE THRESHOLDS ============
PRICE_BUY_THRESHOLD = 0.08      # $/kWh (below this = BUY)
PRICE_HIGH_THRESHOLD = 0.12     # $/kWh (above this = HIGH)

# ============ ALERT CONFIGURATION ============
ALERT_ENABLED = True
ALERT_BUY = True               # Send alerts for BUY
ALERT_HIGH = True              # Send alerts for HIGH
ALERT_NORMAL = False           # Don't send alerts for NORMAL

# ============ EMAIL CONFIGURATION ============
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "energy-monitor@company.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # From .env file

# Email recipients
EMAIL_PROCUREMENT = ["procurement@company.com", "manager@company.com"]
EMAIL_OPERATIONS = ["operations@company.com"]
EMAIL_REPORT = ["director@company.com"]

# ============ SCHEDULING ============
CHECK_INTERVAL_MINUTES = 30     # Check every 30 minutes
REPORT_TIME = "17:00"           # Daily report at 5 PM

# ============ DATABASE ============
DATABASE_FILE = "energy_prices.db"
DATABASE_BACKUP = "energy_prices_backup.db"

# ============ LOGGING ============
LOG_LEVEL = "INFO"
LOG_FILE = "energy_monitor.log"

# ============ FEATURES ============
ENABLE_DATABASE_LOGGING = True
ENABLE_EMAIL_ALERTS = True
ENABLE_DAILY_REPORTS = True
ENABLE_PRICE_VALIDATION = True
```

---

## 3.8 System Requirements

### **Hardware Requirements**

```
CPU:       Minimal (less than 1% usage)
RAM:       128 MB minimum (even old computers work)
Disk:      100 MB for database + logs
Network:   1 Mbps sufficient (very light usage)
```

**Real-world:** A Raspberry Pi or small cloud VM is plenty powerful

---

### **Software Requirements**

```
Operating System:  Linux, Windows, or Mac
Python:            3.9 or higher
Libraries:         
  ├─ requests (for API calls)
  ├─ apscheduler (for scheduling)
  ├─ pandas (for data analysis)
  └─ sqlite3 (built-in)
```

---

### **Infrastructure Options**

**Option 1: Local Server**
```
What:     Always-on computer in your office
Cost:     $0/month (use existing computer)
Setup:    30 minutes
Pros:     ✓ Full control, ✓ Fast, ✓ No subscription
Cons:     ✗ Uses electricity, ✗ Need reliable power
```

**Option 2: Cloud Virtual Machine**
```
What:     Server running in the cloud (AWS, Azure, GCP)
Cost:     $3-15/month
Setup:    1-2 hours
Pros:     ✓ Always on, ✓ Professional, ✓ Scalable
Cons:     ✗ Requires cloud account knowledge
Examples: AWS EC2, DigitalOcean Droplet, Azure VM
```

**Option 3: Docker Container**
```
What:     Containerized application (portable)
Cost:     Variable (depends on hosting)
Setup:    2-3 hours
Pros:     ✓ Portable, ✓ Easy deployment, ✓ Isolated
Cons:     ✗ Requires Docker knowledge
Hosting:  Docker Hub, Cloud platforms
```

**Recommendation:** Start with Local Server or Cloud VM

---

## 3.9 System Reliability & Error Handling

### **What Happens If Something Goes Wrong?**

**Problem 1: API is Down**
```
Scenario: api.energy.com is temporarily unavailable
Response: 
  ├─ Script detects error
  ├─ Retries 3 times (waits 5 seconds between retries)
  ├─ If still fails: Logs error, waits for next check
  ├─ Continues running (doesn't crash)
  └─ Tries again in 30 minutes
```

**Problem 2: Email Server Issue**
```
Scenario: Can't send alert email
Response:
  ├─ Script detects error
  ├─ Logs the error
  ├─ Continues with next steps
  └─ Alert is marked as "failed to send"
  
Note: Price is still logged to database, so no data loss
```

**Problem 3: Database File Corrupted**
```
Scenario: SQLite database is corrupted
Response:
  ├─ Script detects corruption
  ├─ Uses backup database
  ├─ Sends alert to admin
  └─ System continues running
```

**Problem 4: Network Disconnected**
```
Scenario: No internet connection
Response:
  ├─ Script waits for connection
  ├─ Tries API call with timeout
  ├─ Logs offline status
  └─ Retries when connection returns
```

---

## 3.10 Security Considerations

### **How We Keep It Secure**

**Issue 1: Email Credentials**
```
❌ BAD: Store password in code
    email_password = "mypassword123"  # EXPOSED!

✅ GOOD: Store in environment variable
    email_password = os.getenv("EMAIL_PASSWORD")
    
✅ BETTER: Use Gmail App Password
    - Enable 2-factor authentication
    - Generate app-specific password
    - Use this password instead of main password
```

**Issue 2: API Calls**
```
✅ GOOD: Use HTTPS (encrypted connection)
    https://api.energy.com/prices  ← Encrypted

❌ BAD: Use HTTP (not encrypted)
    http://api.energy.com/prices  ← Can be intercepted
```

**Issue 3: Data Storage**
```
✅ GOOD: Database on secure server
    ├─ Access restricted
    ├─ Regular backups
    └─ Encrypted connection

✅ GOOD: Log files with appropriate permissions
    └─ Only admin can read logs
```

---

## 3.11 Monitoring & Maintenance

### **How We Monitor the System**

**Log File Example:**
```
[2026-05-30 08:00:00] INFO - Starting price check
[2026-05-30 08:00:01] INFO - API call successful
[2026-05-30 08:00:01] INFO - Price received: $0.087/kWh
[2026-05-30 08:00:01] INFO - Decision: BUY
[2026-05-30 08:00:02] INFO - Alert sent to procurement@company.com
[2026-05-30 08:00:03] INFO - Data saved to database
[2026-05-30 08:00:03] INFO - Check complete (2.5 seconds)
```

**Daily Maintenance:**
```
✓ Check log file for errors
✓ Verify database file size
✓ Confirm email alerts working
✓ Review daily report
✓ Backup database (weekly)
```

---

## ✅ STEP 3 Complete!

We've designed the complete automation solution:

✅ **System Architecture** - All components connected
✅ **Process Flow** - 6-step automated workflow
✅ **Technology Stack** - Python, API, SQLite, Email, Scheduler
✅ **Decision Logic** - Clear threshold rules
✅ **Data Model** - Database schema and examples
✅ **Configuration** - All parameters documented
✅ **Requirements** - Hardware and software needed
✅ **Error Handling** - How system stays reliable
✅ **Security** - How we keep data safe
✅ **Monitoring** - How we track the system

---

## Ready for STEP 4?

When you're ready to continue, we'll move to:

### **STEP 4: IMPLEMENT A FUNCTIONAL PROTOTYPE**

This will show:
- Complete Python code (ready to copy-paste)
- Installation instructions
- How to run the code
- Test results
- Live demo walkthrough

**Let me know when you're ready!** 👉 Say **"YES for STEP 4"** and I'll create the final document with working code!

---

**Document Status:** ✅ COMPLETE  
**Date:** May 2026  
**Version:** 1.0
