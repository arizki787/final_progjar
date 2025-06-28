import sys
import os.path
import uuid
from glob import glob
from datetime import datetime
import json
import random
import threading

# Daftar merk mobil sebagai kata-kata yang akan ditebak
CAR_BRANDS = [
    "TOYOTA", "HONDA", "NISSAN", "MITSUBISHI", "SUZUKI", "MAZDA", "SUBARU",
    "BMW", "MERCEDES", "AUDI", "VOLKSWAGEN", "PORSCHE", "FERRARI", "LAMBORGHINI",
    "FORD", "CHEVROLET", "DODGE", "JEEP", "CADILLAC", "LINCOLN", "TESLA",
    "HYUNDAI", "KIA", "LEXUS", "INFINITI", "ACURA", "JAGUAR", "BENTLEY",
    "ROLLS", "MASERATI", "BUGATTI", "MCLAREN", "ASTON", "PEUGEOT", "RENAULT"
]

# Global game rooms dan lock
game_rooms = {}
room_lock = threading.Lock()

class HttpServer:
	def __init__(self):
		self.sessions={}
		self.types={}
		self.types['.pdf']='application/pdf'
		self.types['.jpg']='image/jpeg'
		self.types['.txt']='text/plain'
		self.types['.html']='text/html'
		self.types['.json']='application/json'
	
	def process_json_message(self, message, client_socket):
		"""Process JSON message from pygame client"""
		try:
			data = json.loads(message)
			command = data.get('command')
			
			print(f"[DEBUG] Received command: {command} from {client_socket}")
			
			if command == 'join':
				return self.handle_join_command(data, client_socket)
			elif command == 'guess':
				return self.handle_guess_command(data, client_socket)
			else:
				return [json.dumps({'type': 'error', 'message': 'Unknown command'})]
		
		except json.JSONDecodeError:
			return [json.dumps({'type': 'error', 'message': 'Invalid JSON'})]
		except Exception as e:
			print(f"Error processing JSON message: {e}")
			return [json.dumps({'type': 'error', 'message': 'Server error'})]
	
	def handle_join_command(self, data, client_socket):
		"""Handle join room command"""
		room_name = data.get('room')
		if not room_name:
			return [json.dumps({'type': 'error', 'message': 'Room name required'})]
		
		messages_to_send = []
		
		with room_lock:
			if room_name not in game_rooms:
				game_rooms[room_name] = {
					'word': None, 'guessed': set(), 'display': '', 'lives': 6,
					'players': [], 'turn': None, 'game_over': False, 'game_started': False
				}
				print(f"[GAME] Room '{room_name}' created.")
			
			room = game_rooms[room_name]
			if len(room['players']) < 2 and not room['game_started']:
				my_player_id = len(room['players'])
				room['players'].append(client_socket)
				
				messages_to_send.append(json.dumps({'type': 'assign_id', 'id': my_player_id}))
				
				if len(room['players']) == 1:
					messages_to_send.append(json.dumps({'type': 'info', 'message': 'Menunggu pemain kedua...'}))
				elif len(room['players']) == 2:
					# Auto-start game ketika 2 pemain sudah bergabung
					room['game_started'] = True
					room['word'] = random.choice(CAR_BRANDS)
					room['display'] = ' '.join(['_' if char.isalpha() else char for char in room['word']])
					room['turn'] = room['players'][0]  # Player 0 mulai duluan
					
					print(f"[GAME] Game started in '{room_name}' with word: {room['word']}")
					
					# Kirim pesan bahwa game dimulai untuk semua player
					for i, player_socket in enumerate(room['players']):
						messages_to_send.append(json.dumps({
							'type': 'info', 
							'message': f"Game dimulai! Anda adalah Pemain {i}. Tebak merk mobil!"
						}))
					
					# Kirim game state untuk semua player
					game_state_msg = self.get_game_state_message(room_name)
					messages_to_send.append(game_state_msg)
			else:
				messages_to_send.append(json.dumps({'type': 'error', 'message': 'Kamar penuh atau permainan sudah dimulai.'}))
		
		return messages_to_send
	
	def handle_guess_command(self, data, client_socket):
		"""Handle guess letter command"""
		letter = data.get('letter', '').upper()
		
		# Find room yang mengandung client socket ini
		current_room = None
		with room_lock:
			for room_name, room_data in game_rooms.items():
				if client_socket in room_data.get('players', []):
					current_room = room_name
					break
		
		if not current_room:
			return [json.dumps({'type': 'error', 'message': 'You are not in any room'})]
		
		messages_to_send = []
		
		with room_lock:
			room = game_rooms[current_room]
			if room and not room['game_over'] and room['turn'] == client_socket and room['game_started']:
				current_player_id = room['players'].index(client_socket)
				
				if len(letter) == 1 and letter.isalpha():
					if letter in room['guessed']:
						# Huruf sudah pernah ditebak
						messages_to_send.append(json.dumps({
							'type': 'info', 
							'message': f"❌ Huruf '{letter}' sudah pernah ditebak! Coba huruf lain."
						}))
						# Kirim game state untuk refresh tampilan
						game_state_msg = self.get_game_state_message(current_room)
						messages_to_send.append(game_state_msg)
					else:
						# Huruf belum pernah ditebak
						room['guessed'].add(letter)
						
						if letter in room['word']:
							# Update display dengan huruf yang benar
							display_list = list(room['display'])
							for i, char in enumerate(room['word']):
								if char == letter:
									display_list[i*2] = letter
							room['display'] = "".join(display_list)
							
							# Cek apakah kata sudah lengkap
							if '_' not in room['display']:
								room['game_over'] = True
								messages_to_send.append(json.dumps({
									'type': 'game_over', 
									'message': f"🎉 PEMAIN {current_player_id} MENANG! 🎉\nKata: {room['word']}\nPemain {current_player_id} menebak huruf terakhir!"
								}))
							else:
								# Ganti giliran ke pemain lain
								current_idx = room['players'].index(room['turn'])
								next_idx = (current_idx + 1) % len(room['players'])
								room['turn'] = room['players'][next_idx]
								game_state_msg = self.get_game_state_message(current_room)
								messages_to_send.append(game_state_msg)
						else:
							# Huruf salah, kurangi nyawa
							room['lives'] -= 1
							
							if room['lives'] <= 0:
								room['game_over'] = True
								other_player_id = 1 - current_player_id
								messages_to_send.append(json.dumps({
									'type': 'game_over', 
									'message': f"💀 PEMAIN {current_player_id} KALAH! 💀\nKata: {room['word']}\nPEMAIN {other_player_id} MENANG karena lawan melengkapi hangman!"
								}))
							else:
								# Ganti giliran ke pemain lain
								current_idx = room['players'].index(room['turn'])
								next_idx = (current_idx + 1) % len(room['players'])
								room['turn'] = room['players'][next_idx]
								game_state_msg = self.get_game_state_message(current_room)
								messages_to_send.append(game_state_msg)
				else:
					# Input tidak valid
					messages_to_send.append(json.dumps({
						'type': 'info', 
						'message': f"❌ Input tidak valid! Masukkan hanya satu huruf."
					}))
					game_state_msg = self.get_game_state_message(current_room)
					messages_to_send.append(game_state_msg)
			else:
				messages_to_send.append(json.dumps({'type': 'error', 'message': 'Not your turn or game not active'}))
		
		return messages_to_send
	
	def get_game_state_message(self, room_name):
		"""Get current game state as JSON message"""
		state = game_rooms[room_name]
		turn_socket = state.get('turn')
		
		turn_id = state['players'].index(turn_socket) if turn_socket in state['players'] else -1
		
		return json.dumps({
			'type': 'game_update', 
			'display': state['display'],
			'guessed': "".join(sorted(list(state['guessed']))), 
			'lives': state['lives'],
			'turn': turn_id, 
			'players_count': len(state['players']), 
			'clue': 'Merk Mobil'
		})

	def response(self,kode=404,message='Not Found',messagebody=bytes(),headers={}):
		tanggal = datetime.now().strftime('%c')
		resp=[]
		resp.append("HTTP/1.0 {} {}\r\n" . format(kode,message))
		resp.append("Date: {}\r\n" . format(tanggal))
		resp.append("Connection: close\r\n")
		resp.append("Server: myserver/1.0\r\n")
		resp.append("Content-Length: {}\r\n" . format(len(messagebody)))
		for kk in headers:
			resp.append("{}:{}\r\n" . format(kk,headers[kk]))
		resp.append("\r\n")

		response_headers=''
		for i in resp:
			response_headers="{}{}" . format(response_headers,i)
		#menggabungkan resp menjadi satu string dan menggabungkan dengan messagebody yang berupa bytes
		#response harus berupa bytes
		#message body harus diubah dulu menjadi bytes
		if (type(messagebody) is not bytes):
			messagebody = messagebody.encode()

		response = response_headers.encode() + messagebody
		#response adalah bytes
		return response

	def proses(self,data):
		
		requests = data.split("\r\n")
		#print(requests)

		baris = requests[0]
		#print(baris)

		all_headers = [n for n in requests[1:] if n!='']

		j = baris.split(" ")
		try:
			method=j[0].upper().strip()
			if (method=='GET'):
				object_address = j[1].strip()
				return self.http_get(object_address, all_headers)
			if (method=='POST'):
				object_address = j[1].strip()
				return self.http_post(object_address, all_headers)
			else:
				return self.response(400,'Bad Request','',{})
		except IndexError:
			return self.response(400,'Bad Request','',{})
	def http_get(self,object_address,headers):
		files = glob('./*')
		#print(files)
		thedir='./'
		if (object_address == '/'):
			return self.response(200,'OK','Ini Adalah web Server percobaan',dict())

		if (object_address == '/video'):
			return self.response(302,'Found','',dict(location='https://youtu.be/katoxpnTf04'))
		if (object_address == '/santai'):
			return self.response(200,'OK','santai saja',dict())


		object_address=object_address[1:]
		if thedir+object_address not in files:
			return self.response(404,'Not Found','',{})
		fp = open(thedir+object_address,'rb') #rb => artinya adalah read dalam bentuk binary
		#harus membaca dalam bentuk byte dan BINARY
		isi = fp.read()
		
		fext = os.path.splitext(thedir+object_address)[1]
		content_type = self.types[fext]
		
		headers={}
		headers['Content-type']=content_type
		
		return self.response(200,'OK',isi,headers)
	def http_post(self,object_address,headers):
		headers ={}
		isi = "kosong"
		return self.response(200,'OK',isi,headers)
		
			 	
#>>> import os.path
#>>> ext = os.path.splitext('/ak/52.png')

if __name__=="__main__":
	httpserver = HttpServer()
	d = httpserver.proses('GET testing.txt HTTP/1.0')
	print(d)
	d = httpserver.proses('GET donalbebek.jpg HTTP/1.0')
	print(d)
	#d = httpserver.http_get('testing2.txt',{})
	#print(d)
#	d = httpserver.http_get('testing.txt')
#	print(d)
