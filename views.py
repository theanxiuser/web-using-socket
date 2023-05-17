import os
import mimetypes
import urllib.parse
import threading


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


def success(client_sock):
    template = "templates/success.html"
    content_type = mimetypes.guess_type(template)
    resp = prepare_response(template, content_type)
    client_sock.sendall(resp)


def redirect_client(client_sock, url):
    # Construct the redirect response
    redirect_response = f"HTTP/1.1 302 Found\r\nLocation: {url}\r\n\r\n"
    client_sock.sendall(redirect_response.encode())
    # Close the client socket after redirecting
    client_sock.close()


def login(client_sock, req):
    # Extract method
    request_line = req.split("\n")[0]
    method = request_line.split(" ")[0]
    print("method ", method)

    if method == "POST":
        # extract body
        split_req = req.split("\r\n\r\n", 1)
        body = split_req[1] if len(split_req) > 1 else ""
        parsed_body = urllib.parse.parse_qs(body)

        username = parsed_body.get('username', [''])[0]
        password = parsed_body.get('password', [''])[0]

        if username == "bishal" and password == "bishal":
            # Redirect to home page in a separate thread
            redirect_thread = threading.Thread(target=redirect_client, args=(client_sock, "/success"))
            redirect_thread.start()

        else:
            # Send login form again
            template = "templates/login.html"
            content_type = mimetypes.guess_type(template)
            resp = prepare_response(template, content_type)
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
