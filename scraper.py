import time

_cache = {}

def fetch_result_from_university(seat_no):
    current_time = time.time()
    if seat_no in _cache:
        cached_data, timestamp = _cache[seat_no]
        if current_time - timestamp < 600:
            return cached_data

    # محاكاة جلب البيانات بناءً على القواعد الرسمية لمشروعك
    if seat_no == "00000":
        return {"status": "site_down"}
    elif len(seat_no) < 4:
        return {"status": "not_found"}
        
    subjects = {
        "محاسبة مالية": 18,
        "إدارة أعمال": 15,
        "اقتصاد": 16,
        "رياضيات استثمار": 14,
        "قانون تجاري": 17
    }
    
    # حساب المجموع التلقائي بناءً على القواعد: عدد المواد × 20
    max_score = len(subjects) * 20
    total_score = sum(subjects.values())
    percentage = round((total_score / max_score) * 100, 2)
    
    result = {
        "status": "success",
        "name": "أحمد حسن محمد",
        "seat_no": seat_no,
        "subjects": subjects,
        "total": total_score,
        "max": max_score,
        "percentage": percentage,
        "estimation": "جيد جداً"
    }
    
    _cache[seat_no] = (result, current_time)
    return result
