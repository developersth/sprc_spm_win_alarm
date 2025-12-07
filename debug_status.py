"""
Debug script to check database status values
"""

import json
from database import DatabaseManager

# Load config
with open('app_config.json', 'r') as f:
    config = json.load(f)

# Connect to database
db = DatabaseManager(config)

# Query to check distinct status values
cursor = db.connection.cursor()
cursor.execute("SELECT DISTINCT status FROM alarm_history ORDER BY status")
statuses = cursor.fetchall()
print("Distinct status values in database:")
for status in statuses:
    print(f"  - '{status[0]}'")

# Check null status
cursor.execute("SELECT COUNT(*) FROM alarm_history WHERE status IS NULL")
null_count = cursor.fetchone()[0]
print(f"\nNULL status count: {null_count}")

# Sample data
cursor.execute("SELECT log_no, type, description, status FROM alarm_history LIMIT 5")
print("\nSample data:")
for row in cursor.fetchall():
    print(f"  Log: {row[0]}, Type: {row[1]}, Desc: {row[2]}, Status: '{row[3]}'")

cursor.close()
db.close()
