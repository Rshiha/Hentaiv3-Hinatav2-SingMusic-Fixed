def say(a,c): return " ".join(a) if a else "Usage: .say hello"
def reverse(a,c): return " ".join(a)[::-1] if a else "Usage: .reverse hello"
def upper(a,c): return " ".join(a).upper() if a else "Usage: .upper hello"
def lower(a,c): return " ".join(a).lower() if a else "Usage: .lower HELLO"
def count(a,c):
 t=" ".join(a); return f"🔢 Characters: {len(t)} | Words: {len(t.split())}" if t else "Usage: .count text"
def math_cmd(a,c):
 try:
  e=" ".join(a)
  if not e or any(x not in "0123456789+-*/(). % " for x in e): return "❌ Basic math only."
  return f"🧮 {e} = {eval(e,{'__builtins__':{}},{})}"
 except:return "❌ Invalid calculation."
TEXT_COMMANDS={"say":say,"reverse":reverse,"upper":upper,"lower":lower,"count":count,"math":math_cmd}
