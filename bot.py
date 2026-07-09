import telebot
from telebot import types
import database
import scraper
import messages
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
    bot.send_message(message.chat.id, messages.WELCOME_TEXT, reply_markup=get_main_keyboard(user_id))

@bot.message_handler(func=lambda message: True)
def handle_menu_options(message):
    user_id = message.from_user.id
    text = message.text
    
    if text == "الاستعلام عن النتيجة":
        saved_seat = database.get_user_seat_no(user_id)
        if saved_seat:
            execute_and_send_query(message, saved_seat)
        else:
            bot.send_message(message.chat.id, messages.NO_SEAT_NO_QUERY)
            
    elif text == "الاشتراك في الإشعارات":
        if database.is_user_subscribed(message.chat.id):
            bot.send_message(message.chat.id, messages.SUBSCRIBED_ALREADY)
        else:
            saved_seat = database.get_user_seat_no(user_id)
            if saved_seat:
                database.subscribe_user(message.chat.id, saved_seat)
                bot.send_message(message.chat.id, messages.SUBSCRIBE_SUCCESS.format(seat_no=saved_seat))
            else:
                bot.send_message(message.chat.id, messages.NO_SEAT_NO_SUB)
                
    elif text == "تغيير رقم الجلوس":
        bot.send_message(message.chat.id, messages.CHANGE_SEAT_INSTRUCTION)
        
    elif text.isdigit():
        database.save_user_seat_no(user_id, text)
        if database.is_user_subscribed(message.chat.id):
            database.subscribe_user(message.chat.id, text)
        bot.send_message(message.chat.id, messages.CHANGE_SEAT_SUCCESS.format(seat_no=text), reply_markup=get_main_keyboard(user_id))
        
    elif text == "إلغاء الاشتراك":
        if database.is_user_subscribed(message.chat.id):
            database.unsubscribe_user(message.chat.id)
            bot.send_message(message.chat.id, messages.UNSUBSCRIBE_SUCCESS)
        else:
            bot.send_message(message.chat.id, messages.NOT_SUBSCRIBED)
            
    elif text == "المساعدة":
        bot.send_message(message.chat.id, messages.HELP_TEXT)
        
    elif text == "نتيجتي" and user_id == ADMIN_ID:
        saved_seat = database.get_user_seat_no(user_id)
        if saved_seat:
            execute_and_send_query(message, saved_seat)
        else:
            bot.send_message(message.chat.id, messages.ADMIN_NO_SEAT)
            
    elif text == "الإحصائيات" and user_id == ADMIN_ID:
        stats = database.get_system_stats()
        stats_msg = f"إحصائيات النظام الشاملة\n\nعدد المستخدمين:\n{stats['total_users']}\n\nعدد المشتركين:\n{stats['total_subscribers']}\n\nآخر فحص:\n{stats['last_check']}"
        bot.send_message(message.chat.id, stats_msg)
        
    elif text == "المستخدمون" and user_id == ADMIN_ID:
        subs = database.get_all_subscribers()
        if not subs:
            bot.send_message(message.chat.id, messages.NO_SUBSCRIBERS)
            return
        users_msg = f"عدد المشتركين: {len(subs)}\n\n"
        for s in subs[:50]:
            users_msg += f"{s['seat_no']}\n"
        bot.send_message(message.chat.id, users_msg)

def execute_and_send_query(message, seat_no):
    res = scraper.fetch_result_from_university(seat_no)
    if res["status"] == "site_down":
        bot.send_message(message.chat.id, messages.SITE_DOWN)
    elif res["status"] == "not_found":
        bot.send_message(message.chat.id, messages.NOT_FOUND)
    elif res["status"] == "success":
        database.save_result(seat_no, res)
        msg = f"الاسم:\n{res['name']}\n\nرقم الجلوس:\n{res['seat_no']}\n\nالمجموع:\n{res['total']} / {res['max']}\n\nالنسبة:\n{res['percentage']}%\n\nالتقدير:\n{res['estimation']}\n\nدرجات المواد\n----------------------------------------\n"
        for sub, score in res['subjects'].items():
            msg += f"{sub} .......... {score}\n"
        bot.send_message(message.chat.id, msg)

if __name__ == "__main__":
    database.init_db()
    print("Bot deployment active and listening directly...")
    bot.infinity_polling()
