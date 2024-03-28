import socket
import pickle
import time
import threading
import ssl

s = socket.socket()
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="tic_final\server.crt", keyfile="tic_final\server.key")
host = ""
port = 9999
zero_matrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
matrix = {}
playerIndex = 1
roomIndex = 0
playroom = {}
playerConn = {}
rooms = {}
available = {}
lock = threading.Lock()

def get_input(currentPlayer, curr, playerIndex):
    conn = playerConn[curr]
    player = f"Player {curr}'s Turn"
    print(player)
    send_common_msg(player, playerIndex)
    try:
        conn.send("Input".encode())
        data = conn.recv(2048 * 10)
        conn.settimeout(20)
        dataDecoded = data.decode().split(",")
        x = int(dataDecoded[0])
        y = int(dataDecoded[1])
        matrix[playroom[playerIndex]][x][y] = currentPlayer
        send_common_msg("Matrix", playerIndex)
        send_common_msg(str(matrix[playroom[playerIndex]]), playerIndex)
    except:
        conn.send("Error".encode())
        print("Error occured! Try again..")

def check_rows(playerIndex):
    result = 0
    lmatrix = matrix[playroom[playerIndex]]
    for i in range(3):
        if lmatrix[i][0] == lmatrix[i][1] and lmatrix[i][1] == lmatrix[i][2]:
            result = lmatrix[i][0]
            if result != 0:
                break
    return result

def check_columns(playerIndex):
    result = 0
    lmatrix = matrix[playroom[playerIndex]]
    for i in range(3):
        if lmatrix[0][i] == lmatrix[1][i] and lmatrix[1][i] == lmatrix[2][i]:
            result = lmatrix[0][i]
            if result != 0:
                break
    return result

def check_diagonals(playerIndex):
    result = 0
    lmatrix = matrix[playroom[playerIndex]]
    if lmatrix[0][0] == lmatrix[1][1] and lmatrix[1][1] == lmatrix[2][2]:
        result = lmatrix[0][0]
    elif lmatrix[0][2] == lmatrix[1][1] and lmatrix[1][1] == lmatrix[2][0]:
        result = lmatrix[0][2]
    return result

def check_winner(playerIndex):
    result = 0
    result = check_rows(playerIndex)
    if result == 0:
        result = check_columns(playerIndex)
    if result == 0:
        result = check_diagonals(playerIndex)
    return result

def start_server(): 
    try:
        s.bind((host, port))
        print("Tic Tac Toe server started \nBinding to port", port)
        s.listen(1) 
        accept_players()
    except socket.error as e:
        print("Server binding error:", e)
    


def accept_players():
    global playerIndex
    try:
        while True:
            conn, addr = s.accept()
            conn = context.wrap_socket(conn, server_side=True)
            msg = "<<< You are player {} >>>".format(playerIndex)
            conn.send(msg.encode())

            playerConn[playerIndex] = conn
            available[playerIndex] = '1'
            print("Player {} - [{}:{}]".format(playerIndex, addr[0], str(addr[1])))
            thread = threading.Thread(target=start_game, args=(playerIndex, ))
            thread.start()
            playerIndex += 1
        thread.join()
        s.close()
    except socket.error as e:
        print("Player connection error", e)
    except KeyboardInterrupt:
            print("\nKeyboard Interrupt")
            exit()
    except Exception as e:
        print("Error occurred:", e)

def start_game(playerIndex):
    global roomIndex
    with lock:
        if len(available) % 2 == 0:
            # Pair up players
            players = list(available.keys())
            player1 = players[0]
            player2 = players[1]
            available.pop(player1)
            available.pop(player2)
            rooms[roomIndex] = [player1, player2]
            playroom[player1] = roomIndex
            playroom[player2] = roomIndex
            # Create a new zero matrix for each game
            matrix[roomIndex] = [[0 for _ in range(3)] for _ in range(3)]
            roomIndex += 1

    result = 0
    i = 0
    playerOne = 1
    playerTwo = 2
    while result == 0 and i < 9:
        if (i % 2 == 0):
            get_input(playerOne, rooms[playroom[player1]][0], player1)
        else:
            get_input(playerTwo, rooms[playroom[player2]][1], player2)
        result = check_winner(player1)
        i = i + 1
    
    send_common_msg("Over", playerIndex)

    if result == 1:
        lastmsg = f"Player {player1} is the winner!!"
    elif result == 2:
        lastmsg = f"Player {player2} is the winner!!"
    else:
        lastmsg = "Tie game!! Try again later!"

    send_common_msg(lastmsg, playerIndex)
    time.sleep(5)
    with lock:
        for conn in rooms[playroom[player1]]:
            if conn in playerConn:
                playerConn[conn].close()
    
def send_common_msg(text, playerIndex):
    playerConn[rooms[playroom[playerIndex]][0]].send(text.encode())
    playerConn[rooms[playroom[playerIndex]][1]].send(text.encode())
    time.sleep(1)

start_server()