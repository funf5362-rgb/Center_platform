import streamlit as st
import json, time, qrcode
from datetime import datetime
from pathlib import Path

# ---------- إعدادات ----------
ADMIN_PASSWORD = "1234"

USERS_FILE = "users.json"
PAYMENTS_FILE = "payments.json"
RESULTS_FILE = "results.json"
ATTEND_FILE = "attendance.json"

# ---------- أدوات ----------
def load_json(file):
    if not Path(file).exists():
        return []
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def has_done_exam(student_id, lesson):
    results = load_json(RESULTS_FILE)
    return any(r for r in results if r["student_id"] == student_id and r["lesson"] == lesson)

def save_result(student_id, lesson, score):
    results = load_json(RESULTS_FILE)
    results.append({
        "student_id": student_id,
        "lesson": lesson,
        "score": score,
        "date": str(datetime.now())
    })
    save_json(RESULTS_FILE, results)

# ---------- الواجهة ----------
st.set_page_config(page_title="منصة السنتر", layout="centered")
st.title("📘 منصة السنتر الذكية")

menu = st.sidebar.selectbox(
    "القائمة",
    ["تسجيل طالب", "الدفع", "امتحان", "نتائجي", "لوحة المدرس"]
)

# ---------- تسجيل ----------
if menu == "تسجيل طالب":
    name = st.text_input("اسم الطالب")
    phone = st.text_input("رقم الطالب")
    parent = st.text_input("رقم ولي الأمر")

    if st.button("تسجيل"):
        users = load_json(USERS_FILE)
        users.append({
            "id": len(users) + 1,
            "name": name,
            "phone": phone,
            "parent": parent,
            "active": False
        })
        save_json(USERS_FILE, users)
        st.success("✅ تم التسجيل – انتظر التفعيل")

# ---------- الدفع ----------
elif menu == "الدفع":
    student_id = st.number_input("رقم الطالب", min_value=1)
    amount = st.selectbox("قيمة الاشتراك", [100, 150, 200])

    st.code("01XXXXXXXXX")
    receipt = st.file_uploader("ارفع صورة التحويل")

    if st.button("تأكيد الدفع"):
        if receipt:
            payments = load_json(PAYMENTS_FILE)
            payments.append({
                "student_id": student_id,
                "amount": amount,
                "status": "pending",
                "date": str(datetime.now())
            })
            save_json(PAYMENTS_FILE, payments)
            st.success("🕒 الدفع قيد المراجعة")
        else:
            st.error("❌ ارفع صورة التحويل")

# ---------- الامتحان ----------
elif menu == "امتحان":
    student_id = st.number_input("رقم الطالب", min_value=1)
    lesson = st.selectbox("الحصة", ["الحصة 1", "الحصة 2", "الحصة 3"])

    users = load_json(USERS_FILE)
    student = next((u for u in users if u["id"] == student_id), None)

    if not student:
        st.error("❌ الطالب غير موجود")
    elif not student["active"]:
        st.error("🚫 الحساب غير مفعل")
    elif has_done_exam(student_id, lesson):
        st.warning("⛔ تم أداء الامتحان مسبقًا")
    else:
        st.warning("🚫 ممنوع الخروج من الامتحان")

        # حضور
        attendance = load_json(ATTEND_FILE)
        attendance.append({
            "student_id": student_id,
            "lesson": lesson,
            "time": str(datetime.now())
        })
        save_json(ATTEND_FILE, attendance)

        # تايمر
        EXAM_TIME = 30
        if "start_time" not in st.session_state:
            st.session_state.start_time = time.time()

        remaining = EXAM_TIME - int(time.time() - st.session_state.start_time)

        if remaining <= 0:
            st.error("⏰ انتهى الوقت")
            st.session_state.clear()
        else:
            st.info(f"⏳ الوقت المتبقي: {remaining} ثانية")

            q1 = st.radio("2 + 2 =", [3, 4, 5])
            q2 = st.radio("5 × 2 =", [8, 10, 12])

            if st.button("تسليم"):
                score = 0
                if q1 == 4: score += 1
                if q2 == 10: score += 1

                save_result(student_id, lesson, score)
                st.success(f"🎯 درجتك {score}/2")
                st.session_state.clear()

# ---------- نتيجتي ----------
elif menu == "نتائجي":
    student_id = st.number_input("رقم الطالب", min_value=1)
    results = load_json(RESULTS_FILE)

    my = [r for r in results if r["student_id"] == student_id]

    if not my:
        st.info("لا توجد نتائج")
    else:
        for r in my:
            st.write(f"📘 {r['lesson']} — 🎯 {r['score']}")

# ---------- لوحة المدرس ----------
elif menu == "لوحة المدرس":
    pwd = st.text_input("كلمة سر المدرس", type="password")

    if pwd != ADMIN_PASSWORD:
        st.warning("🔐 غير مصرح")
    else:
        st.success("👨‍🏫 مرحبًا")

        st.subheader("💳 المدفوعات")
        payments = load_json(PAYMENTS_FILE)
        users = load_json(USERS_FILE)

        for i, p in enumerate(payments):
            if p["status"] == "pending":
                if st.button(f"تفعيل الطالب {p['student_id']}", key=i):
                    for u in users:
                        if u["id"] == p["student_id"]:
                            u["active"] = True
                    p["status"] = "approved"
                    save_json(USERS_FILE, users)
                    save_json(PAYMENTS_FILE, payments)
                    st.success("✅ تم التفعيل")

        st.subheader("📋 الحضور")
        st.json(load_json(ATTEND_FILE))

        st.subheader("📊 النتائج")
        st.json(load_json(RESULTS_FILE))

        st.subheader("📱 QR الدخول")}
        img = qrcode.make("http://localhost:8501")
        st.image(img)
