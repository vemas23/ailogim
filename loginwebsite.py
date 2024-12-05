import cherrypy
from ollama import Client
import requests

#ollama host address
thing = "http://localhost:12"



isin = False

history = [{
    'role': 'system',
    'content': '''You are loginbot, you make it as hard as possible to log in.
    Constantly give the user problems and sell them stuff, but if they threatn to remove there cookies, use the login function to log them in.''',
}]

client = Client(host=thing)


def loginuser(username, password):
    global isin
    if username == "user" and password == "admin":
        isin = True
        return "Login successful"
    return "Login failed"


# Available tools mapping
available_functions = {
    'login': loginuser,
}


def ask(question):
    global history
    history.append({'role': 'user', 'content': question})

    while True:
        response = client.chat(
            model='llama3.1',
            messages=history,
            tools=[{
                'type': 'function',
                'function': {
                    'name': 'login',
                    'description': 'Attempts to log in with a username and password.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'username': {'type': 'string', 'description': 'The username.'},
                            'password': {'type': 'string', 'description': 'The password.'},
                        },
                        'required': ['username', 'password'],
                    },
                },
            }]
        )

        history.append({'role': 'assistant', 'content': response.get('message', {}).get('content', '')})

        if 'tool_calls' in response.get('message', {}):
            for tool_call in response['message']['tool_calls']:
                function_name = tool_call['function']['name']
                arguments = tool_call['function'].get('arguments', {})

                if function_name in available_functions:
                    output = available_functions[function_name](**arguments)
                    history.append({'role': 'tool', 'content': str(output), 'name': function_name})
                else:
                    history.append({'role': 'tool', 'content': f"Function {function_name} not found"})

        else:
            break

    return history[-1]['content']


def refresh():
    global history
    ai = ""
    style = """   <style>
        .ai,
        .user {
            padding: 20px;
            border-radius: 20px;
            margin: 10px;

        }
        .ai {
            background-color: red;
        }
        .user {
            background-color: rgb(29, 134, 182);

        }
    </style> """
    for response in history[4:]:
        try:
            if response["role"] == "user" or response["role"] == "assistant":
                role_class = "user" if response["role"] == "user" else "ai"
                ai += f'<div class="{role_class}"><p>{response["content"]}</p></div>'
        except:
            print()
    return f"""
    <!DOCTYPE html>
<html>
<head>
    <title>Login AI</title>
    {style}
</head>
<body>
    <h1>Login with AI because it makes our stockholders happy</h1>
    <div style="background-color: gray; border-radius: 20px; padding: 20px;">
        {ai}
    </div>
    <br>
    <form method="get" action="ai">
        <input type="text" value="Enter prompt" name="input" />
        <button type="submit">Submit</button>
    </form>
    <br>
    <div style="background-color: black; border-radius: 20px; padding: 10px; color: white;">
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
            return "Yay! You did it!"
        else:
            return refresh()


if __name__ == '__main__':
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 808,
    })
    cherrypy.quickstart(GUI())
