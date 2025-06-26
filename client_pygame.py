# client_pygame.py - Hangman Multiplayer with Pygame GUI
import pygame
import socket
import threading
import json
import sys
import time

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 200)
GREEN = (0, 150, 0)
RED = (200, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_BLUE = (0, 50, 100)

# Game states
STATE_MENU = "menu"
STATE_CREATE_ROOM = "create_room"
STATE_JOIN_ROOM = "join_room"
STATE_WAITING = "waiting"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"

class HangmanClient:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Hangman Multiplayer - Tebak Merk Mobil")
        self.clock = pygame.time.Clock()
        
        # Try to use system font that supports emojis, fallback to default
        self.emoji_support = False
        try:
            # Try different system fonts that might support emojis
            font_names = ['segoeuiemoji', 'segoeui', 'arial unicode ms', 'noto color emoji']
            for font_name in font_names:
                try:
                    test_font = pygame.font.SysFont(font_name, 28)
                    # Test if font can render emoji
                    test_surface = test_font.render('🏎️', True, BLACK)
                    if test_surface.get_width() > 10:  # Basic check if emoji rendered
                        self.font = pygame.font.SysFont(font_name, 28)
                        self.big_font = pygame.font.SysFont(font_name, 42)
                        self.small_font = pygame.font.SysFont(font_name, 20)
                        self.emoji_support = True
                        break
                except:
                    continue
        except:
            pass
        
        # Fallback to default fonts if no emoji support
        if not self.emoji_support:
            self.font = pygame.font.Font(None, 36)
            self.big_font = pygame.font.Font(None, 48)
            self.small_font = pygame.font.Font(None, 24)
        
        # Game state
        self.state = STATE_MENU
        self.client_socket = None
        self.is_my_turn = False
        self.my_player_id = -1
        self.game_is_active = True
        self.waiting_for_input = False
        
        # Game data
        self.display_word = ""
        self.guessed_letters = ""
        self.lives = 6
        self.turn_player = -1
        self.clue = "Merk Mobil"
        self.message = ""
        self.game_over_message = ""
        self.is_winner = False  # Flag untuk menentukan menang/kalah
        self.final_word = ""    # Kata terakhir untuk ditampilkan
        
        # Input handling
        self.input_text = ""
        self.input_active = False
        
        # Network thread
        self.network_thread = None
        
    def connect_to_server(self, host="127.0.0.1", port=9999):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
            
            # Start network thread
            self.network_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.network_thread.start()
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def receive_messages(self):
        buffer = ""
        while self.game_is_active:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                
                buffer += message
                
                # Process all complete lines (JSON messages) in the buffer
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self.process_message(data)
                        except json.JSONDecodeError as e:
                            print(f"JSON Error: {e}")
                            
            except Exception as e:
                print(f"Connection error: {e}")
                self.game_is_active = False
                break
    
    def process_message(self, data):
        try:
            print(f"[DEBUG] Received message: {data}")  # Debug print
            
            if data['type'] == 'info' or data['type'] == 'error':
                self.message = data['message']
                print(f"[DEBUG] Info/Error message: {self.message}")
                # Jika masih di waiting state dan mendapat info tentang game dimulai, tetap di waiting
                if self.state == STATE_WAITING and "Game dimulai" in data['message']:
                    # Game akan segera dimulai, tunggu game_update
                    pass
            
            elif data['type'] == 'assign_id':
                self.my_player_id = data['id']
                self.message = f"Anda terhubung sebagai Pemain {self.my_player_id}"
                print(f"[DEBUG] Assigned player ID: {self.my_player_id}")
                # Tetap di STATE_WAITING sampai ada game_update atau info lain
            
            elif data['type'] == 'game_update':
                print(f"[DEBUG] Game update received, switching to PLAYING state")
                self.state = STATE_PLAYING
                self.is_my_turn = (data['turn'] == self.my_player_id)
                self.display_word = data['display']
                self.guessed_letters = data['guessed']
                self.lives = data['lives']
                self.turn_player = data['turn']
                self.clue = data.get('clue', 'Merk Mobil')
                
                if self.is_my_turn:
                    self.message = f"Giliran Anda (Pemain {self.my_player_id})!"
                    self.waiting_for_input = True
                    self.input_active = True  # Auto-activate input for turn
                else:
                    self.message = f"Menunggu Pemain {self.turn_player}..."
                    self.waiting_for_input = False
                    self.input_active = False
            
            elif data['type'] == 'game_over':
                print(f"[DEBUG] Game over received")
                self.state = STATE_GAME_OVER
                self.game_over_message = data['message']
                self.waiting_for_input = False
                self.input_active = False
                
                # Parse game over message untuk menentukan winner
                message = data['message']
                if "MENANG" in message:
                    # Cek apakah player ini yang menang
                    if f"PEMAIN {self.my_player_id} MENANG" in message:
                        self.is_winner = True
                    else:
                        self.is_winner = False
                elif "KALAH" in message:
                    # Cek apakah player ini yang kalah
                    if f"PEMAIN {self.my_player_id} KALAH" in message:
                        self.is_winner = False
                    else:
                        self.is_winner = True
                
                # Extract final word dari message
                if "Kata:" in message:
                    try:
                        self.final_word = message.split("Kata:")[1].split("\n")[0].strip()
                    except:
                        self.final_word = "Unknown"
                
        except KeyError as e:
            print(f"Missing key: {e}")
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def send_join_room(self, room_name):
        if self.client_socket:
            message = json.dumps({'command': 'join', 'room': room_name})
            self.client_socket.send(message.encode('utf-8'))
    
    def send_guess(self, letter):
        if self.client_socket and self.is_my_turn:
            message = json.dumps({'command': 'guess', 'letter': letter})
            self.client_socket.send(message.encode('utf-8'))
            self.waiting_for_input = False
    
    def draw_button(self, text, x, y, width, height, color=LIGHT_GRAY, text_color=BLACK):
        pygame.draw.rect(self.screen, color, (x, y, width, height))
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
        text_surface = self.font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(text_surface, text_rect)
        return pygame.Rect(x, y, width, height)
    
    def draw_input_box(self, x, y, width, height, active=False):
        color = BLUE if active else GRAY
        pygame.draw.rect(self.screen, WHITE, (x, y, width, height))
        pygame.draw.rect(self.screen, color, (x, y, width, height), 2)
        text_surface = self.font.render(self.input_text, True, BLACK)
        self.screen.blit(text_surface, (x + 5, y + 5))
        return pygame.Rect(x, y, width, height)
    
    def draw_hangman(self, lives):
        # Simple hangman drawing
        x, y = 150, 150
        
        # Gallows
        pygame.draw.line(self.screen, BLACK, (x, y + 200), (x + 100, y + 200), 5)  # Base
        pygame.draw.line(self.screen, BLACK, (x + 20, y + 200), (x + 20, y), 5)    # Pole
        pygame.draw.line(self.screen, BLACK, (x + 20, y), (x + 80, y), 5)          # Top
        pygame.draw.line(self.screen, BLACK, (x + 80, y), (x + 80, y + 30), 5)     # Noose
        
        # Body parts (drawn when lives decrease)
        if lives <= 5:  # Head
            pygame.draw.circle(self.screen, BLACK, (x + 80, y + 50), 20, 3)
        if lives <= 4:  # Body
            pygame.draw.line(self.screen, BLACK, (x + 80, y + 70), (x + 80, y + 150), 5)
        if lives <= 3:  # Left arm
            pygame.draw.line(self.screen, BLACK, (x + 80, y + 90), (x + 50, y + 120), 3)
        if lives <= 2:  # Right arm
            pygame.draw.line(self.screen, BLACK, (x + 80, y + 90), (x + 110, y + 120), 3)
        if lives <= 1:  # Left leg
            pygame.draw.line(self.screen, BLACK, (x + 80, y + 150), (x + 60, y + 180), 3)
        if lives <= 0:  # Right leg
            pygame.draw.line(self.screen, BLACK, (x + 80, y + 150), (x + 100, y + 180), 3)
    
    def draw_menu(self):
        self.screen.fill(WHITE)
        
        # Title
        title = self.big_font.render("HANGMAN MULTIPLAYER", True, DARK_BLUE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        subtitle = self.font.render("Tebak Merk Mobil", True, BLUE)
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Buttons
        create_btn = self.draw_button("Buat Kamar", 300, 250, 200, 60, GREEN, WHITE)
        join_btn = self.draw_button("Gabung Kamar", 300, 330, 200, 60, BLUE, WHITE)
        
        # Instructions with emoji support check
        if self.emoji_support:
            instructions = [
                "📝 Setiap kamar maksimal 2 pemain",
                "🎯 Game otomatis dimulai ketika 2 pemain bergabung",
                "🏆 Menang: Tebak huruf terakhir yang melengkapi kata",
                "💀 Kalah: Melengkapi gambar hangman"
            ]
        else:
            instructions = [
                "[*] Setiap kamar maksimal 2 pemain",
                "[>] Game otomatis dimulai ketika 2 pemain bergabung", 
                "[!] Menang: Tebak huruf terakhir yang melengkapi kata",
                "[X] Kalah: Melengkapi gambar hangman"
            ]
        
        y_start = 450
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, BLACK)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, y_start + i * 25))
            self.screen.blit(text, text_rect)
        
        return create_btn, join_btn
    
    def draw_room_input(self, title):
        self.screen.fill(WHITE)
        
        # Title
        title_surface = self.big_font.render(title, True, DARK_BLUE)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(title_surface, title_rect)
        
        # Input label
        label = self.font.render("Nama Kamar:", True, BLACK)
        label_rect = label.get_rect(center=(WINDOW_WIDTH // 2, 250))
        self.screen.blit(label, label_rect)
        
        # Input box
        input_box = self.draw_input_box(250, 280, 300, 40, self.input_active)
        
        # Buttons
        ok_btn = self.draw_button("OK", 300, 350, 80, 40, GREEN, WHITE)
        back_btn = self.draw_button("Kembali", 420, 350, 80, 40, RED, WHITE)
        
        return input_box, ok_btn, back_btn
    
    def draw_waiting(self):
        self.screen.fill(WHITE)
        
        # Title
        title = self.big_font.render("MENUNGGU...", True, DARK_BLUE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)
        
        # Message - handle multiline messages
        if self.message:
            lines = self.message.split('\n') if '\n' in self.message else [self.message]
            y_start = 280
            for i, line in enumerate(lines):
                if line.strip():  # Only render non-empty lines
                    msg_surface = self.font.render(line.strip(), True, BLACK)
                    msg_rect = msg_surface.get_rect(center=(WINDOW_WIDTH // 2, y_start + i * 35))
                    self.screen.blit(msg_surface, msg_rect)
        
        # Loading indicator
        dots = "." * ((pygame.time.get_ticks() // 500) % 4)
        loading_text = self.small_font.render(f"Memuat{dots}", True, GRAY)
        loading_rect = loading_text.get_rect(center=(WINDOW_WIDTH // 2, 400))
        self.screen.blit(loading_text, loading_rect)
    
    def draw_playing(self):
        self.screen.fill(WHITE)
        
        # Title
        title = self.font.render("HANGMAN MULTIPLAYER - TEBAK MERK MOBIL", True, DARK_BLUE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 30))
        self.screen.blit(title, title_rect)
        
        # Hangman drawing
        self.draw_hangman(self.lives)
        
        # Game info
        if self.emoji_support:
            clue_text = self.font.render(f"🏎️ CLUE: {self.clue}", True, BLUE)
        else:
            clue_text = self.font.render(f"[CAR] CLUE: {self.clue}", True, BLUE)
        self.screen.blit(clue_text, (350, 100))
        
        word_text = self.big_font.render(f"Kata: {self.display_word}", True, BLACK)
        self.screen.blit(word_text, (350, 140))
        
        lives_text = self.font.render(f"Nyawa: {self.lives}", True, RED)
        self.screen.blit(lives_text, (350, 190))
        
        guessed_text = self.font.render(f"Huruf Ditebak: {self.guessed_letters}", True, GRAY)
        self.screen.blit(guessed_text, (350, 220))
        
        # Turn info
        if self.message:
            msg_surface = self.font.render(self.message, True, GREEN if self.is_my_turn else BLUE)
            self.screen.blit(msg_surface, (350, 260))
        
        # Input for guessing
        if self.is_my_turn and self.waiting_for_input:
            input_label = self.font.render("Masukkan huruf:", True, BLACK)
            self.screen.blit(input_label, (350, 320))
            
            input_box = self.draw_input_box(350, 350, 100, 40, self.input_active)
            
            submit_btn = self.draw_button("Tebak", 470, 350, 80, 40, GREEN, WHITE)
            return input_box, submit_btn
        
        return None, None
    
    def draw_game_over(self):
        self.screen.fill(WHITE)
        
        # Customized title based on win/lose
        if self.is_winner:
            if self.emoji_support:
                title = self.big_font.render("🎉 YOU WIN! 🎉", True, GREEN)
            else:
                title = self.big_font.render("*** YOU WIN! ***", True, GREEN)
            subtitle = self.font.render("Selamat! Anda adalah pemenangnya!", True, GREEN)
        else:
            if self.emoji_support:
                title = self.big_font.render("💀 YOU LOSE 💀", True, RED)
            else:
                title = self.big_font.render("XXX YOU LOSE XXX", True, RED)
            subtitle = self.font.render("Sayang sekali, coba lagi!", True, RED)
        
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 120))
        self.screen.blit(title, title_rect)
        
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 170))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Show final word
        if self.final_word:
            word_text = self.font.render(f"Kata: {self.final_word}", True, DARK_BLUE)
            word_rect = word_text.get_rect(center=(WINDOW_WIDTH // 2, 220))
            self.screen.blit(word_text, word_rect)
        
        # Show original server message (smaller, for reference)
        if self.game_over_message:
            detail_title = self.small_font.render("Detail Game:", True, GRAY)
            detail_rect = detail_title.get_rect(center=(WINDOW_WIDTH // 2, 270))
            self.screen.blit(detail_title, detail_rect)
            
            lines = self.game_over_message.split('\n')
            y_start = 300
            for i, line in enumerate(lines):
                if line.strip():
                    msg_surface = self.small_font.render(line.strip(), True, GRAY)
                    msg_rect = msg_surface.get_rect(center=(WINDOW_WIDTH // 2, y_start + i * 25))
                    self.screen.blit(msg_surface, msg_rect)
        
        # Back to menu button
        menu_btn = self.draw_button("Main Lagi", 300, 450, 200, 60, BLUE, WHITE)
        return menu_btn
    
    def reset_game(self):
        self.state = STATE_MENU
        self.is_my_turn = False
        self.my_player_id = -1
        self.waiting_for_input = False
        self.display_word = ""
        self.guessed_letters = ""
        self.lives = 6
        self.turn_player = -1
        self.message = ""
        self.game_over_message = ""
        self.is_winner = False
        self.final_word = ""
        self.input_text = ""
        
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.game_is_active = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if self.state == STATE_MENU:
                        create_btn, join_btn = self.draw_menu()
                        if create_btn.collidepoint(mouse_pos):
                            self.state = STATE_CREATE_ROOM
                            self.input_text = ""
                            self.input_active = True
                        elif join_btn.collidepoint(mouse_pos):
                            self.state = STATE_JOIN_ROOM
                            self.input_text = ""
                            self.input_active = True
                    
                    elif self.state in [STATE_CREATE_ROOM, STATE_JOIN_ROOM]:
                        title = "BUAT KAMAR" if self.state == STATE_CREATE_ROOM else "GABUNG KAMAR"
                        input_box, ok_btn, back_btn = self.draw_room_input(title)
                        
                        if input_box.collidepoint(mouse_pos):
                            self.input_active = True
                        else:
                            self.input_active = False
                        
                        if ok_btn.collidepoint(mouse_pos) and self.input_text.strip():
                            if self.connect_to_server():
                                self.send_join_room(self.input_text.strip())
                                # Reset input dan pindah ke waiting state
                                self.input_text = ""
                                self.input_active = False
                                self.state = STATE_WAITING
                                self.message = "Menghubungkan ke server..."
                            else:
                                self.message = "Gagal terhubung ke server!"
                                self.state = STATE_MENU
                        
                        elif back_btn.collidepoint(mouse_pos):
                            self.state = STATE_MENU
                            self.input_text = ""
                    
                    elif self.state == STATE_PLAYING:
                        input_box, submit_btn = self.draw_playing()
                        
                        if input_box and input_box.collidepoint(mouse_pos):
                            self.input_active = True
                        elif submit_btn and submit_btn.collidepoint(mouse_pos) and self.input_text.strip():
                            letter = self.input_text.strip().upper()
                            if len(letter) == 1 and letter.isalpha():
                                self.send_guess(letter)
                                self.input_text = ""
                                self.input_active = False
                        else:
                            # Click outside input areas
                            if not (input_box and input_box.collidepoint(mouse_pos)):
                                self.input_active = False
                    
                    elif self.state == STATE_GAME_OVER:
                        menu_btn = self.draw_game_over()
                        if menu_btn.collidepoint(mouse_pos):
                            self.reset_game()
                
                elif event.type == pygame.KEYDOWN:
                    if self.input_active:
                        if event.key == pygame.K_RETURN:
                            if self.state in [STATE_CREATE_ROOM, STATE_JOIN_ROOM] and self.input_text.strip():
                                if self.connect_to_server():
                                    self.send_join_room(self.input_text.strip())
                                    # Reset input dan pindah ke waiting state
                                    self.input_text = ""
                                    self.input_active = False
                                    self.state = STATE_WAITING
                                    self.message = "Menghubungkan ke server..."
                                else:
                                    self.message = "Gagal terhubung ke server!"
                                    self.state = STATE_MENU
                            elif self.state == STATE_PLAYING and self.input_text.strip():
                                letter = self.input_text.strip().upper()
                                if len(letter) == 1 and letter.isalpha():
                                    self.send_guess(letter)
                                    self.input_text = ""
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_text = self.input_text[:-1]
                        else:
                            if len(self.input_text) < 20:  # Limit input length
                                self.input_text += event.unicode
            
            # Draw current state
            if self.state == STATE_MENU:
                self.draw_menu()
            elif self.state == STATE_CREATE_ROOM:
                self.draw_room_input("BUAT KAMAR")
            elif self.state == STATE_JOIN_ROOM:
                self.draw_room_input("GABUNG KAMAR")
            elif self.state == STATE_WAITING:
                self.draw_waiting()
            elif self.state == STATE_PLAYING:
                self.draw_playing()
            elif self.state == STATE_GAME_OVER:
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        # Cleanup
        if self.client_socket:
            self.client_socket.close()
        pygame.quit()

if __name__ == "__main__":
    client = HangmanClient()
    client.run()
