from datetime import datetime

class ABACEngine:
    @staticmethod
    def check_access(user, resource):
        # 1. Проверка активности аккаунта
        if user.account_status != 'active':
            return False
        
        # 2. Basic пользователь не может получать premium ресурсы
        if user.subscription_level == 'basic' and resource.access_level == 'premium':
            return False
        
        # 3. Проверка времени доступа - ФИКС сравнения времени
        if resource.available_hours_start and resource.available_hours_end:
            try:
                current_time = datetime.now().strftime('%H:%M')
                start = resource.available_hours_start
                end = resource.available_hours_end
                
                # Если время доступа круглосуточно
                if start == "00:00" and end == "23:59":
                    return True
                
                # Для нормального сравнения конвертируем в минуты
                def time_to_minutes(t):
                    h, m = map(int, t.split(':'))
                    return h * 60 + m
                
                current_minutes = time_to_minutes(current_time)
                start_minutes = time_to_minutes(start)
                end_minutes = time_to_minutes(end)
                
                # Если диапазон не пересекает полночь (09:00-18:00)
                if start_minutes <= end_minutes:
                    if not (start_minutes <= current_minutes <= end_minutes):
                        return False
                # Если диапазон пересекает полночь (22:00-06:00)
                else:
                    if not (current_minutes >= start_minutes or current_minutes <= end_minutes):
                        return False
                        
            except Exception as e:
                print(f"Ошибка проверки времени: {e}")
                # При ошибке разрешаем доступ
                return True
        
        return True