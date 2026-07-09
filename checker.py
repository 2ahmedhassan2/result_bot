import time
import telebot
import database
import scraper
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

def run_background_result_checker():
    subscribers = database.get_all_subscribers()
    if not subscribers:
        database.log_check_operation("success", "لا يوجد مشتركون حالياً لطلب فحصهم.")
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
                notification += "المواد التي تغيرت:\n\n" + changed_subjects_text
            
            try:
                bot.send_message(chat_id, notification)
                database.save_result(seat_no, new_result)
            except Exception:
                pass
                
    database.log_check_operation("success", f"تم فحص عدد {len(subscribers)} مشتركين بنجاح.")

if __name__ == "__main__":
    database.init_db()
    print("بدء خدمة الفحص الدوري التلقائي (كل دقيقة) على PythonAnywhere...")
    
    while True:
        try:
            run_background_result_checker()
        except Exception as e:
            print(f"حدث خطأ أثناء الفحص الدوري: {e}")
        
        # النوم لمدة 60 ثانية (دقيقة واحدة) قبل الفحص التالي
        time.sleep(60)
