import sys

def update():
    with open("app.py", "r") as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if '"Method": tx.classification_method' in line:
            lines[i] = line.replace(
                '"Method": tx.classification_method', 
                '"Method": "🤖 AI Suggested" if tx.classification_method == "ai_fallback" else tx.classification_method'
            )
            break
            
    with open("app.py", "w") as f:
        f.writelines(lines)

update()
print("Updated AI tagging.")
