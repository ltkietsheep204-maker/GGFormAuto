#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/2apple_mgn_63_ram16/Desktop/GGform')

from gui_app_v3 import GoogleFormWorker

worker = GoogleFormWorker("https://docs.google.com/forms/d/1Py98mcOo55G_gqUqALn-2YwEdr2vNXaL_7t74uPYRzA/edit?hl=vi")

# Capture signals
worker.progress.connect(lambda msg: print(f"[PROGRESS] {msg}"))
worker.error.connect(lambda msg: print(f"[ERROR] {msg}"))

def on_finished(questions):
    print(f"\n[FINISHED] Total questions: {len(questions)}")
    for q in questions:
        print(f"  - {q['title']} ({q['type']}) - {len(q['options'])} options")
        for opt in q['options']:
            print(f"      * {opt['text']}")

worker.finished.connect(on_finished)
worker.run()
