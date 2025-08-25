#!/usr/bin/env python3
"""
Fix database schema by dropping and recreating tables with proper pgvector types.
"""

import sys
import os

# Add the api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from api.models.db import engine, drop_tables, create_tables
from api.models.entities import SQLModel

def fix_database():
    """Drop and recreate all tables with proper schema."""
    print("🗑️  Dropping existing tables...")
    drop_tables()
    
    print("🔧 Recreating tables with proper pgvector schema...")
    create_tables()
    
    print("✅ Database schema fixed!")
    print("📝 Tables recreated with proper pgvector types")

if __name__ == "__main__":
    fix_database()
