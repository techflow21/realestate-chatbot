from flask import Flask, render_template, request, jsonify
import json
import numpy as np
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

# Load properties
with open('data/properties.json', 'r', encoding='utf-8') as f:
    all_properties = json.load(f)

# Remove duplicates based on title
seen_titles = set()
PROPERTIES = []
for p in all_properties:
    if p['title'] not in seen_titles:
        seen_titles.add(p['title'])
        PROPERTIES.append(p)

print(f"Loaded {len(PROPERTIES)} unique properties (removed {len(all_properties) - len(PROPERTIES)} duplicates)")

# Initialize lightweight semantic model (runs on CPU)
model = SentenceTransformer('all-MiniLM-L6-v2')  # ~80MB, fast, great for matching

# Precompute embeddings for *descriptions + titles + locations*
print("Precomputing property embeddings...")
property_texts = [
    f"{p['title']} in {p['location']}. {p['description']}. Has: {', '.join(p.get('features', []))}"
    for p in PROPERTIES
]
embeddings = model.encode(property_texts, convert_to_tensor=True, show_progress_bar=True)
print("✅ Embeddings ready.")


@app.route('/')
def index():
    # Show first 10 properties by default
    sample_props = PROPERTIES[:10]
    return render_template('index.html', properties=sample_props)


@app.route('/search')
def search():
    query = request.args.get('q', '').strip().lower()
    limit = int(request.args.get('limit', 10))

    if not query:
        results = PROPERTIES[:limit]
    else:
        # Hybrid: keyword fallback + semantic ranking
        keyword_matches = [
            p for p in PROPERTIES
            if query in p['title'].lower()
               or query in p['location'].lower()
               or query in p['description'].lower()
        ]
        if len(keyword_matches) >= 3:
            results = keyword_matches[:limit]
        else:
            # Semantic rerank full set
            query_emb = model.encode(query, convert_to_tensor=True)
            cos_scores = util.cos_sim(query_emb, embeddings)[0]
            top_k = min(limit, len(cos_scores))
            top_results = np.argpartition(-cos_scores, range(top_k))[:top_k]
            results = [PROPERTIES[i] for i in top_results]
    return render_template('index.html', properties=results, query=query)


@app.route('/api/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message', '').strip()
    if not user_msg:
        return jsonify({"error": "No message provided"}), 400

    # Semantic search for top 3 matches
    query_emb = model.encode(user_msg, convert_to_tensor=True)
    cos_scores = util.cos_sim(query_emb, embeddings)[0]
    top3 = np.argpartition(-cos_scores, range(3))[:3]
    matches = [PROPERTIES[i] for i in top3]

    # Format response
    response = {
        "reply": f"Here are 3 properties matching *'{user_msg}'*:",
        "properties": [
            {
                "id": p.get("title", "")[:30],
                "title": p["title"],
                "price": f"₦{p['price']:,}",
                "location": p["location"],
                "image_url": p["image_url"].strip(),
                "bedrooms": p.get("bedrooms", "N/A"),
                "bathrooms": p.get("bathrooms", "N/A"),
                "area_sqm": p.get("area_sqm", "N/A")
            }
            for p in matches
        ]
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)