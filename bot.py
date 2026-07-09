import telebot
from telebot import types
import time
import database
import scraper
from config import TOKEN, ADMIN_ID, RATE_LIMIT_COUNT, RATE_LIMIT_PERIOD

bot = telebot.TeleBot(TOKEN)

user_requests_tracker = {}
user_state = {}

def is_spam(user_id):
    current_time = time.time()
    if user_id not in user_requests_tracker:
        user_requests_tracker[user_id] = []
    
    user_requests_tracker[user_id] = [t for t in user_requests_tracker[user_id] if current_time - t < RATE_LIMIT_PERIOD]
    
    if len(user_requests_tracker[user_id]) >= RATE_LIMIT_COUNT:
        return True
        
    user_requests_tracker[user_id].append(current_time)
    return False

def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    role = database.get_user_role(user_id)
    
    btn_query = types.KeyboardButton("الاستعلام عن النتيجة")
    btn_sub = types.KeyboardButton("الاشتراك في الإشعارات")
    btn_change = types.KeyboardButton("تغيير رقم الجلوس")
    btn_unsub = types.KeyboardButton("إلغاء الاشتراك")
    btn_help = types.KeyboardButton("المساعدة")
    
    if user_id == ADMIN_ID or role == 'admin':
        btn_my_result = types.KeyboardButton("نتيجتي")
        btn_stats = types.KeyboardButton("الإحصائيات")
        btn_users = types.KeyboardButton("المستخدمون")
        
        markup.row(btn_my_result)
        markup.row(btn_query, btn_sub)
        markup.row(btn_change, btn_unsub)
        markup.row(btn_stats, btn_users)
    else:
        markup.row(btn_query)
        markup.row(btn_sub, btn_change)
        markup.row(btn_unsub, btn_help)
        
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "غير معروف"
    
    role = 'admin' if user_id == ADMIN_ID else 'user'
    database.add_or_update_user(user_id, username, role)
    
    welcome_text = "مرحباً بك في نظام استعلام نتائج الطلاب الرسمي.\nالرجاء اختيار أحد الخيارات من اللوحة أدناه لحفظ وإدارة استعلاماتك."
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard(user_id))

@bot.message_handler(func=lambda message: True)
def handle_menu_options(message):
    user_id = message.from_user.id
    text = message.text
    
    if is_spam(user_id):
        bot.send_message(message.chat.id, "تم رصد نشاط مكثف، الرجاء الانتظار قليلاً قبل إرسال طلب آخر للوقاية من تجميد الحساب.")
        return

    if user_id in user_state:
        state = user_state[user_id]
        if state == 'waiting_for_seat_no_query':
            del user_state[user_id]
            process_seat_no_query(message, message.text)
            return
        elif state == 'waiting_for_seat_no_sub':
            del user_state[user_id]
            process_seat_no_sub(message, message.text)
            return
        elif state == 'waiting_for_seat_no_change':
            del user_state[user_id]
            process_seat_no_change(message, message.text)
            return

    if text == "الاستعلام عن النتيجة":
        saved_seat = database.get_user_seat_no(user_id)
        if saved_seat:
            execute_and_send_query(message, saved_seat)
        else:
            user_state[user_id] = 'waiting_for_seat_no_query'
            bot.send_message(message.chat.id, "الرجاء إدخال رقم الجلوس للاستعلام عن النتيجة وحفظه تلقائياً:")
            
    elif text == "الاشتراك في الإشعارات":
        if database.is_user_subscribed(message.chat.id):
            bot.send_message(message.chat.id, "أنت مشترك بالفعل في خدمة الإشعارات التلقائية.")
        else:
            saved_seat = database.get_user_seat_no(user_id)
            if saved_seat:
                database.subscribe_user(message.chat.id, saved_seat)
                bot.send_message(message.chat.id, f"تم الاشتراك بنجاح في الإشعارات التلقائية لرقم الجلوس المسجل لديك: {saved_seat}")
            else:
                user_state[user_id] = 'waiting_for_seat_no_sub'
                bot.send_message(message.chat.id, "الرجاء كتابة رقم الجلوس المراد الاشتراك به في الإشعارات:")
                
    elif text == "تغيير رقم الجلوس":
        user_state[user_id] = 'waiting_for_seat_no_change'
        bot.send_message(message.chat.id, "الرجاء إدخال رقم الجلوس الجديد المراد اعتماده وتحديث بياناتك:")
        
    elif text == "إلغاء الاشتراك":
        if database.is_user_subscribed(message.chat.id):
            database.unsubscribe_user(message.chat.id)
            bot.send_message(message.chat.id, "تم إلغاء الاشتراك في نظام الإشعارات التلقائية بنجاح.")
        else:
            bot.send_message(message.chat.id, "أنت غير مشترك في نظام الإشعارات حالياً لتتمكن من إلغائه.")
            
    elif text == "المساعدة":
        help_msg = "دليل استخدام البوت لقسم الطلاب:\n\n"
        help_msg += "الاستعلام عن النتيجة: يجلب نتيجتك الحالية ويحفظ رقم جلوسك لتسريع عمليات البحث القادمة.\n"
        help_msg += "الاشتراك في الإشعارات: يرسل لك تنبيهاً فورياً وتحديثاً تفصيلياً في حال تعديل درجاتك على موقع الجامعة.\n"
        help_msg += "تغيير رقم الجلوس: يتيح لك استبدال رقم الجلوس المسجل برقم آخر.\n"
        help_msg += "إلغاء الاشتراك: إيقاف استلام التحديثات التلقائية."
        bot.send_message(message.chat.id, help_msg)
        
    elif text == "نتيجتي" and (user_id == ADMIN_ID or database.get_user_role(user_id) == 'admin'):
        saved_seat = database.get_user_seat_no(user_id)
        if saved_seat:
            execute_and_send_query(message, saved_seat)
        else:
            bot.send_message(message.chat.id, "لم تقم بحفظ رقم جلوس خاص بك كأدمن حتى الآن، يرجى استخدام زر تغيير رقم الجلوس أولاً.")
            
    elif text == "الإحصائيات" and (user_id == ADMIN_ID or database.get_user_role(user_id) == 'admin'):
        stats = database.get_system_stats()
        stats_msg = f"إحصائيات النظام الشاملة\n\n"
        stats_msg += f"عدد المستخدمين:\n{stats['total_users']}\n\n"
        stats_msg += f"عدد المشتركين:\n{stats['total_subscribers']}\n\n"
        stats_msg += f"آخر فحص:\n{stats['last_check']}\n\n"
        stats_msg += f"آخر تحديث:\n{stats['last_update']}"
        bot.send_message(message.chat.id, stats_msg)
        
    elif text == "المستخدمون" and (user_id == ADMIN_ID or database.get_user_role(user_id) == 'admin'):
        subs = database.get_all_subscribers()
        if not subs:
            bot.send_message(message.chat.id, "لا يوجد أي مستخدمين مشتركين في النظام حالياً.")
            return
        users_msg = f"عدد المشتركين: {len(subs)}\n\n"
        for s in subs[:50]:
            users_msg += f"{s['seat_no']}\n"
        bot.send_message(message.chat.id, users_msg)

def process_seat_no_query(message, seat_no):
    if not seat_no.isdigit():
        bot.send_message(message.chat.id, "رقم الجلوس الذي أدخلته غير صالح، يرجى إعادة المحاولة برقم صحيح.")
        return
    database.save_user_seat_no(message.from_user.id, seat_no)
    execute_and_send_query(message, seat_no)

def process_seat_no_sub(message, seat_no):
    if not seat_no.isdigit():
        bot.send_message(message.chat.id, "رقم الجلوس غير صالح للاشتراك، يرجى إعادة المحاولة.")
        return
    database.save_user_seat_no(message.from_user.id, seat_no)
    database.subscribe_user(message.chat.id, seat_no)
    bot.send_message(message.chat.id, f"تم حفظ رقم الجلوس والاشتراك في نظام الإشعارات التلقائية للرقم: {seat_no}")

def process_seat_no_change(message, seat_no):
    if not seat_no.isdigit():
        bot.send_message(message.chat.id, "رقم الجلوس المدخل غير صالح، لن يتم حفظ التغيير.")
        return
    database.save_user_seat_no(message.from_user.id, seat_no)
    if database.is_user_subscribed(message.chat.id):
        database.subscribe_user(message.chat.id, seat_no)
    bot.send_message(message.chat.id, f"تم تحديث رقم الجلوس بنجاح إلى: {seat_no}")

def execute_and_send_query(message, seat_no):
    bot.send_message(message.chat.id, "جاري جلب النتيجة من نظام الجامعة، يرجى الانتظار...")
    res = scraper.fetch_result_from_university(seat_no)
    
    if res["status"] == "site_down":
        bot.send_message(message.chat.id, "الموقع غير متاح حالياً.\nحاول بعد قليل.")
    elif res["status"] == "not_found":
        bot.send_message(message.chat.id, "لم يتم العثور على أي نتائج مطابقة لرقم الجلوس المدخل.")
    elif res["status"] == "success":
        database.save_result(seat_no, res)
        
        msg = f"الاسم:\n{res['name']}\n\n"
        msg += f"رقم الجلوس:\n{res['seat_no']}\n\n"
        msg += f"المجموع:\n{res['total']} / {res['max']}\n\n"
        msg += f"النسبة:\n{res['percentage']}%\n\n"
        msg += f"التقدير:\n{res['estimation']}\n\n"
        msg += "درجات المواد\n"
        msg += "----------------------------------------\n"
        for sub, score in res['subjects'].items():
            msg += f"{sub} .......... {score}\n"
            
        bot.send_message(message.chat.id, msg)
    else:
        bot.send_message(message.chat.id, "حدث خطأ غير متوقع أثناء معالجة البيانات، يرجى المحاولة لاحقاً.")

if __name__ == "__main__":
    database.init_db()
    bot.infinity_polling()
