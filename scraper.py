import requests
import time

_cache = {}

def fetch_result_from_university(seat_no):
    current_time = time.time()
    
    if seat_no in _cache:
        data, timestamp = _cache[seat_no]
        if current_time - timestamp < 600:
            return data

    # رابط وهمي كمثال - قم باستبداله برابط المنظومة الحقيقي
    url = f"https://example-university-portal.edu/api/results/{seat_no}"
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            raw_data = response.json()
            processed_data = process_raw_result(raw_data)
            _cache[seat_no] = (processed_data, current_time)
            return processed_data
        elif response.status_code == 404:
            return {"status": "not_found"}
        else:
            return {"status": "site_down"}
    except (requests.exceptions.RequestException, ValueError):
        return {"status": "site_down"}

def process_raw_result(raw_data):
    student_name = raw_data.get("name", "غير معروف")
    seat_no = raw_data.get("seat_no")
    subjects = raw_data.get("subjects", {})
    
    num_subjects = len(subjects)
    if num_subjects == 0:
        return {"status": "invalid_data"}
        
    total_score = sum(subjects.values())
    max_score = num_subjects * 20
    percentage = (total_score / max_score) * 100
    
    if percentage >= 85:
        estimation = "امتياز"
    elif percentage >= 75:
        estimation = "جيد جداً"
    elif percentage >= 65:
        estimation = "جيد"
    elif percentage >= 50:
        estimation = "مقبول"
    else:
        estimation = "ضعيف"
        
    return {
        "status": "success",
        "name": student_name,
        "seat_no": seat_no,
        "total": total_score,
        "max": max_score,
        "percentage": round(percentage, 2),
        "estimation": estimation,
        "subjects": subjects
    }
