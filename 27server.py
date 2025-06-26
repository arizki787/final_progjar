# server.py (Versi Bersih Final)
import socket
import threading
import json
import sys
import random

# Daftar merk mobil sebagai kata-kata yang akan ditebak
CAR_BRANDS = [
    "TOYOTA", "HONDA", "NISSAN", "MITSUBISHI", "SUZUKI", "MAZDA", "SUBARU",
    "BMW", "MERCEDES", "AUDI", "VOLKSWAGEN", "PORSCHE", "FERRARI", "LAMBORGHINI",
    "FORD", "CHEVROLET", "DODGE", "JEEP", "CADILLAC", "LINCOLN", "TESLA",
    "HYUNDAI", "KIA", "LEXUS", "INFINITI", "ACURA", "JAGUAR", "BENTLEY",
    "ROLLS", "MASERATI", "BUGATTI", "MCLAREN", "ASTON", "PEUGEOT", "RENAULT"
]

game_rooms = {}
room_lock = threading.Lock()

def do_broadcast(players_list, message, sender_socket=None):
    for client_socket in players_list:
        if client_socket != sender_socket:
            try:
                client_socket.send(message.encode('utf-8'))
            except:
                client_socket.close()

def get_game_state_message(room_name):
    state = game_rooms[room_name]
    turn_socket = state.get('turn')
    
    turn_id = state['players'].index(turn_socket) if turn_socket in state['players'] else -1

    return json.dumps({
        'type': 'game_update', 'display': state['display'],
        'guessed': "".join(sorted(list(state['guessed']))), 'lives': state['lives'],
        'turn': turn_id, 'players_count': len(state['players']), 
        'clue': 'Merk Mobil'
    })

def handle_client(client_socket, addr):
    print(f"[KONEKSI BARU] {addr} terhubung.")
    current_room = None
    try:
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            
            messages_to_send = []
            
            data = json.loads(message)
            print(f"[DEBUG] Pesan dari {addr}: {json.dumps(data)}")
            command = data.get('command')
            print(f"[DEBUG] Command: {command}")

            with room_lock:
                if command == 'join':
                    room_name = data['room']
                    current_room = room_name
                    
                    if room_name not in game_rooms:
                        game_rooms[room_name] = {
                            'word': None, 'guessed': set(), 'display': '', 'lives': 6,
                            'players': [], 'turn': None, 'game_over': False, 'game_started': False
                        }
                        print(f"[GAME] Kamar '{room_name}' dibuat.")

                    room = game_rooms[room_name]
                    if len(room['players']) < 2 and not room['game_started']:
                        my_player_id = len(room['players'])
                        room['players'].append(client_socket)
                        
                        messages_to_send.append((client_socket, json.dumps({'type': 'assign_id', 'id': my_player_id})))
                        
                        if len(room['players']) == 1:
                            messages_to_send.append((client_socket, json.dumps({'type': 'info', 'message': 'Menunggu pemain kedua...'})))
                        elif len(room['players']) == 2:
                            # Auto-start game ketika 2 pemain sudah bergabung
                            room['game_started'] = True
                            room['word'] = random.choice(CAR_BRANDS)
                            room['display'] = ' '.join(['_' if char.isalpha() else char for char in room['word']])
                            room['turn'] = room['players'][0]  # Player 0 mulai duluan
                            
                            print(f"[GAME] Permainan dimulai di '{room_name}' dengan kata: {room['word']}")
                            
                            # Kirim pesan bahwa game dimulai
                            for i, player_socket in enumerate(room['players']):
                                messages_to_send.append((player_socket, json.dumps({
                                    'type': 'info', 
                                    'message': f"Game dimulai! Anda adalah Pemain {i}. Tebak merk mobil!"
                                })))
                            
                            # Kirim game state
                            update_msg = get_game_state_message(current_room)
                            for player_socket in room['players']:
                                messages_to_send.append((player_socket, update_msg))
                        
                        # Broadcast pemain baru bergabung
                        if len(room['players']) < 2:
                            broadcast_msg = json.dumps({'type': 'info', 'message': f"Pemain baru bergabung. Total pemain: {len(room['players'])}/2"})
                            for player_socket in room['players']:
                                if player_socket != client_socket:
                                    messages_to_send.append((player_socket, broadcast_msg))
                    else:
                        messages_to_send.append((client_socket, json.dumps({'type': 'error', 'message': 'Kamar penuh atau permainan sudah dimulai.'})))

                # Hapus command 'set_word' karena tidak diperlukan lagi
                
                elif command == 'guess' and current_room:
                    room = game_rooms.get(current_room)
                    if room and not room['game_over'] and room['turn'] == client_socket and room['game_started']:
                        guess = data['letter'].upper()
                        msg = None
                        current_player_id = room['players'].index(client_socket)
                        
                        if len(guess) == 1 and guess.isalpha():
                            if guess in room['guessed']:
                                # Huruf sudah pernah ditebak
                                messages_to_send.append((client_socket, json.dumps({
                                    'type': 'info', 
                                    'message': f"❌ Huruf '{guess}' sudah pernah ditebak! Coba huruf lain."
                                })))
                                # Kirim game state untuk refresh tampilan
                                msg = get_game_state_message(current_room)
                                for player_socket in room['players']:
                                    messages_to_send.append((player_socket, msg))
                            else:
                                # Huruf belum pernah ditebak
                                room['guessed'].add(guess)
                                
                                if guess in room['word']:
                                    # Update display dengan huruf yang benar
                                    display_list = list(room['display'])
                                    for i, letter in enumerate(room['word']):
                                        if letter == guess:
                                            display_list[i*2] = guess
                                    room['display'] = "".join(display_list)
                                    
                                    # Cek apakah kata sudah lengkap
                                    if '_' not in room['display']:
                                        room['game_over'] = True
                                        msg = json.dumps({
                                            'type': 'game_over', 
                                            'message': f"🎉 PEMAIN {current_player_id} MENANG! 🎉\nKata: {room['word']}\nPemain {current_player_id} menebak huruf terakhir!"
                                        })
                                    else:
                                        # Ganti giliran ke pemain lain
                                        current_idx = room['players'].index(room['turn'])
                                        next_idx = (current_idx + 1) % len(room['players'])
                                        room['turn'] = room['players'][next_idx]
                                        msg = get_game_state_message(current_room)
                                else:
                                    # Huruf salah, kurangi nyawa
                                    room['lives'] -= 1
                                    
                                    if room['lives'] <= 0:
                                        room['game_over'] = True
                                        other_player_id = 1 - current_player_id
                                        msg = json.dumps({
                                            'type': 'game_over', 
                                            'message': f"💀 PEMAIN {current_player_id} KALAH! 💀\nKata: {room['word']}\nPEMAIN {other_player_id} MENANG karena lawan melengkapi hangman!"
                                        })
                                    else:
                                        # Ganti giliran ke pemain lain
                                        current_idx = room['players'].index(room['turn'])
                                        next_idx = (current_idx + 1) % len(room['players'])
                                        room['turn'] = room['players'][next_idx]
                                        msg = get_game_state_message(current_room)
                                
                                # Kirim message ke semua pemain untuk kasus huruf baru
                                for player_socket in room['players']:
                                    messages_to_send.append((player_socket, msg))
                        else:
                            # Input tidak valid (bukan huruf atau lebih dari 1 karakter)
                            messages_to_send.append((client_socket, json.dumps({
                                'type': 'info', 
                                'message': f"❌ Input tidak valid! Masukkan hanya satu huruf."
                            })))
                            # Kirim game state untuk refresh tampilan
                            msg = get_game_state_message(current_room)
                            for player_socket in room['players']:
                                messages_to_send.append((player_socket, msg))

            for sock, message_string in messages_to_send:
                try:
                    # Add newline delimiter to separate JSON messages
                    sock.send((message_string + '\n').encode('utf-8'))
                except Exception as e:
                    print(f"[ERROR KIRIM] Gagal mengirim ke salah satu klien: {e}")
    
    except Exception as e:
        print(f"Error pada koneksi {addr}: {e}")
    finally:
        print(f"[KONEKSI PUTUS] {addr} terputus.")
        # Di sini bisa ditambahkan logika untuk membersihkan pemain yang disconnect dari 'game_rooms'
        client_socket.close()

def main(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[*] Server berjalan di {host}:{port}")
    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()

if __name__ == "__main__":
    HOST = '0.0.0.0'
    PORT = 9999
    if len(sys.argv) == 2:
        PORT = int(sys.argv[1])
    main(HOST, PORT)