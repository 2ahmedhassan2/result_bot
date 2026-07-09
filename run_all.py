import os
import telebot
from telebot import types
import time
import database
import scraper
from config import TOKEN, ADMIN_ID

bot = telebot.TeleBot(TOKEN)

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
    
    welcome_text = "مرحباً بك في نظام استعلام نتائج الطلاب الرسمي.\nالرجاء اختيار أحد الخيارات من اللوحة أدناه لإدارة استعلاماتك."
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard(user_id))

@bot.message_handler(func=lambda message: True)
def handle_menu_options(message):
    user_id = message.from_user.id
    text = message.text
    
    if text == "الاستعلام عن النتيجة":
        saved_seat = database.get_user_seat_no(user_id)
        if saved_seat:
            execute_and_send_query(message, saved_seat)
        else:
            bot.send_message(message.chat.id, "لم تقم بحفظ رقم جلوسك. يرجى إرسال رقم الجلوس مباشرة في المحادثة لتسجيله.")
            
    elif text == "الاشتراك في الإشعارات":
        if database.is_user_subscribed(message.chat.id):
            bot.send_message(message.chat.id, "أنت مشترك بالفعل في خدمة الإشعارات التلقائية.")
        else:
            saved_seat = database.get_user_seat_no(user_id)
            if saved_seat:
                database.subscribe_user(message.chat.id, saved_seat)
                bot.send_message(message.chat.id, f"تم الاشتراك بنجاح في الإشعارات للرقم المسجل: {saved_seat}")
            else:
                bot.send_message(message.chat.id, "الرجاء تسجيل رقم جلوسك أولاً بإرساله في رسالة نصية لتتمكن من الاشتراك.")
                
    elif text == "تغيير رقم الجلوس":
        bot.send_message(message.chat.id, "لتغيير أو تسجيل رقم الجلوس، يرجى إرسال الرقم في رسالة تحتوي على أرقام فقط.")
        
    elif text.isdigit():
        database.save_user_seat_no(user_id, text)
        if database.is_user_subscribed(message.chat.id):
            database.subscribe_user(message.chat.id, text)
        bot.send_message(message.chat.id, f"تم اعتماد وتحديث رقم الجلوس الخاص بك إلى: {text}", reply_markup=get_main_keyboard(user_id))
        
    elif text == "إلغاء الاشتراك":
        if database.is_user_subscribed(message.chat.id):
            database.unsubscribe_user(message.chat.id)
            bot.send_message(message.chat.id, "تم إلغاء الاشتراك في نظام الإشعارات بنجاح.")
        else:
            bot.send_message(message.chat.id, "أنت غير مشترك في النظام حالياً.")
            
    elif text == "المساعدة":
        help_msg = "دليل الاستخدام:\n\nاكتب رقم جلوسك مباشرة في المحادثة لحفظه وتحديثه.\nاضغط على الاستعلام للبحث الفوري.\nاشترك لاستقبل التنبيهات تلقائياً عند تحديث النتيجة."
        bot.send_message(message.chat.id, help_msg)
        
    elif text == "نتيجتي" and user_id == ADMIN_ID:
        saved_seat = database.get_user_seat_no(user_id)
        if saved_seat:
            execute_and_send_query(message, saved_seat)
        else:
            bot.send_message(message.chat.id, "لم تقم بحفظ رقم جلوس خاص بك كأدمن بعد.")
            
    elif text == "الإحصائيات" and user_id == ADMIN_ID:
        stats = database.get_system_stats()
        stats_msg = f"إحصائيات النظام الشاملة\n\nعدد المستخدمين:\n{stats['total_users']}\n\nعدد المشتركين:\n{stats['total_subscribers']}\n\nآخر فحص:\n{stats['last_check']}"
        bot.send_message(message.chat.id, stats_msg)
        
    elif text == "المستخدمون" and user_id == ADMIN_ID:
        subs = database.get_all_subscribers()
        if not subs:
            bot.send_message(message.chat.id, "لا يوجد أي مشتركين حالياً.")
            return
        users_msg = f"عدد المشتركين: {len(subs)}\n\n"
        for s in subs[:50]:
            users_msg += f"{s['seat_no']}\n"
        bot.send_message(message.chat.id, users_msg)

def execute_and_send_query(message, seat_no):
    res = scraper.fetch_result_from_university(seat_no)
    if res["status"] == "site_down":
        bot.send_message(message.chat.id, "الموقع غير متاح حالياً. حاول بعد قليل.")
    elif res["status"] == "not_found":
        bot.send_message(message.chat.id, "لم يتم العثور على أي نتائج مطابقة لرقم الجلوس.")
    elif res["status"] == "success":
        database.save_result(seat_no, res)
        msg = f"الاسم:\n{res['name']}\n\nرقم الجلوس:\n{res['seat_no']}\n\nالمجموع:\n{res['total']} / {res['max']}\n\nالنسبة:\n{res['percentage']}%\n\nالتقدير:\n{res['estimation']}\n\nدرجات المواد\n----------------------------------------\n"
        for sub, score in res['subjects'].items():
            msg += f"{sub} .......... {score}\n"
        bot.send_message(message.chat.id, msg)

def run_background_result_checker():
    subscribers = database.get_all_subscribers()
    if not subscribers:
        database.log_check_operation("success", "لا يوجد مشتركون حالياً.")
        return

    for sub in subscribers:
        chat_id = sub['chat_id']
        seat_no = sub['seat_no']
        
        new_result = scraper.fetch_result_from_university(seat_no)
        if not new_result or new_result.get("status") != "success":
            continue
            
        old_result = database.get_saved_result(seat_no)
        if old_result is None:
            database.save_result(seat_no, new_result)
            continue
            
        if old_result['total'] != new_result['total'] or old_result['subjects'] != new_result['subjects']:
            changed_subjects_text = ""
            for sub_name, new_score in new_result['subjects'].items():
                old_score = old_result['subjects'].get(sub_name, 0)
                if old_score != new_score:
                    changed_subjects_text += f"{sub_name}:\n{old_score} ← {new_score}\n\n"
            
            notification = "تم تحديث النتيجة.\n\n"
            notification += f"الاسم:\n{new_result['name']}\n\nالمجموع الحالي:\n{new_result['total']} / {new_result['max']}\n\nالنسبة:\n{new_result['percentage']}%\n\n"
            if changed_subjects_text:
                notification += "المواد المتغيرة:\n\n" + changed_subjects_text
            
            try:
                bot.send_message(chat_id, notification)
                database.save_result(seat_no, new_result)
            except Exception:
                pass
                
    database.log_check_operation("success", f"تم فحص عدد {len(subscribers)} مشتركين.")

if __name__ == "__main__":
    database.init_db()
    
    # فحص الرسائل الواردة بشكل متتابع ومعالجتها فوراً
    updates = bot.get_updates(timeout=5, allowed_updates=["message"])
    if updates:
        bot.process_new_updates(updates)
    
    # تشغيل الفحص الدوري على المشتركين
    run_background_result_checker()
