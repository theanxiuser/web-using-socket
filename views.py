import os
import mimetypes


def index(request):
    # resp = prepare_page("templates/index.html")
    index_file = "templates/index.html"
    content = ""
    if os.path.exists(index_file):
        with open(index_file, "r") as file:
            content = file.read()

    status = "200 OK"
    content_type = mimetypes.guess_type(index_file)
    print("This is content type of index.html -------", content_type)
    headers = [("Content-Type", "text/html; charset=utf-8"),
               ("Content-Length", str(len(content)))]
    resp = f"HTTP/1.1 {status}\r\n"
    for header in headers:
        resp += f"{header[0]}: {header[1]}\r\n"
    resp += "\r\n"
    resp += content
    resp = resp.encode()
    request.sendall(resp)


def image_file(request, img_path):
    content = ""
    with open(img_path, "rb") as file:
        content = file.read()

    status = "200 OK"
    content_type = mimetypes.guess_type(img_path)[0]
    headers = [("Content-Type", content_type),
               ("Content-Length", str(len(content)))]
    resp = f"HTTP/1.1 {status}\r\n"
    for header in headers:
        resp += f"{header[0]}: {header[1]}\r\n"
    resp += "\r\n"
    resp = resp.encode() + content
    request.sendall(resp)


def error_404(request):
    error_file = "templates/error.html"
    content = ""
    if os.path.exists(error_file):
        with open(error_file, "r") as file:
            content = file.read()

    status = "404 Not Found"
    headers = [("Content-Type", "text/html; charset=utf-8"),
               ("Content-Length", str(len(content)))]
    resp = f"HTTP/1.1 {status}\r\n"
    for header in headers:
        resp += f"{header[0]}: {header[1]}\r\n"
    resp += "\r\n"
    resp += content
    resp = resp.encode()
    request.sendall(resp)
