import streamlit as st
import sqlite3
import os
from google import genai

# --- Langkah 1: Title ---

st.title("👨‍💻 IT Support Chatbot")
st.caption("Silahkan pilih pertanyaan dari sidebar")

# --- Langkah 2: Fungsi Database SQLite ---
def init_db():
    """Menginisialisasi database SQLite dan mengisi data awal."""
    try:
        conn = sqlite3.connect('data/it_support_kb.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS it_knowledge (
                id INTEGER PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL
            )
        ''')
        
        # Tambahkan data jika tabel masih kosong
        c.execute("SELECT count(*) FROM it_knowledge")
        if c.fetchone()[0] == 0:
            knowledge_base = [
                ("Apa itu IP Address?", "IP Address adalah alamat unik yang mengidentifikasi sebuah perangkat di jaringan, baik lokal maupun internet. Contoh: 192.168.1.1"),
                ("Bagaimana cara restart router?", "1. Cabut kabel power router. 2. Tunggu 30 detik. 3. Colokkan kembali kabel power dan tunggu hingga semua lampu indikator menyala stabil."),
                ("Apa itu VPN?", "VPN (Virtual Private Network) adalah teknologi yang menciptakan koneksi aman dan terenkripsi di atas jaringan yang tidak aman, seperti internet."),
                ("Bagaimana cara memperbaiki koneksi Wi-Fi yang lambat?", "1. Restart router dan perangkat Anda. 2. Posisikan router di tempat terbuka. 3. Ganti saluran Wi-Fi (Wi-Fi channel) di pengaturan router.")
            ]
            c.executemany("INSERT INTO it_knowledge (question, answer) VALUES (?, ?)", knowledge_base)
            conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

# Pastikan folder 'data' ada
if not os.path.exists('data'):
    os.makedirs('data')

# Panggil fungsi inisialisasi database
init_db()

# --- Langkah 3: Tampilan dan Logika Chatbot ---
# Inisialisasi riwayat chat di session state Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tampilkan riwayat chat yang ada
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Tampilkan pilihan menu di sidebar dari database
st.sidebar.subheader("Pilihan Pengetahuan IT Support")
try:
    conn = sqlite3.connect('data/it_support_kb.db')
    c = conn.cursor()
    c.execute("SELECT question FROM it_knowledge")
    questions = c.fetchall()
    conn.close()

    for q in questions:
        if st.sidebar.button(q[0]):
            st.session_state.messages.append({"role": "user", "content": q[0]})
            with st.chat_message("assistant"):
                conn = sqlite3.connect('data/it_support_kb.db')
                c = conn.cursor()
                c.execute("SELECT answer FROM it_knowledge WHERE question=?", (q[0],))
                answer = c.fetchone()[0]
                conn.close()
                st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
except sqlite3.Error as e:
    st.error(f"Error accessing database from sidebar: {e}")

# Tangani input dari pengguna
if prompt := st.chat_input("Tanyakan sesuatu tentang IT Support..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Cek di database
        response = None
        try:
            conn = sqlite3.connect('data/it_support_kb.db')
            c = conn.cursor()
            c.execute("SELECT answer FROM it_knowledge WHERE question LIKE ?", (f"%{prompt.strip()}%",))
            db_answer = c.fetchone()
            conn.close()
            
            if db_answer:
                response = db_answer[0]
                st.markdown(response)
            else:
                # Jika tidak ada di database, gunakan Gemini AI
                model = genai.GenerativeModel('gemini-2.5-flash')
                response_gemini = model.generate_content(f"Kamu adalah chatbot IT Support. Jawab pertanyaan berikut dengan singkat dan jelas: {prompt}")
                response = response_gemini.text
                st.markdown(response)
        except Exception as e:
            st.markdown(f"Maaf, terjadi kesalahan: {e}")
            response = f"Maaf, terjadi kesalahan: {e}"

    st.session_state.messages.append({"role": "assistant", "content": response})
