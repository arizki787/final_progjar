Tentu, berikut adalah `README.md` yang telah diformat dengan rapi. Anda bisa langsung menyalin dan menempelkannya ke GitHub.

-----

# **Final Project Pemrograman Jaringan KELOMPOK 19: Hangman Multiplayer**


-----

## **Anggota Kelompok 19**

| Nama | NRP |
| :--- | :--- |
| Roofiif Alria Dzakwan | 5025221012 |
| Maruli Gilbert Cristopel Hutagaol | 5025221119 |
| Muhammad Rafi Budi Purnama | 5025221307 |
| Aditya Rizki Muhammad | 5025221272 |


## **Deskripsi**

Aplikasi ini adalah implementasi dari permainan Hangman klasik yang dirancang untuk dimainkan oleh dua orang (multiplayer). Pemain dapat terhubung ke sebuah server, masuk ke dalam "kamar" permainan, dan bersaing untuk menebak kata yang telah dipilih secara acak oleh server. Tema dari kata-kata yang harus ditebak adalah merk-merk mobil terkenal.

Aplikasi ini terdiri dari dua komponen utama yang saling berinteraksi:

  * **Server (`27server.py`):** Bertindak sebagai pusat kendali permainan. Server bertanggung jawab untuk mengelola koneksi dari client, membuat kamar permainan, memilih kata secara acak dari daftar yang telah ditentukan, memvalidasi setiap tebakan yang dikirim oleh pemain, mengelola giliran bermain, menghitung sisa nyawa (kesempatan menebak), dan pada akhirnya menentukan pemenang serta pecundang. Dengan menggunakan `threading`, server mampu menangani beberapa kamar permainan secara simultan.
  * **Client (`client_pygame.py`):** Merupakan antarmuka grafis (GUI) yang digunakan oleh pemain untuk berinteraksi dengan game. Dibuat menggunakan library Pygame, client menyediakan visualisasi yang menarik dan fungsionalitas yang mudah digunakan. Pemain dapat membuat atau bergabung ke dalam kamar, melihat status permainan (termasuk gambar hangman yang terbentuk, sisa nyawa, dan kata yang sedang ditebak), serta memasukkan tebakan huruf.

-----

## **Alur Aplikasi & Antarmuka Pengguna**

Bagian ini menjelaskan alur penggunaan aplikasi dari sudut pandang pemain, dilengkapi dengan tangkapan layar antarmuka pengguna (GUI).

### **1. Menu Utama**

Saat aplikasi client (`client_pygame.py`) dijalankan, pemain akan disambut dengan menu utama. Tampilan ini memberikan dua opsi utama untuk memulai permainan.

  * **Buat Kamar:** Opsi untuk membuat sebuah ruang permainan baru.
  * **Gabung Kamar:** Opsi untuk bergabung dengan ruang permainan yang sudah ada.

Di bagian bawah, terdapat instruksi singkat mengenai aturan dasar permainan, seperti jumlah maksimal pemain dan kondisi menang/kalah.
*Tampilan Menu awal:*
![MENUAWAL](https://github.com/user-attachments/assets/6de45a04-bcc3-42fd-8a6b-d65c52434f88)
\<br\> *Gambar 1. Menu Awal*
### **2. Membuat dan Bergabung dengan Kamar**

Setelah memilih salah satu opsi dari menu utama, pemain akan diarahkan ke halaman untuk memasukkan "Nama Kamar".

  * Jika pemain memilih **"Buat Kamar"**, ia akan membuat kamar baru dengan nama yang dimasukkan.
  * Jika pemain memilih **"Gabung Kamar"**, ia akan mencoba terhubung ke kamar dengan nama yang sesuai.

Pemain harus menekan tombol "OK" untuk melanjutkan atau "Kembali" untuk membatalkan. Setelah menekan "OK", client akan mengirimkan perintah `join` ke server.

*Tampilan untuk membuat kamar baru:*
![BUATKAMAR](https://github.com/user-attachments/assets/854fa81d-64d8-4781-8dd2-5d6852899966)

\<br\> *Gambar 2. Buat kamar*

*Tampilan untuk bergabung dengan kamar yang sudah ada:*
![GABUNGKAMAR](https://github.com/user-attachments/assets/d1b4070f-9780-4a75-ad42-1079819a0576)

\<br\> *Gambar 3. Gabung kamar*

### **3. Fase Permainan**

Setelah berhasil terhubung, pemain akan masuk ke dalam fase permainan. Jika pemain adalah orang pertama di kamar, ia akan berada di layar "Menunggu..." sampai pemain kedua bergabung. Ketika dua pemain sudah ada di dalam kamar, permainan akan otomatis dimulai. Selama permainan, antarmuka akan menampilkan:

  * Gambar hangman yang akan bertambah bagian tubuhnya setiap ada tebakan yang salah.
  * Kata yang harus ditebak, direpresentasikan dengan garis bawah (`_`).
  * Jumlah nyawa yang tersisa.
  * Huruf-huruf yang sudah pernah ditebak.
  * Informasi giliran pemain.

Pemain yang mendapat giliran dapat memasukkan satu huruf sebagai tebakannya.

### **4. Akhir Permainan: Menang atau Kalah**

Permainan berakhir ketika salah satu pemain berhasil menebak kata tersebut atau ketika salah satu pemain kehabisan nyawa (gambar hangman lengkap).

  * **Kondisi Menang:** Pemain dinyatakan menang jika ia yang memberikan tebakan huruf terakhir yang melengkapi kata. Layar kemenangan akan ditampilkan dengan pesan selamat.
  * **Kondisi Kalah:** Pemain dinyatakan kalah jika lawan berhasil menebak kata terlebih dahulu, atau jika pemain tersebut membuat tebakan salah yang menghabiskan nyawa terakhir.

Pada kedua layar akhir, kata yang benar akan ditampilkan. Terdapat juga tombol "Main Lagi" yang akan mengembalikan pemain ke menu utama untuk memulai permainan baru.

*Tampilan Menang:*
![WIN](https://github.com/user-attachments/assets/bac7b21e-06fa-4fdb-b6a4-cb4e487b2e81)

\<br\> *Gambar 4. Tampilan menang*

*Tampilan Kalah:*
![LOSE](https://github.com/user-attachments/assets/77b181a6-80eb-466c-9c55-9c9fd8f330a7)

\<br\> *Gambar 5. Tampilan Kalah*

-----

## **Definisi Protokol**

Komunikasi antara client dan server dilakukan melalui protokol TCP/IP dengan format pesan menggunakan JSON. Setiap pesan yang dikirim adalah sebuah objek JSON yang dienkode ke dalam format UTF-8 dan diakhiri dengan karakter newline (`\n`) sebagai pembatas.

### **Pesan dari Client ke Server**

Client mengirimkan perintah ke server dengan struktur JSON berikut: `{"command": "nama_perintah", "parameter": "nilai"}`

  * **`join`**: Perintah untuk bergabung ke sebuah kamar permainan.

      * **Parameter**: `room` (string) - Nama kamar yang ingin dimasuki.
      * **Contoh**: `{"command": "join", "room": "kamar123"}`

  * **`guess`**: Perintah untuk menebak sebuah huruf.

      * **Parameter**: `letter` (string) - Huruf yang ditebak oleh pemain.
      * **Contoh**: `{"command": "guess", "letter": "A"}`

### **Pesan dari Server ke Client**

Server mengirimkan pembaruan status dan informasi ke client dengan struktur JSON berikut: `{"type": "tipe_pesan", "parameter": "nilai"}`

  * **`assign_id`**: Memberikan ID unik kepada client setelah berhasil terhubung.

      * **Parameter**: `id` (integer) - ID pemain (0 atau 1).
      * **Contoh**: `{"type": "assign_id", "id": 0}`

  * **`info`** atau **`error`**: Mengirimkan pesan informasi atau error untuk ditampilkan kepada pemain.

      * **Parameter**: `message` (string) - Isi pesan.
      * **Contoh**: `{"type": "info", "message": "Menunggu pemain kedua..."}`

  * **`game_update`**: Mengirimkan status permainan terkini setiap kali ada perubahan.

      * **Parameter**:
          * `display` (string): Kata yang ditampilkan dengan garis bawah (contoh: `T O Y _ T A`).
          * `guessed` (string): Kumpulan huruf yang sudah ditebak.
          * `lives` (integer): Sisa nyawa pemain.
          * `turn` (integer): ID pemain yang mendapat giliran.
          * `players_count` (integer): Jumlah pemain saat ini.
          * `clue` (string): Petunjuk kata.
      * **Contoh**: `{"type": "game_update", "display": "_ _ _ _", "guessed": "AEI", "lives": 5, "turn": 1, "players_count": 2, "clue": "Merk Mobil"}`

  * **`game_over`**: Menginformasikan bahwa permainan telah berakhir.

      * **Parameter**: `message` (string) - Pesan yang menjelaskan hasil akhir permainan.
      * **Contoh**: `{"type": "game_over", "message": "PEMAIN 0 MENANG! Kata: HONDA"}`

-----

## **Arsitektur**

### **IP Address**

  * **Server**: Menggunakan `0.0.0.0`. Ini berarti server akan mendengarkan koneksi dari semua antarmuka jaringan yang tersedia di mesin tersebut, memungkinkan client dari jaringan lokal (LAN) maupun dari luar (jika port forwarding diatur) untuk terhubung.
  * **Client**: Secara default terhubung ke `127.0.0.1` (localhost). Ini berarti client akan mencoba terhubung ke server yang berjalan di mesin yang sama. Alamat IP ini dapat diubah di dalam kode jika server berjalan di mesin yang berbeda.

### **Port TCP/IP**

  * Aplikasi menggunakan port `9999` sebagai port default untuk komunikasi TCP. Port ini dapat diubah saat menjalankan server melalui argumen command-line.

-----

## **Repository Tugas**

Repository final project kami dapat di akses di link berikut:
[https://github.com/arizki787/final\_progjar.git](https://github.com/arizki787/final_progjar.git)
