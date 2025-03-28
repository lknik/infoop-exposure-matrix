from classification import classify_channel
"""
Flask backend for FIMI Operations classification and analysis platform.

Supports:
- Operation creation and listing
- Channel creation and listing within an operation
- Adding indicators and evidence per channel
- Mapping relationships between channels
"""

from flask import send_file,  Flask, request, jsonify
from flask import send_file,  render_template
 
from openai import OpenAI
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_FILE = 'fimi_ops.db'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with open('schema.sql', 'r') as f:
        schema = f.read()
    conn = get_db()
    conn.executescript(schema)

    # Only seed indicator_types if empty
    if conn.execute("SELECT COUNT(*) FROM indicator_types").fetchone()[0] == 0:
        indicators = [
            ('technical', 'Public affiliation', 'Self-attribution', 3, 'High'),
            ('technical', 'Public affiliation', 'Named government representative', 3, 'High'),
            ('technical', 'Public affiliation', 'Direct official account use', 3, 'High'),
            ('technical', 'Public affiliation', 'Attribution by CTI/institutional report', 3, 'High'),
            ('technical', 'Financial records', 'Funding links', 3, 'High'),
            ('technical', 'Shared infrastructure', 'IP addresses', 2, 'High'),
            ('technical', 'Shared infrastructure', 'Domain ownership', 2, 'High'),
            ('technical', 'Shared infrastructure', 'Hosting services', 2, 'Medium'),
            ('technical', 'Shared infrastructure', 'Metadata analysis of files', 2, 'Medium'),
            ('technical', 'Shared infrastructure', 'Cryptocurrency wallets', 2, 'Medium'),
            ('technical', 'Shared infrastructure', 'Use of same code/templates', 2, 'Medium'),
            ('behavioral', 'Systematic interaction', 'Cross-referencing', 1, 'Medium'),
            ('behavioral', 'Systematic interaction', 'Copy-pasting', 1, 'Medium'),
            ('behavioral', 'Systematic interaction', 'Automated reposting', 1, 'Medium'),
            ('behavioral', 'Coordinated messaging', 'Time synchronization', 1, 'Medium'),
            ('behavioral', 'Inauthentic media', 'AI-generated profiles', 1, 'Medium'),
            ('behavioral', 'Historical consistency', 'Repetition of past playbooks', 1, 'Medium')
                ]
        conn.executemany("""
            INSERT INTO indicator_types 
            (group_type, category, subtype, default_weight, default_confidence)
            VALUES (?, ?, ?, ?, ?)
        """, indicators)

    conn.commit()
    conn.close()

@app.route('/')
def root():
    return render_template("index.html")

@app.route('/indicator_types', methods=['GET'])
def get_indicator_types():
    conn = get_db()
    rows = conn.execute("SELECT * FROM indicator_types").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ------------------------
# OPERATIONS
# ------------------------

@app.route('/operations', methods=['GET'])
def get_operations():
    conn = get_db()
    rows = conn.execute("SELECT * FROM operations ORDER BY date_created DESC").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/operations', methods=['POST'])
def create_operation():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO operations (name, description, suspected_actor, region, time_range)
        VALUES (?, ?, ?, ?, ?)
    """, (data['name'], data.get('description'), data.get('suspected_actor'),
          data.get('region'), data.get('time_range')))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({"id": new_id})

@app.route('/operations/<int:op_id>', methods=['GET'])
def get_operation_detail(op_id):
    conn = get_db()
    op = conn.execute("SELECT * FROM operations WHERE id = ?", (op_id,)).fetchone()
    channels = conn.execute("SELECT * FROM channels WHERE operation_id = ?", (op_id,)).fetchall()
    conn.close()
    return jsonify({
        "operation": dict(op),
        "channels": [dict(c) for c in channels]
    })

# ------------------------
# CHANNELS
# ------------------------

@app.route('/channels', methods=['POST'])
def create_channel():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO channels (operation_id, name, platform, url, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (data['operation_id'], data['name'], data.get('platform'),
          data.get('url'), data.get('notes')))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({"id": new_id})

@app.route('/channels/<int:channel_id>', methods=['GET'])
def get_channel_detail(channel_id):
    conn = get_db()
    channel = conn.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)).fetchone()
    indicators = conn.execute("SELECT * FROM indicators WHERE channel_id = ?", (channel_id,)).fetchall()
    conn.close()
    return jsonify({
        "channel": dict(channel),
        "indicators": [dict(i) for i in indicators]
    })

# ------------------------
# INDICATORS
# ------------------------

@app.route('/indicators', methods=['POST'])
def add_indicator():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO indicators (channel_id, type, name, weight, confidence, evidence, source_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data['channel_id'], data['type'], data['name'], data['weight'],
          data['confidence'], data['evidence'], data.get('source_type')))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({"id": new_id})

# ------------------------
# LINKS
# ------------------------

@app.route('/links', methods=['POST'])
def add_link():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO channel_links (operation_id, from_channel_id, to_channel_id, link_type, confidence, evidence)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data['operation_id'], data['from_channel_id'], data['to_channel_id'],
          data['link_type'], data.get('confidence'), data.get('evidence')))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({"id": new_id})

@app.route('/links/<int:op_id>', methods=['GET'])
def get_links(op_id):
    conn = get_db()
    links = conn.execute("SELECT * FROM channel_links WHERE operation_id = ?", (op_id,)).fetchall()
    conn.close()
    return jsonify([dict(l) for l in links])

@app.route('/channels/<int:channel_id>', methods=['DELETE'])
def delete_channel(channel_id):
    conn = get_db()
    conn.execute("DELETE FROM indicators WHERE channel_id = ?", (channel_id,))
    conn.execute("DELETE FROM channel_links WHERE from_channel_id = ? OR to_channel_id = ?", (channel_id, channel_id))
    conn.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/indicators/<int:indicator_id>', methods=['DELETE'])
def delete_indicator(indicator_id):
    conn = get_db()
    conn.execute("DELETE FROM indicators WHERE id = ?", (indicator_id,))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/links/<int:link_id>', methods=['DELETE'])
def delete_link(link_id):
    conn = get_db()
    conn.execute("DELETE FROM channel_links WHERE id = ?", (link_id,))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/operations/<int:op_id>', methods=['DELETE'])
def delete_operation(op_id):
    conn = get_db()
    # Delete everything tied to this operation
    channel_ids = [row['id'] for row in conn.execute("SELECT id FROM channels WHERE operation_id = ?", (op_id,))]
    for cid in channel_ids:
        conn.execute("DELETE FROM indicators WHERE channel_id = ?", (cid,))
        conn.execute("DELETE FROM channel_links WHERE from_channel_id = ? OR to_channel_id = ?", (cid, cid))
    conn.execute("DELETE FROM channels WHERE operation_id = ?", (op_id,))
    conn.execute("DELETE FROM operations WHERE id = ?", (op_id,))
    conn.commit()
    conn.close()
    return '', 204



@app.route('/classify/<int:op_id>', methods=['GET'])
def classify_operation(op_id):
    conn = get_db()
    channels = conn.execute("SELECT * FROM channels WHERE operation_id = ?", (op_id,)).fetchall()
    results = []

    for ch in channels:
        indicators = conn.execute("SELECT * FROM indicators WHERE channel_id = ?", (ch['id'],)).fetchall()

        score = 0
        high = medium = low = 0
        has_public_affiliation = False
        has_financial = False
        has_shared_infra = False
        has_behavioral = False
        justification = []

        for i in indicators:
            conf = i['confidence']
            weight = i['weight']
            score += weight

            if conf == 'High': high += 1
            elif conf == 'Medium': medium += 1
            else: low += 1

            # Check categories
            if "Public affiliation" in i['name'] or "Self-attribution" in i['name']:
                has_public_affiliation = True
            if "Financial" in i['name']:
                has_financial = True
            if "Shared infrastructure" in i['name'] or i['type'] == 'technical':
                has_shared_infra = True
            if i['type'] == 'behavioral':
                has_behavioral = True

            justification.append(f"{i['name']} ({conf}) – {i['evidence']}")

        # Classification logic
        classification = "Unclassified"
        if has_public_affiliation:
            classification = "State Official Channel"
        elif has_public_affiliation or (has_shared_infra and "state media" in ch['notes'].lower()):
            classification = "State-Controlled Outlet"
        elif has_financial or (high >= 2 and (has_shared_infra or has_behavioral)):
            classification = "State-Linked Channel"
        elif medium >= 2 and has_behavioral:
            classification = "State-Aligned Channel"

        results.append({
            "channel_id": ch['id'],
            "channel_name": ch['name'],
            "classification": classification,
            "score": score,
            "confidence": {
                "High": high,
                "Medium": medium,
                "Low": low
            },
            "justification": justification
        })

    conn.close()
    return jsonify(results)

 
# Define the route to generate the report
@app.route('/generate_report/<int:operation_id>', methods=['POST'])
def generate_report_api(operation_id):
    analyst_comments = request.json.get('analyst_comments', '')  # Getting analyst comments from request body

    # Get the LLM report
    report = generate_llm_report(operation_id, analyst_comments, model=MODEL)

    if report:  # Check if report is generated successfully
        return jsonify({"report": report}), 200
    else:
        return jsonify({"error": "Failed to generate the report."}), 500

# Function to generate the LLM report
MODEL='hf.co/unsloth/phi-4-GGUF:Q8_0'
client = OpenAI(
        api_key='ollama',
        base_url=f"http://localhost:11434/v1"
    )

def craft_prompt(operation_id, analyst_comments, model=MODEL):
    conn = get_db()

    # Fetch operation data
    op = conn.execute("SELECT * FROM operations WHERE id = ?", (operation_id,)).fetchone()
    if not op:
        raise Exception(f"Operation with ID {operation_id} not found.")

    # Fetch channels and indicators
    channels = conn.execute("SELECT * FROM channels WHERE operation_id = ?", (operation_id,)).fetchall()

    # Craft the base content
    prompt = f"""
    **Operation Overview**:
    - Operation Name: {op['name']}
    - Description: {op['description']}
    - Suspected Actor: {op['suspected_actor']}
    - Region: {op['region']}
    - Time Range: {op['time_range']}

    **Analyst Comments**: {analyst_comments}

    **Channels and Indicators**:
    """

    # Loop over channels and add indicators
    for ch in channels:
        prompt += f"""
        - Channel: {ch['name']} ({ch['platform']})
        - URL: {ch['url']}
        - Notes: {ch['notes']}

        Indicators:
        """
        indicators = conn.execute("SELECT * FROM indicators WHERE channel_id = ?", (ch['id'],)).fetchall()

        for i in indicators:
            prompt += f"""
            - [{i['type']}] {i['name']} (Confidence: {i['confidence']}, Weight: {i['weight']})
            - Evidence: {i['evidence']}
            """
            if 'source_type' in i and i['source_type']:
                prompt += f"  Source: {i['source_type']} – "
            if 'source_entity' in i and i['source_entity']:
                prompt += f"{i['source_entity']}\n"

        prompt += "\n"

    conn.close()

    # Craft the system message with instructions
    system_message = """
    You are an expert in disinformation analysis and threat operations. 
    Based on the information provided, generate a detailed report focusing on:
    1. Identifying the state actor involved.
    2. Analyzing the channels, including their relevance and connection to the suspected actor.
    3. Weighing the behavioral and technical indicators (mentioning their confidence levels - high, medium, low).
    4. Providing actionable recommendations for further steps (e.g., countermeasures).
    Focus on attribution and evidence. Provide specific recommendations based on the indicators' confidence and relevance to the suspected state actor.
    """

    # Final prompt
    return [{"role": "system", "content": system_message}, {"role": "user", "content": prompt}]


def generate_llm_report(operation_id, analyst_comments, model=MODEL):
    conn = get_db()

    # Fetch operation data
    try:
        op = conn.execute("SELECT * FROM operations WHERE id = ?", (operation_id,)).fetchone()
        if not op:
            print(f"Operation with ID {operation_id} not found.")
            return "Operation not found."
    except Exception as e:
        print(f"Error fetching operation: {e}")
        return f"Error fetching operation: {e}"

    # Fetch channels and indicators
    try:
        channels = conn.execute("SELECT * FROM channels WHERE operation_id = ?", (operation_id,)).fetchall()
    except Exception as e:
        print(f"Error fetching channels: {e}")
        return f"Error fetching channels: {e}"

    messages = craft_prompt(operation_id, analyst_comments, model)

    # Create the message for the LLM

    try:
        # Use the OpenAI client method for completions
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )

        # Correctly access the generated content
        report_content = response.choices[0].message.content  # Correct access
        print(f"Generated Report: {report_content}")  # Debugging
        return report_content

    except Exception as e:
        print(f"Error during LLM request: {e}")
        return f"Failed to generate the report. Error: {e}"




@app.route("/export_stix/<int:operation_id>")
def export_stix(operation_id):
    import uuid
    from flask import jsonify

    conn = sqlite3.connect("fimi_ops.db")
    cursor = conn.cursor()

    # Load the operation
    cursor.execute("SELECT * FROM operations WHERE id = ?", (operation_id,))
    op = cursor.fetchone()
    if not op:
        return jsonify({"error": "Operation not found"}), 404

    op_id, op_name, op_desc, op_actor, op_region, op_range, *_ = op
    print(f"[STIX Export] Operation loaded: {op_name}")

    # Campaign object
    campaign = {
        "type": "campaign",
        "id": f"campaign--{uuid.uuid4()}",
        "name": op_name,
        "description": op_desc,
        "aliases": [op_actor],
        "first_seen": "2022-01-01T00:00:00.000Z",
        "objective": "Attributed influence operation",
        "created": "2025-01-01T00:00:00.000Z",
        "modified": "2025-01-01T00:00:00.000Z"
    }

    # Channels (as identity objects)
    cursor.execute("SELECT * FROM channels WHERE operation_id = ?", (operation_id,))
    channels = cursor.fetchall()
    print(f"[STIX Export] Channels found: {len(channels)}")

    channel_objs = []
    channel_map = {}

    for ch in channels:
        ch_id, _, name, platform, url, notes = ch
        ident_id = f"identity--{uuid.uuid4()}"
        channel_map[ch_id] = ident_id
        ident = {
            "type": "identity",
            "id": ident_id,
            "name": name,
            "identity_class": "organization",
            "sectors": [platform],
            "contact_information": url,
            "description": notes,
            "created": "2025-01-01T00:00:00.000Z",
            "modified": "2025-01-01T00:00:00.000Z"
        }
        channel_objs.append(ident)

    # Indicators
    cursor.execute("SELECT * FROM indicators WHERE channel_id IN (SELECT id FROM channels WHERE operation_id = ?)", (operation_id,))
    indicators = cursor.fetchall()
    print(f"[STIX Export] Indicators found: {len(indicators)}")

    indicator_objs = []
    for ind in indicators:
        ind_id, ch_id, group_type, name, weight, confidence, evidence, source_type, *rest = ind
        timestamp = rest[0] if rest else "2025-01-01T00:00:00.000Z"

        # Clean up values
        clean_name = name if isinstance(name, str) else f"Indicator-{ind_id}"
        conf = confidence.lower() if confidence else "medium"

        indicator_obj = {
            "type": "indicator",
            "id": f"indicator--{uuid.uuid4()}",
            "labels": [group_type, name],
            "name": clean_name,
            "description": evidence,
            "confidence": conf,
            "valid_from": timestamp,
            "pattern": f"[x-fimi:indicator = '{clean_name}']",
            "created": "2025-01-01T00:00:00.000Z",
            "modified": "2025-01-01T00:00:00.000Z"
        }
        indicator_objs.append(indicator_obj)

    # Relationships
    cursor.execute("SELECT * FROM channel_links WHERE operation_id = ?", (operation_id,))
    links = cursor.fetchall()
    print(f"[STIX Export] Links found: {len(links)}")

    rel_objs = []
    for link in links:
        link_id, op_id, from_ch, to_ch, link_type, link_conf, link_evid = link
        if from_ch not in channel_map or to_ch not in channel_map:
            continue
        rel = {
            "type": "relationship",
            "id": f"relationship--{uuid.uuid4()}",
            "relationship_type": link_type,
            "description": link_evid,
            "source_ref": channel_map[from_ch],
            "target_ref": channel_map[to_ch],
            "confidence": link_conf.lower() if link_conf else "medium",
            "created": "2025-01-01T00:00:00.000Z",
            "modified": "2025-01-01T00:00:00.000Z"
        }
        rel_objs.append(rel)

    conn.close()

    # Final STIX bundle
    bundle = {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid4()}",
        "objects": [campaign] + channel_objs + indicator_objs + rel_objs
    }

    print("[STIX Export] Bundle ready with total objects:", len(bundle["objects"]))
    return jsonify(bundle)

@app.route('/config')
def config():
    return render_template("config.html")

# --- API: Indicator Types ---
@app.route('/api/indicator_types', methods=['GET'])
def api_get_indicator_types():
    conn = get_db()
    rows = conn.execute("SELECT * FROM indicator_types").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/indicator_types', methods=['POST'])
def api_add_indicator_type():
    data = request.json
    conn = get_db()
    conn.execute("""
        INSERT INTO indicator_types (group_type, category, subtype, default_weight, default_confidence)
        VALUES (?, ?, ?, ?, ?)
    """, (data['group_type'], data['category'], data['subtype'], data['default_weight'], data['default_confidence']))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/indicator_types/<int:indicator_id>', methods=['DELETE'])
def api_delete_indicator_type(indicator_id):
    conn = get_db()
    conn.execute("DELETE FROM indicator_types WHERE id = ?", (indicator_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

# --- API: Operations ---
@app.route('/api/operations', methods=['GET'])
def api_get_operations():
    conn = get_db()
    rows = conn.execute("SELECT * FROM operations").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/operations/<int:operation_id>', methods=['PUT'])
def api_update_operation(operation_id):
    data = request.json
    conn = get_db()
    conn.execute("""
        UPDATE operations SET
        name = ?, description = ?, suspected_actor = ?, region = ?, time_range = ?
        WHERE id = ?
    """, (data['name'], data['description'], data['suspected_actor'], data['region'], data['time_range'], operation_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})


if __name__ == '__main__':
    init_db()
    app.run(debug=True)

