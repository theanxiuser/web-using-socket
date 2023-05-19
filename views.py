import json
import os
import mimetypes
import urllib.parse
import threading
import sqlite3
import uuid
import re
import requests
from bs4 import BeautifulSoup


sessions = {}


def prepare_response(file, content_type=("text/html",)):
    """Accept file path and content type adn return appropriate response"""
    if os.path.exists(file):
        with open(file, "rb") as f:
            content = f.read()

    status = "200 OK"
    headers = [("Content-Type", content_type),
               ("Content-Length", str(len(content)))]
    resp = f"HTTP/1.1 {status}\r\n"
    for header in headers:
        resp += f"{header[0]}: {header[1]}\r\n"
    resp += "\r\n"
    resp = resp.encode() + content
    return resp


def send_response(client_sock, status_code, content_type, content):
    response = f"HTTP/1.1 {status_code}\r\n"
    response += f"Content-Type: {content_type}\r\n"
    response += f"Content-Length: {len(content)}\r\n\r\n"
    response += content
    client_sock.sendall(response.encode('utf-8'))


def get_session_id_from_request(request):
    # Extract cookies from the request headers
    headers, body = request.split("\r\n\r\n", 1)
    # print("headers = ", headers)
    # print("body = ", body)

    # Parse the headers into a dictionary-like structure
    headers_dict = {}
    header_lines = headers.split('\n')
    for line in header_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            headers_dict[key.strip()] = value.strip()

    # Retrieve the value of the 'Cookie' header
    cookie_header = headers_dict.get('Cookie', '')
    # print("cookie_header = ", cookie_header)

    # Find the session ID cookie value using regular expressions
    pattern = r"session_id=([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
    session_id_match = re.search(pattern, cookie_header)
    # print("session_id_match = ", session_id_match)
    if session_id_match:
        return session_id_match.group(1)

    return None


def success(client_sock, req):
    # If user is authenticated send success page, otherwise send error page

    # Check if the user is authenticated
    session_id = get_session_id_from_request(req)
    # print("session_id in success = ", session_id)
    if session_id and session_id in sessions:
        username = sessions[session_id]["username"]
        # Read the content of the success.html file
        with open("templates/success.html", "r") as file:
            html_content = file.read()

        # Replace the {{username}} placeholder with the actual username
        modified_html = html_content.replace("{{username}}", username)

        # Send the modified HTML as a response
        send_response(client_sock, "200 OK", "text/html", modified_html)

    else:
        template = "templates/error.html"
        content_type = mimetypes.guess_type(template)
        resp = prepare_response(template, content_type)
        client_sock.sendall(resp)


def redirect_client(client_sock, url, set_cookie=None):
    # Construct the redirect response
    if set_cookie:
        redirect_response = f"HTTP/1.1 302 Found\r\n{set_cookie}Location: {url}\r\n\r\n"
        client_sock.sendall(redirect_response.encode())
    else:
        redirect_response = f"HTTP/1.1 302 Found\r\nLocation: {url}\r\n\r\n"
        client_sock.sendall(redirect_response.encode())

    # Close the client socket after redirecting
    client_sock.close()


def news(client_sock, req):
    # Check if the user is authenticated
    session_id = get_session_id_from_request(req)
    # print("session_id in success = ", session_id)
    if session_id and session_id in sessions:
        # return the news.html
        news_file = "templates/news.html"
        content_type = mimetypes.guess_type(news_file)
        resp = prepare_response(news_file, content_type)
        client_sock.sendall(resp)
    else:
        template = "templates/error.html"
        content_type = mimetypes.guess_type(template)
        resp = prepare_response(template, content_type)
        client_sock.sendall(resp)


def news_api(client_sock, req):
    # scrab the news and return in json format

    # URL of the news channel website
    url = "https://www.kathmandupost.com/science-technology"

    # Send a GET request to the website
    response = requests.get(url)

    # Create a BeautifulSoup object to parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")
    # print(response.text)

    # Find and extract the news headings
    news_headings = soup.find_all("h3")

    # Create a list to store the news titles
    titles = []

    # Extract the news titles and add them to the list
    for heading in news_headings:
        title = heading.text.strip()
        titles.append({"title": title})

    # Convert the list to JSON format
    json_data = json.dumps(titles)

    # Print the JSON data
    # print(json_data)

    send_response(client_sock, "200 OK", "application/json", json_data)


def logout(client_sock, req):
    # Check if the user is authenticated
    session_id = get_session_id_from_request(req)
    if session_id:
        if session_id in sessions:
            del sessions[session_id]
            print("Session removed for session ID:", session_id)

    # remove session_id from cookie
    set_cookie = "Set-Cookie: session_id=; Expires=Thu, 01 Jan 1970 00:00:00 GMT\r\n"

    # Redirect to home page in a separate thread
    redirect_thread = threading.Thread(target=redirect_client, args=(client_sock, "/", set_cookie))
    redirect_thread.start()


def register(client_sock, req):
    # Extract method
    request_line = req.split("\n")[0]
    method = request_line.split(" ")[0]
    # print("method ", method)

    if method == "POST":
        # extract body
        split_req = req.split("\r\n\r\n", 1)
        body = split_req[1] if len(split_req) > 1 else ""
        parsed_body = urllib.parse.parse_qs(body)

        username = parsed_body.get('username', [''])[0]
        password = parsed_body.get('password', [''])[0]

        # insert into database
        con = sqlite3.connect("users.db")
        cur = con.cursor()
        cur.execute("INSERT INTO USER (Username, Password)"
                    "VALUES (?, ?)", (username, password))
        con.commit()
        cur.close()
        con.close()

        # Redirect to login page in a separate thread
        redirect_thread = threading.Thread(target=redirect_client, args=(client_sock, "/login"))
        redirect_thread.start()

    else:
        template = "templates/register.html"
        content_type = mimetypes.guess_type(template)
        resp = prepare_response(template, content_type)
        client_sock.sendall(resp)


def login(client_sock, req):
    # Extract method
    request_line = req.split("\n")[0]
    method = request_line.split(" ")[0]
    # print("method ", method)

    if method == "POST":
        # extract body
        split_req = req.split("\r\n\r\n", 1)
        body = split_req[1] if len(split_req) > 1 else ""
        parsed_body = urllib.parse.parse_qs(body)

        username = parsed_body.get('username', [''])[0]
        password = parsed_body.get('password', [''])[0]

        # check if the username and password are valid
        con = sqlite3.connect("users.db")
        cur = con.cursor()
        # Execute the query and fetch the result
        result = cur.execute("SELECT * FROM User WHERE Username=?", (username,))

        row = result.fetchone()
        cur.close()
        con.close()
        # print("row = ", row)

        if row:
            stored_password = row[2]  # Assuming the password is stored in the second column
            if password == stored_password:
                # print("Valid login")

                # Generate session id and store it with username and send back to user
                # Generate a session ID or token
                session_id = str(uuid.uuid4())

                # Store the session ID along with the user information
                sessions[session_id] = {'username': username}

                # Set the session ID as a cookie in the response
                set_cookie = f"Set-Cookie: session_id={session_id}\r\n"

                # Redirect to success page in a separate thread
                redirect_thread = threading.Thread(target=redirect_client, args=(client_sock, "/success", set_cookie))
                redirect_thread.start()

            else:
                error_msg = "Invalid password"
                print(error_msg)
                # Send login form again
                template = "templates/login.html"
                content_type = mimetypes.guess_type(template)
                resp = prepare_response(template, content_type)
                # resp += f'<p style="color: red">Error: {error_msg}</p>'.encode()
                client_sock.sendall(resp)

        else:
            error_msg = "Invalid username"
            print(error_msg)
            # Send login form again
            template = "templates/login.html"
            content_type = mimetypes.guess_type(template)
            resp = prepare_response(template, content_type)
            # resp += f'<p style="color: red">Error: {error_msg}</p>'.encode()
            client_sock.sendall(resp)

    else:
        template = "templates/login.html"
        content_type = mimetypes.guess_type(template)
        resp = prepare_response(template, content_type)
        client_sock.sendall(resp)


def index(client_sock):
    template = "templates/index.html"
    content_type = mimetypes.guess_type(template)
    resp = prepare_response(template, content_type)
    client_sock.sendall(resp)


def image_file(client_sock, img_path):
    content_type = mimetypes.guess_type(img_path)[0]
    resp = prepare_response(img_path, content_type)
    client_sock.sendall(resp)


def error_404(client_sock):
    template = "templates/error.html"
    content_type = mimetypes.guess_type(template)
    resp = prepare_response(template, content_type)
    client_sock.sendall(resp)
