import os
import socket
import mimetypes
import threading
import views

HOST = "localhost"
PORT = 8000


def handle_request(client_sock):
    req = client_sock.recv(5000).decode()
    print(req)

    # Extract request method and path
    request_line = req.split("\n")[0]
    method, path, _ = request_line.split(" ")

    if method == "GET" and path == "/":
        views.index(client_sock)

    else:
        # Check if the requested path is an image file
        img_path = os.path.join(os.path.dirname(__file__), path[1:])
        if os.path.isfile(img_path) and mimetypes.guess_type(img_path)[0].startswith("image/"):
            views.image_file(client_sock, img_path)

        else:
            views.error_404(client_sock)


def handle_client(client_sock):
    with client_sock:
        handle_request(client_sock)


def run_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_sock.bind((HOST, PORT))
        server_sock.listen(5)

        while True:
            client_sock, client_addr = server_sock.accept()
            print(f"Connected to client: {client_addr}")

            # Create a new thread for each client
            thread = threading.Thread(target=handle_client, args=(client_sock,))
            thread.start()

    except KeyboardInterrupt:
        print("\nclosing the server...")
        print("done!")

    except Exception as e:
        print("Exception:")
        print(e)

    finally:
        server_sock.close()


if __name__ == "__main__":
    print("A simple web server using socket")
    print(f"Visit http://{HOST}:{PORT}")
    run_server()
