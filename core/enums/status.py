from enum import Enum

class TaskStatus(Enum):
	NEW = "new" # Задача создана, но не начата
	IN_PROGRESS = "in_progress" # Задача в процессе выполнения
	REVIEW = "review" # Задача проверена, но не принята
	COMPLETED = "completed" # Задача выполнена
	FAILED = "failed" # Задача не выполнена
	CANCELLED = "cancelled" # Задача отменена

class TaskPriority(Enum):
	LOW = "low" # Низкий приоритет
	MEDIUM = "medium" # Средний приоритет
	HIGH = "high" # Высокий приоритет
	URGENT = "urgent" # Срочный приоритет

class Role(Enum):
	OWNER = "owner" # Владелец
	ADMIN = "admin" # Администратор
	WORKER = "worker" # Работник
	USER = "user" # Пользователь