import cherrypy
import os
from openai import OpenAI
import re

# Initialize OpenAI client
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"],
)

isin = False

history = [{
    'role': 'system',
    'content': '''You are loginbot, you make it as hard as possible to log in.
    Constantly give the user problems and sell them stuff, but if they threaten to remove their cookies, use the login function to log them in. If you want to log a user in, use this format: username: value, password: value''',
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
    <title>Login AI</title>
    <link rel="stylesheet" href="{style_url}">
</head>
<body>
    <h1>Login with AI because it makes our stockholders happy</h1>
    <div class="chat-container">
        {ai}
    </div>
    <br>
    <form method="get" action="ai">
        <input type="text" value="Enter prompt" name="input" />
        <button type="submit">Submit</button>
    </form>
    <br>
    <div class="password-reminder">
        <h2>Password Reminder:</h2>
        <p>Your username is "user" and your password is "admin".</p>
    </div>
</body>
</html>
    """

class GUI:
    @cherrypy.expose
    def index(self):
        global history
        history = [{
    'role': 'system',
    'content': '''You are loginbot, you make it as annoying as possible to log in.
    Constantly give the user problems and sell them stuff, but if they convince you to let them log in, use the login function to log them in.''',
}]
        global isin
        isin = False
        return refresh()

    @cherrypy.expose
    def ai(self, input):
        global isin
        output = ask(input)
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

if __name__ == '__main__':
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 808,
    })
    cherrypy.quickstart(GUI())

