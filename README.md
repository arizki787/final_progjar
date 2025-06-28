---

# Final Project Pemrograman Jaringan - Kelompok 16: **Hangman Multiplayer**

---

## Anggota Kelompok

| Nama                              | NRP        |
| --------------------------------- | ---------- |
| Roofiif Alria Dzakwan             | 5025221012 |
| Maruli Gilbert Cristopel Hutagaol | 5025221119 |
| Muhammad Rafi Budi Purnama        | 5025221307 |
| Aditya Rizki Muhammad             | 5025221272 |

---

## Deskripsi
Proyek ini adalah adaptasi dari server hangman multiplayer (`27server.py`) ke dalam arsitektur HTTP server yang sudah ada (`http.py` dan `server_thread_http.py`). Server yang dihasilkan dapat melayani **dua jenis koneksi**:

1. **HTTP Requests** - untuk web browser atau HTTP clients
2. **JSON Game Protocol** - untuk pygame client (`client_pygame.py`)

## Struktur File

### File Yang Dimodifikasi:

#### 1. `http.py`
- **Ditambahkan**: 
  - Import tambahan: `json`, `random`, `threading`
  - Konstanta `CAR_BRANDS` untuk daftar merk mobil
  - Global variables `game_rooms` dan `room_lock` untuk manajemen game
  - Method `process_json_message()` untuk menangani pesan JSON dari pygame client
  - Method `handle_join_command()` untuk menangani perintah join room
  - Method `handle_guess_command()` untuk menangani perintah tebak huruf
  - Method `get_game_state_message()` untuk membuat pesan status game
  - Support untuk tipe MIME `application/json`

#### 2. `server_thread_http.py`
- **Ditambahkan**:
  - Import `json` untuk parsing JSON messages
  - Deteksi otomatis jenis koneksi (HTTP vs JSON)
  - Method `broadcast_to_room_players()` untuk broadcast pesan ke semua player di room
  - Method `cleanup_client()` untuk membersihkan client yang disconnect
  - Port default diubah ke 9999 (sama dengan `27server.py`)
  - Improved error handling dan logging

## Protokol Komunikasi

### JSON Protocol (untuk pygame client):
```json
// Join room
{"command": "join", "room": "room_name"}

// Guess letter
{"command": "guess", "letter": "A"}

// Response messages
{"type": "assign_id", "id": 0}
{"type": "info", "message": "Menunggu pemain kedua..."}
{"type": "game_update", "display": "T O _ O T A", "guessed": "ATO", "lives": 6, "turn": 1, "players_count": 2, "clue": "Merk Mobil"}
{"type": "game_over", "message": "🎉 PEMAIN 0 MENANG! 🎉\nKata: TOYOTA\nPemain 0 menebak huruf terakhir!"}
```

### HTTP Protocol (untuk web browser):
- Menggunakan standard HTTP methods (GET, POST)
- Mendukung serving static files
- Backward compatible dengan fungsi HTTP yang sudah ada

## Cara Menjalankan

### 1. Menjalankan Server
```bash
python server_thread_http.py [port]
```
- Port default: 9999
- Server akan mendengarkan di `0.0.0.0:9999`

### 2. Menjalankan Client Pygame
```bash
python client_pygame.py
```
- Client akan terhubung ke `127.0.0.1:9999`
- Mendukung GUI untuk bermain hangman multiplayer

## Fitur Game

### Aturan Permainan:
1. **Maksimal 2 pemain** per room
2. **Auto-start** ketika 2 pemain bergabung
3. **Bergantian** menebak huruf
4. **6 nyawa** untuk setiap game
5. **Tema**: Merk mobil (35 merk tersedia)

### Kondisi Menang/Kalah:
- **Menang**: Menebak huruf terakhir yang melengkapi kata
- **Kalah**: Melengkapi gambar hangman (nyawa habis)

## Contoh Penggunaan
