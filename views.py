import os
import mimetypes


def prepare_response(file, content_type):
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


def index(request):
    template = "templates/index.html"
    content_type = mimetypes.guess_type(template)
    resp = prepare_response(template, content_type)
    request.sendall(resp)


def image_file(request, img_path):
    content_type = mimetypes.guess_type(img_path)[0]
    resp = prepare_response(img_path, content_type)
    request.sendall(resp)


def error_404(request):
    template = "templates/error.html"
    content_type = mimetypes.guess_type(template)
    resp = prepare_response(template, content_type)
    request.sendall(resp)
