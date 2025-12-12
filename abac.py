from datetime import datetime

class ABACEngine:
    @staticmethod
    def check_access(user, resource):
        # Получаем все политики из БД
        from models import Policy
        policies = Policy.query.all()
        
        # Проверяем каждую политику
        for policy in policies:
            if not ABACEngine.check_policy(policy, user, resource):
                return False
        
        return True
    
    @staticmethod
    def check_policy(policy, user, resource):
        # Получаем значение атрибута
        attr_value = None
        
        if policy.attribute == 'user.subscription_level':
            attr_value = user.subscription_level
        elif policy.attribute == 'user.account_status':
            attr_value = user.account_status
        elif policy.attribute == 'resource.access_level':
            attr_value = resource.access_level
        elif policy.attribute == 'context.time':
            attr_value = datetime.now().strftime('%H:%M')
        elif policy.attribute == 'resource.time_access':
            current_time = datetime.now().strftime('%H:%M')
            return resource.available_hours_start <= current_time <= resource.available_hours_end
        
        # Применяем оператор
        if policy.operator == 'eq':
            return attr_value == policy.value
        elif policy.operator == 'ne':
            return attr_value != policy.value
        
        return True