import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    ADMIN_ID = os.getenv('ADMIN_ID', 'YOUR_ADMIN_ID_HERE')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://your-app-name.onrender.com')
    PORT = int(os.getenv('PORT', 10000))
    
    # Earning settings
    EARN_PER_AD = 0.02
    AD_DURATION = 30
    
    # Withdrawal settings
    MIN_WITHDRAWAL = 1.00
    PAYMENT_METHODS = ['bkash', 'nagad', 'rocket', 'paypal']
    
    # Ad Smart Link
    AD_LINK = "https://saladattic.com/vdzzc7mhs6?key=ad6aa00be4469ae37878287b76fbb59e"
    
    # Database
    DATABASE_URL = 'sqlite:///users.db'
