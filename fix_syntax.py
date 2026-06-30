import sys

def fix():
    with open("app.py", "r") as f:
        content = f.read()
        
    broken = '''report_md = f"### ⚠️ Report Generation Failed

**Error:** `{e}`

```python
{traceback.format_exc()}
```"'''
    fixed = 'report_md = f"### ⚠️ Report Generation Failed\\n\\n**Error:** `{e}`\\n\\n```python\\n{traceback.format_exc()}\\n```"'
    
    if broken in content:
        content = content.replace(broken, fixed)
        with open("app.py", "w") as f:
            f.write(content)
        print("Fixed syntax error!")
    else:
        print("Could not find the broken string block.")
        
fix()
