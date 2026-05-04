import json
import psycopg2

def update_workflow():
    conn = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    cur = conn.cursor()
    
    # Get current definition
    cur.execute("SELECT workflow_definition FROM workflows WHERE id = 62;")
    row = cur.fetchone()
    if not row:
        print("Workflow 62 not found")
        return
    
    definition = row[0]
    # In some psql versions it might be a dict already if using JSONB, otherwise string
    if isinstance(definition, str):
        definition = json.loads(definition)
    
    nodes = definition.get('nodes', [])
    for node in nodes:
        if node.get('id') == '1':
            data = node.get('data', {})
            prompt = data.get('prompt', '')
            # Remove the specific line
            new_prompt = prompt.replace("Tell them that we are connecting you to the suryacaller.", "")
            new_prompt = new_prompt.replace("Start your conversation by greeting them politely .", "Start your conversation by greeting them politely and introducing yourself as Sam from Surya International.")
            data['prompt'] = new_prompt
            # Disable delayed start
            data['delayed_start'] = False
            node['data'] = data
            print(f"Updated node 1 prompt: {new_prompt}")
            break
            
    # Update back to DB
    cur.execute("UPDATE workflows SET workflow_definition = %s WHERE id = 62;", (json.dumps(definition),))
    conn.commit()
    cur.close()
    conn.close()
    print("Workflow updated successfully")

if __name__ == "__main__":
    update_workflow()
