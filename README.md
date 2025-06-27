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

Aplikasi ini merupakan implementasi permainan **Hangman** klasik dalam versi **multiplayer** berbasis jaringan. Dua pemain dapat bergabung ke dalam satu kamar untuk saling bersaing menebak kata bertema **merek mobil terkenal** yang dipilih secara acak oleh server.

Aplikasi ini terdiri dari dua komponen utama:

* **Server (`27server.py`)**
  Bertugas mengatur alur permainan, mengelola koneksi client, membuat kamar, memilih kata secara acak, memvalidasi tebakan, mengatur giliran, menghitung nyawa, serta menentukan pemenang. Menggunakan modul `threading`, server mampu menangani banyak kamar secara bersamaan.

* **Client (`client_pygame.py`)**
  Antarmuka grafis berbasis **Pygame** yang digunakan pemain untuk membuat/bergabung ke kamar dan bermain. Menampilkan visual hangman, kata yang ditebak, giliran bermain, serta input huruf secara interaktif.

---

## Alur Aplikasi & Antarmuka Pengguna

### 1. Menu Utama

Pemain akan melihat tampilan awal dengan dua opsi:

* **Buat Kamar** – Membuat ruang permainan baru.
* **Gabung Kamar** – Masuk ke kamar yang sudah ada.

Di bagian bawah, terdapat instruksi dasar permainan.

*Gambar 1: Menu Utama*
![MENUAWAL](https://github.com/user-attachments/assets/6de45a04-bcc3-42fd-8a6b-d65c52434f88)


---

### 2. Membuat dan Bergabung Kamar

Setelah memilih opsi, pemain akan memasukkan **nama kamar**.

* **Buat Kamar:** Membuat kamar baru.
* **Gabung Kamar:** Terhubung ke kamar yang sudah dibuat.

*Gambar 2: Buat Kamar*
![BUATKAMAR](https://github.com/user-attachments/assets/854fa81d-64d8-4781-8dd2-5d6852899966)


*Gambar 3: Gabung Kamar*
![GABUNGKAMAR](https://github.com/user-attachments/assets/d1b4070f-9780-4a75-ad42-1079819a0576)


---

### 3. Fase Permainan

Jika pemain pertama sudah masuk kamar, layar akan menampilkan status *Menunggu Pemain Kedua*. Setelah dua pemain masuk, permainan dimulai.

Elemen yang ditampilkan:

* Visualisasi hangman
* Kata dengan garis bawah (`_`)
* Sisa nyawa
* Huruf-huruf yang sudah ditebak
* Giliran pemain

Pemain dapat menebak **satu huruf** di gilirannya.

---

### 4. Akhir Permainan

Permainan selesai jika:

* Kata berhasil ditebak oleh salah satu pemain
* Pemain kehabisan nyawa

*Gambar 4: Pemain Menang*
![WIN](https://github.com/user-attachments/assets/bac7b21e-06fa-4fdb-b6a4-cb4e487b2e81)


*Gambar 5: Pemain Kalah*
![LOSE](https://github.com/user-attachments/assets/9c52a1be-1228-4d9e-b4a1-b5162198b05a)


Pada akhir permainan, kata yang benar ditampilkan dan pemain bisa memilih opsi **Main Lagi**.

---

## Definisi Protokol

Komunikasi dilakukan melalui **TCP/IP** dengan format pesan **JSON**, diakhiri newline (`\n`).

### 🔁 Client → Server

```json
{"command": "join", "room": "nama_kamar"}
```

```json
{"command": "guess", "letter": "A"}
```

### Server → Client

* **assign\_id**

  ```json
  {"type": "assign_id", "id": 0}
  ```

* **info / error**

  ```json
  {"type": "info", "message": "Menunggu pemain kedua..."}
  ```

* **game\_update**

  ```json
  {
    "type": "game_update",
    "display": "_ _ _ _",
    "guessed": "AEI",
    "lives": 5,
    "turn": 1,
    "players_count": 2,
    "clue": "Merk Mobil"
  }
  ```

* **game\_over**

  ```json
  {"type": "game_over", "message": "PEMAIN 0 MENANG! Kata: HONDA"}
  ```

---

## Arsitektur

### IP Address

* **Server:** `0.0.0.0` – Mendengarkan semua koneksi jaringan.
* **Client:** Default `127.0.0.1` (localhost), bisa diubah di dalam kode.

### Port

* Default menggunakan **port 9999** untuk koneksi TCP.
* Bisa dikustomisasi melalui argumen saat menjalankan server.

---

## Repository

🔗 [Klik di sini untuk mengakses repository](https://github.com/arizki787/final_progjar.git)

---
