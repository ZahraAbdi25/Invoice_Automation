#!/usr/bin/env python3
"""
Energy Price Monitoring Dashboard
Real-time web interface for German electricity prices
"""

from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

# Database file
DATABASE_FILE = "germany_energy_prices.db"

# ============================================================
#              DATABASE QUERY FUNCTIONS
# ============================================================

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_current_price():
    """Get the most recent price"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT price_eur_mwh, decision, region, timestamp
            FROM prices
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'price': round(result['price_eur_mwh'], 2),
                'decision': result['decision'],
                'region': result['region'],
                'timestamp': result['timestamp']
            }
        return None
    except Exception as e:
        print(f"Error getting current price: {e}")
        return None

def get_today_statistics():
    """Get today's price statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                MIN(price_eur_mwh) as min_price,
                MAX(price_eur_mwh) as max_price,
                AVG(price_eur_mwh) as avg_price,
                COUNT(*) as total_checks
            FROM prices
            WHERE DATE(timestamp) = DATE('now')
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result['total_checks'] > 0:
            return {
                'min': round(result['min_price'], 2),
                'max': round(result['max_price'], 2),
                'avg': round(result['avg_price'], 2),
                'total': result['total_checks']
            }
        return None
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return None

def get_alert_summary():
    """Get summary of alerts today"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT decision, COUNT(*) as count
            FROM prices
            WHERE DATE(timestamp) = DATE('now')
            GROUP BY decision
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        summary = {'BUY': 0, 'HIGH': 0, 'NORMAL': 0}
        for row in results:
            summary[row['decision']] = row['count']
        
        return summary
    except Exception as e:
        print(f"Error getting alert summary: {e}")
        return {'BUY': 0, 'HIGH': 0, 'NORMAL': 0}

def get_chart_data(hours=24):
    """Get price data for chart (last N hours)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get data from last N hours
        cursor.execute(f'''
            SELECT timestamp, price_eur_mwh, decision, region
            FROM prices
            WHERE timestamp > datetime('now', '-{hours} hours')
            ORDER BY timestamp ASC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        data = {
            'labels': [],
            'prices': [],
            'decisions': []
        }
        
        for row in results:
            # Format timestamp for display
            dt = datetime.fromisoformat(row['timestamp'])
            data['labels'].append(dt.strftime('%H:%M'))
            data['prices'].append(round(row['price_eur_mwh'], 2))
            data['decisions'].append(row['decision'])
        
        return data
    except Exception as e:
        print(f"Error getting chart data: {e}")
        return {'labels': [], 'prices': [], 'decisions': []}

def get_regional_data():
    """Get latest price for each region"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT region, price_eur_mwh, decision, timestamp
            FROM prices
            WHERE (region, timestamp) IN (
                SELECT region, MAX(timestamp)
                FROM prices
                WHERE DATE(timestamp) = DATE('now')
                GROUP BY region
            )
            ORDER BY price_eur_mwh DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        regions = []
        for row in results:
            regions.append({
                'name': row['region'],
                'price': round(row['price_eur_mwh'], 2),
                'decision': row['decision'],
                'timestamp': row['timestamp']
            })
        
        return regions
    except Exception as e:
        print(f"Error getting regional data: {e}")
        return []

def get_recent_prices(limit=20):
    """Get recent price records"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, price_eur_mwh, region, decision, alert_sent, alert_recipient
            FROM prices
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        records = []
        for row in results:
            records.append({
                'timestamp': row['timestamp'],
                'price': round(row['price_eur_mwh'], 2),
                'region': row['region'],
                'decision': row['decision'],
                'alert': '✅' if row['alert_sent'] else '❌',
                'recipient': row['alert_recipient'] or '-'
            })
        
        return records
    except Exception as e:
        print(f"Error getting recent prices: {e}")
        return []

# ============================================================
#              FLASK ROUTES
# ============================================================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/current-price')
def api_current_price():
    """API endpoint for current price"""
    data = get_current_price()
    return jsonify(data or {})

@app.route('/api/statistics')
def api_statistics():
    """API endpoint for today's statistics"""
    stats = get_today_statistics()
    alerts = get_alert_summary()
    return jsonify({
        'statistics': stats,
        'alerts': alerts
    })

@app.route('/api/chart-data')
def api_chart_data():
    """API endpoint for chart data"""
    data = get_chart_data(24)
    return jsonify(data)

@app.route('/api/regional-data')
def api_regional_data():
    """API endpoint for regional data"""
    data = get_regional_data()
    return jsonify(data)

@app.route('/api/recent-prices')
def api_recent_prices():
    """API endpoint for recent price records"""
    data = get_recent_prices(20)
    return jsonify(data)

@app.route('/api/dashboard-summary')
def api_dashboard_summary():
    """API endpoint for complete dashboard summary"""
    return jsonify({
        'current_price': get_current_price(),
        'statistics': get_today_statistics(),
        'alerts': get_alert_summary(),
        'regions': get_regional_data(),
        'recent': get_recent_prices(10)
    })

# ============================================================
#              ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================
#              MAIN EXECUTION
# ============================================================

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("⚡⚡⚡ GERMAN ELECTRICITY PRICE DASHBOARD ⚡⚡⚡")
    print("=" * 70)
    print("")
    print("🌐 Dashboard URL: http://localhost:5000")
    print("📊 API Base: http://localhost:5000/api/")
    print("")
    print("Available Endpoints:")
    print("  📈 /api/current-price       - Current price and decision")
    print("  📊 /api/statistics           - Today's statistics")
    print("  📉 /api/chart-data           - Last 24 hours data for charts")
    print("  🗺️  /api/regional-data       - Regional breakdown")
    print("  📋 /api/recent-prices        - Recent 20 records")
    print("  💾 /api/dashboard-summary    - Complete summary")
    print("")
    print("=" * 70)
    print("")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
