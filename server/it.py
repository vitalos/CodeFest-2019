#!/usr/bin/env python3
import json

from flask import Flask, render_template
from search_engine import SearchEngine

app = Flask(__name__)
search_engine = SearchEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tutorials')
def tutorials():
    return render_template('tutorials.html')

@app.route('/demo-search')
def demo_search():
    return render_template('search.html')

@app.route('/search')
def search():
    return json.dumps(search_engine.search(request.args.get('query', '')))    
