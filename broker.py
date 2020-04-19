import sys
import socket
import time
import threading
import select

sock_out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_out.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock_out.bind(('0.0.0.0', 22244))
sock_out.listen(5)

sock_in  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_in.bind(('0.0.0.0', 22233))
sock_in.setblocking(0)

consumers = []

def accepting_function(name,run_event):
    try:
        while run_event.is_set():
            readable, writable, errored = select.select([sock_out], [], [], 1)
            for s in readable:
                (clientsocket, address) = sock_out.accept()
                consumers.append((clientsocket, address))
                sys.stderr.write("Client connected:\t%s\n" % str(address))
    except KeyboardInterrupt:
        pass

def receiving_function(name,run_event):
    try:
        while run_event.is_set():
            ready = select.select([sock_in], [], [], 1)
            if ready[0]:
                data, address = sock_in.recvfrom(4096)
                print ('received %s bytes from %s' % (len(data), address))
                for consumer in consumers:
                    try:
                        consumer[0].send(data)
                    except:
                        sys.stderr.write("Client disconnected:\t%s\n" % str(consumer[1]))
                        consumers.remove(consumer)
    except KeyboardInterrupt:
        pass

run_event = threading.Event()
run_event.set()

accepting = threading.Thread(target=accepting_function, args=(1,run_event))
receiving = threading.Thread(target=receiving_function, args=(2,run_event))

accepting.start()
receiving.start()

try:
    while True:
        time.sleep(.1)
except KeyboardInterrupt:
    sys.stderr.write("Terminating threads\n")
    run_event.clear()
    accepting.join()
    receiving.join()
    sys.stderr.write("Threads successfully stopped\n")

sock_out.close()
sock_in.close()
