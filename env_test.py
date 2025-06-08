import os
from dotenv import load_dotenv

# Друк абсолютного шляху до .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(">>> Очікуваний шлях до .env:", env_path)

# Завантаження .env
load_dotenv(dotenv_path=env_path)

# Читання змінних
bot_token = os.getenv("7784019887:AAED0R6gwR3bNdQ8aYy1NFcoGi1VBaZKlEk")
seller_id = os.getenv("1227954847")

print(">>> BOT_TOKEN =", bot_token)
print(">>> SELLER_ID =", seller_id)