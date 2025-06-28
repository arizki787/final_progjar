from socket import *
import socket
import threading
import time
import sys
import logging
import json
from http import HttpServer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

httpserver = HttpServer()


class ProcessTheClient(threading.Thread):
	def __init__(self, connection, address):
		self.connection = connection
		self.address = address
		threading.Thread.__init__(self)

	def run(self):
		print(f"[KONEKSI BARU] {self.address} terhubung.")
		rcv = ""
		try:
			while True:
				try:
					data = self.connection.recv(1024)
					if data:
						# Decode data dari socket
						d = data.decode('utf-8')
						rcv = rcv + d
						
						# Cek apakah ini HTTP request atau JSON message
						if rcv.startswith('GET') or rcv.startswith('POST'):
							# HTTP Request
							if rcv.endswith('\r\n\r\n') or '\r\n\r\n' in rcv:
								logging.info("HTTP request dari client: {}".format(rcv[:100]))
								hasil = httpserver.proses(rcv)
								hasil = hasil + "\r\n\r\n".encode()
								logging.info("HTTP response ke client")
								self.connection.sendall(hasil)
								rcv = ""
								self.connection.close()
								break
						else:
							# JSON Message dari pygame client
							# Process semua complete JSON messages yang dipisah dengan newline
							while '\n' in rcv or rcv.endswith('}'):
								if '\n' in rcv:
									line, rcv = rcv.split('\n', 1)
								else:
									line = rcv
									rcv = ""
								
								line = line.strip()
								if line:
									try:
										# Validasi JSON
										json.loads(line)
										logging.info("JSON message dari client: {}".format(line))
										
										# Process JSON message
										responses = httpserver.process_json_message(line, self.connection)
										
										# Send responses
										for response in responses:
											response_with_newline = (response + '\n').encode('utf-8')
											logging.info("JSON response ke client: {}".format(response))
											self.connection.send(response_with_newline)
										
										# Jika ada multiple players, broadcast ke semua player di room yang sama
										self.broadcast_to_room_players(responses)
										
									except json.JSONDecodeError:
										# Belum complete JSON, tunggu data lebih
										rcv = line + '\n' + rcv
										break
									except Exception as e:
										logging.error(f"Error processing JSON: {e}")
										error_response = json.dumps({'type': 'error', 'message': 'Server error'})
										self.connection.send((error_response + '\n').encode('utf-8'))
								
								if not rcv:
									break
					else:
						break
				except OSError as e:
					logging.error(f"Socket error: {e}")
					break
				except Exception as e:
					logging.error(f"Unexpected error: {e}")
					break
		except Exception as e:
			logging.error(f"Error in client thread: {e}")
		finally:
			print(f"[KONEKSI PUTUS] {self.address} terputus.")
			self.cleanup_client()
			self.connection.close()
	
	def broadcast_to_room_players(self, messages):
		"""Broadcast messages to all players in the same room"""
		try:
			from http import game_rooms, room_lock
			
			with room_lock:
				for room_name, room_data in game_rooms.items():
					if self.connection in room_data.get('players', []):
						# Found the room, broadcast to all players except sender
						for message in messages:
							if 'game_update' in message or 'game_over' in message:
								for player_socket in room_data['players']:
									if player_socket != self.connection:
										try:
											player_socket.send((message + '\n').encode('utf-8'))
											logging.info(f"Broadcasted to player in room {room_name}: {message}")
										except Exception as e:
											logging.error(f"Failed to broadcast to player: {e}")
						break
		except Exception as e:
			logging.error(f"Error broadcasting: {e}")
	
	def cleanup_client(self):
		"""Remove client from game rooms"""
		try:
			from http import game_rooms, room_lock
			
			with room_lock:
				for room_name, room_data in list(game_rooms.items()):
					if self.connection in room_data.get('players', []):
						room_data['players'].remove(self.connection)
						logging.info(f"Removed client from room {room_name}")
						
						# If room is empty, remove it
						if len(room_data['players']) == 0:
							del game_rooms[room_name]
							logging.info(f"Removed empty room {room_name}")
						break
		except Exception as e:
			logging.error(f"Error cleaning up client: {e}")



class Server(threading.Thread):
	def __init__(self, port=9999):
		self.the_clients = []
		self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.port = port
		threading.Thread.__init__(self)

	def run(self):
		self.my_socket.bind(('0.0.0.0', self.port))
		self.my_socket.listen(5)
		print(f"[*] Server berjalan di 0.0.0.0:{self.port}")
		print("[*] Mendukung HTTP requests dan JSON game protocol")
		while True:
			self.connection, self.client_address = self.my_socket.accept()
			logging.info("connection from {}".format(self.client_address))

			clt = ProcessTheClient(self.connection, self.client_address)
			clt.start()
			self.the_clients.append(clt)



def main():
	PORT = 9999
	if len(sys.argv) == 2:
		PORT = int(sys.argv[1])
	
	svr = Server(PORT)
	svr.start()
	
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print("\n[*] Server shutting down...")
		sys.exit(0)

if __name__=="__main__":
	main()