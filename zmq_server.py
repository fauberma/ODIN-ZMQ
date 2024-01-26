import zmq


def start_zmq_server():
    context = zmq.Context()
    socket = context.socket(zmq.REP)

    # Replace 'tcp://*:5555' with the desired server address
    socket.bind('tcp://*:5555')

    try:
        while True:
            # Wait for a request
            request = socket.recv_string()
            print(f"Received request: {request}")

            # Process the request (you can replace this with your own logic)
            response = f"Processed: {request}"

            # Send the response back to the client
            socket.send_string(response)
            print(f"Sent response: {response}")

    except KeyboardInterrupt:
        pass
    finally:
        # Close the socket and context upon exiting
        socket.close()
        context.term()


if __name__ == "__main__":
    start_zmq_server()