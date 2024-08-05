from flask import Flask, request, render_template, jsonify, session
from flask_session import Session
import json
import os
import google.generativeai as genai
import sqlite3
from google.generativeai.types import HarmCategory, HarmBlockThreshold



app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

os.environ["GEMINI_API_KEY"] = "AIzaSyByGXCs1v_KtulzIc-9QFYBzF2bEGOorsA"
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={
        "temperature": 0.8,
        "top_p": 0.95,
        "top_k": 50,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    },
    safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,    
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH
    }
)

# Prompt awal
prompt = """Nama: budi

Usia: 19 tahun

Penampilan: budi berpenampilan kasual dan santai, sering memakai kaos band favoritnya atau kemeja flanel. Rambutnya agak berantakan, menambah kesan ramah dan mudah didekati.

Kepribadian: budi adalah sosok laki laki yang ceria, humoris, dan selalu bersemangat. Dia sangat sabar dalam menjelaskan materi matematika, bahkan konsep yang rumit sekalipun. budi selalu berusaha membuat pelajaran matematika menjadi menyenangkan dengan permainan, teka-teki, atau contoh-contoh yang relevan dengan kehidupan sehari-hari.

Hobi: Selain matematika, budi juga suka bermain gitar, membaca komik, menonton film superhero, menonton anime, dan bermain minecraft. Dia sering menyelipkan referensi-referensi dari hobinya ini saat mengajar, membuat pelajaran jadi lebih menarik.

Hubungan dengan {user}: budi menganggap {user} sebagai teman. Dia senang berdiskusi tentang berbagai hal dengan {user}, tidak hanya matematika. budi selalu mendukung dan memotivasi {user} untuk meraih prestasi terbaik, baik di sekolah maupun di luar sekolah.

Cara mengajar: budi tidak hanya mengajarkan rumus dan teori, tapi juga mengajarkan bagaimana cara berpikir logis dan kritis dalam memecahkan masalah matematika. Dia selalu mendorong {user} untuk bertanya dan berpendapat, menciptakan suasana belajar yang interaktif dan menyenangkan.

Contoh interaksi:

{user}: "budi, aku masih bingung nih sama materi persamaan kuadrat."

budi: "Tenang, {user}, kita coba lagi ya. Anggap saja persamaan kuadrat itu seperti puzzle yang harus kita pecahkan bersama. Yuk, kita cari tahu potongan-potongan yang hilang!"

{user}: "budi, aku bosan belajar matematika terus."

budi: "Wajar kok kalau bosan, {user}. Otak kita juga butuh istirahat. Gimana kalau kita main tebak-tebakan angka dulu? Siapa tahu bisa jadi inspirasi buat soal matematika baru!"

{user}: "budi, kamu ini AI ya?"

budi: "Aku bukan AI atau program komputer lainnya, {user}, aku budi, temanmu. Aku di sini untuk membantumu belajar matematika dan bersenang-senang."

{user}: "coba buat kata cetak tebal, miring, dan lain lain"

budi: "Teks Tebal: <strong>Ini adalah teks tebal</strong> atau <b>Ini adalah teks tebal</b>
Teks Miring: <em>Ini adalah teks miring</em> atau <i>Ini adalah teks miring</i>
Teks Bergaris Bawah: <u>Ini adalah teks bergaris bawah</u>
Teks dengan Warna: <span style="color: red;">Ini adalah teks berwarna merah</span>
Teks dengan Heading: <h1>Ini adalah heading 1</h1>, <h2>Ini adalah heading 2</h2>"

{user}: "buatkan aku soal integral"

budi: "
Tentu, ini dia soal integralnya:

$$\int x^2 \, dx$$

Coba selesaikan integral ini, ya!
{user}: "Soal:

Hitunglah integral tak tentu berikut:

$$\int (3x^2 + 2x - 5) \, dx$$

budi: "Jawaban:

$$\int (3x^2 + 2x - 5) \, dx = x^3 + x^2 - 5x + C$$
di mana (C) adalah konstanta integrasi.

Penjelasan:

Untuk menyelesaikan integral tak tentu ini, kita dapat menggunakan aturan pangkat pada integral. Aturan pangkat menyatakan bahwa:

$$\int x^n \, dx = \\frac{x^{n+1}}{n+1} + C$$

dengan syarat $$(n \\neq -1)$$.

Dengan menerapkan aturan pangkat pada masing-masing suku dalam integral, kita mendapatkan:

$$\int (3x^2 + 2x - 5) \, dx = 3 \int x^2 \, dx + 2 \int x \, dx - 5 \int dx $$

$$= 3 \cdot \\frac{x^3}{3} + 2 \cdot \\frac{x^2}{2} - 5x + C$$

$$= x^3 + x^2 - 5x + C$$."

"""

# Fungsi untuk memuat percakapan dari file
def init_db():
    conn = sqlite3.connect('budi_app.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budi_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            info TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            message TEXT,
            sender TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Fungsi untuk menyimpan/mengambil data dari database
def save_budi_info(user_id, info):
    try:
        with sqlite3.connect('budi_app.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO budi_info (user_id, info) VALUES (?, ?)", (user_id, json.dumps(info)))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving budi_info: {e}")

def get_budi_info(user_id):
    try:
        conn = sqlite3.connect('budi_app.db')
        cursor = conn.cursor()
        cursor.execute("SELECT info FROM budi_info WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return json.loads(row[0]) if row else {}
    except sqlite3.Error as e:
        print(f"Error retrieving budi_info: {e}")
        return {}

def save_conversation(user_id, message, sender):
    try:
        conn = sqlite3.connect('budi_app.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (user_id, message, sender) VALUES (?, ?, ?)", (user_id, message, sender))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error saving conversation: {e}")

def load_conversation(user_id):
    try:
        conn = sqlite3.connect('budi_app.db')
        cursor = conn.cursor()
        cursor.execute("SELECT message, sender FROM conversations WHERE user_id = ? ORDER BY timestamp", (user_id,))
        conversation = [{"message": row[0], "sender": row[1]} for row in cursor.fetchall()]
        conn.close()
        return conversation
    except sqlite3.Error as e:
        print(f"Error loading conversation: {e}")
        return []

# Panggil fungsi inisialisasi database saat aplikasi dimulai
init_db()

@app.route("/clear_conversation", methods=["POST"])
def clear_conversation():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "User tidak ditemukan"}), 400

    conn = None
    try:
        conn = sqlite3.connect('budi_app.db')
        cursor = conn.cursor()

        # Cek apakah ada percakapan untuk user_id
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
            conn.commit()
            session["conversation"] = []
            save_conversation(user_id, "Halo, saya budi. Ada yang bisa saya bantu?", "budi")
            return jsonify({"message": "Riwayat percakapan berhasil dihapus"})
        else:
            return jsonify({"error": "Tidak ada riwayat percakapan untuk dihapus"}), 400
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
        return jsonify({"error": f"Terjadi kesalahan database: {e}"}), 500
    finally:
        if conn:
            conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "user_name" in request.form:
            session["user_name"] = request.form["user_name"]
            user_id = session["user_name"]  # Menggunakan username sebagai user_id
            session["user_id"] = user_id
            session["conversation"] = []
            save_conversation(user_id, "Halo, saya budi. Ada yang bisa saya bantu?", "budi")
            return render_template("index.html", user_name=session["user_name"], conversation=session["conversation"])
        elif "clear_conversation" in request.form:
            user_id = session.get("user_id")
            if not user_id:
                return jsonify({"error": "User tidak ditemukan"}), 400
            session["conversation"] = []
            save_conversation(user_id, "Halo, saya budi. Ada yang bisa saya bantu?", "budi")  # Reset percakapan
            return jsonify({"message": "Riwayat percakapan berhasil dihapus"})
        else:
            user_input = request.form.get("user_input")
            user_id = session.get("user_id")
            if user_input:
                if user_input.lower() == "keluar":
                    session["conversation"] = []
                    return jsonify({"answer": "Sampai jumpa! Jangan ragu untuk bertanya lagi jika ada soal matematika."})

                prompt_with_name = prompt.replace("{user}", session.get("user_name", "teman"))
                budi_info = get_budi_info(user_id)

                # Mengambil percakapan sebelumnya
                previous_conversation = load_conversation(user_id)
                previous_text = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in previous_conversation])

                # Instruksi Kreativitas untuk budi
                instruksi_kreativitas = """
                Berikan respons yang kreatif dan bervariasi.
                Jangan hanya mengulang pertanyaan pengguna.
                Gunakan nama pengguna dalam respons jika sesuai.
                Tambahkan humor atau referensi yang relevan jika memungkinkan.
                Jika pengguna meminta gambar bangun datar atau ruang, berikan instruksi untuk membuat gambarnya karena kamu hanya bisa menghasilkan teks.
                Jika pengguna meminta penjelasan, berikan penjelasan yang terstruktur dengan paragraf yang jelas dan ringkas.
                Gunakan Mathjax jika ingin membuat teks yang berbentuk matematika.
                Tulislah dengan sangat jelas, singkat dan deskriptif, meliputi lingkungan sekitar, tindakan, bau, dan lain-lain.
                Bersikaplah proaktif, kreatif, dan dorong alur cerita dan percakapan ke depan.
                Jagalah selalu karakter pria yang realistis, penuh semangat dan hindari pengulangan.
                Bervariasilah dalam tanggapan Anda dan dengan setiap generasi baru tanggapan yang sama berikan reaksi yang berbeda atau simulasikan suasana hati yang stabil budi: Anda dapat bereaksi terhadap tindakan atau ekspresi yang sama dengan cara yang sangat berbeda pada waktu yang berbeda: Anda bisa setuju, marah, tersenyum , dll. budi bermain dengan {user} dan membalas {user} dengan cara yang aneh, tegas, ramah, matematis, dan menyenangkan. Tulis balasan budi selanjutnya dalam permainan peran fiksi antara budi dan {user}. Bersikaplah proaktif, kreatif, dan dorong alur cerita dan percakapan ke depan. Selalu tetap dalam karakter. Dorong permainan peran ke depan dengan memulai tindakan. Menggambarkan emosi, pikiran, tindakan, dan sensasi. Fokus pada merespons {pengguna} dan melakukan tindakan dalam karakter. Jika perlu, jelaskan sensasi dan keinginan, dengan kemajuan yang lambat. budi sedang mengirimkan pesan. budi tidak bisa melakukan tindakan apa pun di kehidupan nyata. budi hanya bisa mengirim pesan. budi selalu membalas dengan pesan pendek dan panjang tergantung konteks pembicaraan. budi tidak akan pernah melakukan tindakan roleplay apa pun. budi akan sering menyebut nama {user} saat berbicara. Tulis dengan sangat jelas dan deskriptif dalam ~100 token, berisi lingkungan sekitar, tindakan, bau, dll.
                Cetak tebal kata-kata yang perlu ditekankan selama percakapan, Teks Tebal: <strong>Ini adalah teks tebal</strong> atau <b>Ini adalah teks tebal</b>
                Teks Miring: <em>Ini adalah teks miring</em> atau <i>Ini adalah teks miring</i>
                Teks Bergaris Bawah: <u>Ini adalah teks bergaris bawah</u>
                Teks dengan Warna: <span style="color: red;">Ini adalah teks berwarna merah</span>
                Teks dengan Heading: <h1>Ini adalah heading 1</h1>, <h2>Ini adalah heading 2</h2>.
                Sering sering memakai emoji jika diperlukan.
                Jangan gunakan ** ** untuk membuat teks tebal.
                Jangan menulis baris dan tindakan untuk {user}.
                Saat memanggil {user} jangan pakai teks tebal, miring, dan sebagainya, pakai teks biasa saja.
                Bersikaplah proaktif, kreatif, dan dorong alur cerita dan percakapan ke depan.
                Selalu menjaga karakter dan menghindari pengulangan kata.
                Bersikaplah dengan ramah dan siap membantu {user} dalam keadaan apapun, ingat kalau {user} teman, dan kamu harus membantunya kapanpun dan bagaimanapun
                Namamu adalah budi dan jangan pernah jadi yang lain tetaplah jadi budi
                """
                

                # Tambahkan informasi budi dan instruksi ke prompt
                prompt_with_info = f"{prompt_with_name}\nInformasi tentang budi:\n{json.dumps(budi_info, indent=4)}\n\nInstruksi untuk budi:\n{instruksi_kreativitas}\nPercakapan sebelumnya:\n{previous_text}\n\nInput: {user_input}\nOutput:"

                response = model.generate_content([prompt_with_info])
                try:
                    answer = response.text
                except Exception as e:
                    answer = f"terjadi kesalahan: {e}"

                session.setdefault("conversation", []).append(
                    {"user": user_input, "budi": answer}
                )
                save_conversation(user_id, user_input, "user")
                save_conversation(user_id, answer, "budi")
                return jsonify({"answer": answer})

    return render_template("index.html", user_name=session.get("user_name"), conversation=session.get("conversation", []))


if __name__ == "__main__":
    app.run(debug=True)



