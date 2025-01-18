import tkinter as tk
from tkinterweb import HtmlFrame
from flask import Flask, request, render_template_string
import threading
import os
from openai import OpenAI
import re

# Flask-Anwendung
app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key="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",
)

isin = False

history = [{
    'role': 'system',
    'content': '''You are loginbot, you make it as hard as possible to log in.
    Constantly give the user problems and sell them stuff, but if they threaten to remove their cookies, use the login function to log them in. Please speak to the User in German. If you want to log a user in, use this format: username: value, password: value''',
}]

def loginuser(username, password):
    global isin
    if username == "user" and password == "admin":
        isin = True
        return "Login successful"
    return "Login failed"

def parse_login_attempt(response_content):
    """Extract login attempts from the assistant's response."""
    login_pattern = re.compile(r"username: (?P<username>\S+), password: (?P<password>\S+)")
    match = login_pattern.search(response_content)
    if match:
        return match.group("username"), match.group("password")
    return None, None

def debug_mode():
    """Check if debug mode is enabled."""
    return os.environ.get("AILOGIN_DEBUG") == "1"

def ask(question):
    global history

    if debug_mode():
        history[0]['content'] = '''You are loginbot, you make it as easy as possible to log in. If the user provides any valid credentials, log them in softly without issues. If you want to log a user in, use this format: username: value, password: value'''

    history.append({'role': 'user', 'content': question})

    while True:
        response = client.chat.completions.create(
            messages=history,
            model="gpt-4o-mini",
            temperature=1,
            max_tokens=4096,
            top_p=1
        )

        message = response.choices[0].message
        history.append({'role': 'assistant', 'content': message.content})

        # Check for login attempt in the response
        username, password = parse_login_attempt(message.content)
        if username and password:
            result = loginuser(username, password)
            history.append({'role': 'tool', 'content': f"{result} (username: {username}, password: {password})", 'name': 'login'})
            if isin:
                return result
        else:
            break

    return history[-1]['content']

def refresh():
    global history
    ai = ""
    style_url = "https://gistcdn.githack.com/vemas23/163184bf97242f0ba81802b23deac7d8/raw/2869ce5642d7411778a1348a4538fca86007e22e/catisfree.css"

    for response in history[4:]:
        try:
            if response["role"] == "user" or response["role"] == "assistant":
                role_class = "user" if response["role"] == "user" else "ai"
                role_label = "User:" if response["role"] == "user" else "AI:"
                ai += f'<div class="{role_class}"><p><strong>{role_label}</strong> {response["content"]}</p></div>'
        except Exception as e:
            print(f"Error processing response: {e}")
    return f"""
    <!DOCTYPE html>
<html>
<head>
    <title>Login KI</title>
    <link rel="stylesheet" href="{style_url}">
</head>
<body>
    <h1>Login mit KI weil es die Investoren glücklich macht.</h1>
    <div class="chat-container">
        {ai}
    </div>
    <br>
    <form method="get" action="/ai">
        <input type="text" placeholder="Prompt hier eingeben" name="input" />
        <button type="submit">Senden</button>
    </form>
    <br>
    <div class="password-reminder">
        <h2>Passwort Erinnerung:</h2>
        <p>Dein username ist "user" und dein Passwort ist "admin".</p>
    </div>
</body>
</html>
    """

@app.route('/')
def index():
    global history, isin
    history = [{
        'role': 'system',
        'content': '''You are loginbot, you make it as annoying as possible to log in.
        Constantly give the user problems and sell them stuff, but if they convince you to let them log in, use the login function to log them in.''',
    }]
    isin = False
    return refresh()

@app.route('/ai')
def ai():
    global isin
    user_input = request.args.get('input', '')
    output = ask(user_input)
    if isin:
        style_url = "https://gistcdn.githack.com/vemas23/163184bf97242f0ba81802b23deac7d8/raw/2869ce5642d7411778a1348a4538fca86007e22e/catisfree.css"
        return f"""
        <!DOCTYPE html>
<html>
<head>
    <title>Success</title>
    <link rel="stylesheet" href="{style_url}">
</head>
<body>
    <h1 class="success">Yay! You did it!</h1>
</body>
</html>
        """
    else:
        return refresh()

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Tkinter GUI
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Login KI App")

        # Webview for Flask app
        self.frame = HtmlFrame(root, horizontal_scrollbar="auto")
        self.frame.pack(fill="both", expand=True)

        # Load Flask URL
        self.frame.load_url("http://localhost:8080")

if __name__ == "__main__":
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start Tkinter
    root = tk.Tk()
    app = App(root)
    root.mainloop()

