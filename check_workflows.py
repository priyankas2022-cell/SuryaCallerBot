from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv

load_dotenv('api/.env')

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"Connecting to database...")

engine = create_engine(DATABASE_URL.replace('+asyncpg', '+psycopg2'))

with engine.connect() as conn:
    # Check workflows
    result = conn.execute(text("""
        SELECT id, name, status, workflow_definition, created_at 
        FROM workflows 
        WHERE id IN (6, 7, 8, 9)
        ORDER BY created_at DESC
    """))
    workflows = result.fetchall()
    
    print("\n📋 WORKFLOWS TABLE:")
    print("=" * 80)
    for wf in workflows:
        print(f"\nWorkflow ID: {wf.id}")
        print(f"  Name: {wf.name}")
        print(f"  Status: {wf.status}")
        print(f"  Has Definition JSON: {'✓' if wf.workflow_definition else '✗ EMPTY'}")
        if wf.workflow_definition:
            nodes = wf.workflow_definition.get('nodes', [])
            edges = wf.workflow_definition.get('edges', [])
            print(f"  Nodes: {len(nodes)}")
            print(f"  Edges: {len(edges)}")
        print(f"  Created: {wf.created_at}")
    
    # Check workflow_definitions table
    result = conn.execute(text("""
        SELECT wd.id, wd.workflow_id, w.name, wd.is_current, wd.workflow_json
        FROM workflow_definitions wd
        JOIN workflows w ON wd.workflow_id = w.id
        WHERE wd.workflow_id IN (6, 7, 8, 9)
        ORDER BY wd.workflow_id, wd.created_at DESC
    """))
    definitions = result.fetchall()
    
    print("\n\n📚 WORKFLOW_DEFINITIONS TABLE:")
    print("=" * 80)
    for df in definitions:
        print(f"\nDefinition ID: {df.id}")
        print(f"  Workflow ID: {df.workflow_id} ({df.name})")
        print(f"  Is Current: {'✓' if df.is_current else '✗'}")
        print(f"  Has JSON: {'✓' if df.workflow_json else '✗ EMPTY'}")
        if df.workflow_json:
            nodes = df.workflow_json.get('nodes', [])
            edges = df.workflow_json.get('edges', [])
            print(f"  Nodes: {len(nodes)}")
            print(f"  Edges: {len(edges)}")
