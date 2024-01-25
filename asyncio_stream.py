from odin_zmq import OdinZMQ
import zmq
import asyncio
import time


async def send_zmq_request(interval, odin):
    global start
    while True:
        start_time = time.time()
        # Replace 'your_request_data' with the actual data you want to send
        response = odin.stream_get(mode=None)

        # Wait for the response
        #print(f"Received response: {response}", len(response))
        #new_time = time.time()
        #print(new_time - start)
        #start = new_time

        end_time = time.time()
        execution_time = end_time - start_time
        print(execution_time)

        # Sleep for the specified interval
        #await asyncio.sleep(max(0, interval - execution_time))


if __name__ == "__main__":
    odin = OdinZMQ("172.16.19.108")
    odin.stream_configure('all')
    time.sleep(5)

    # Set the interval in seconds (5 ms = 0.005 seconds)
    interval_seconds = 0.0
    start = time.time()

    # Create an event loop
    loop = asyncio.get_event_loop()

    # Run the coroutine indefinitely
    try:
        loop.run_until_complete(send_zmq_request(interval_seconds, odin))
    except KeyboardInterrupt:
        pass
    finally:
        # Close the socket and context upon exiting
        odin.close_socket()