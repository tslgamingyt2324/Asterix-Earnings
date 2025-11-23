import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = os.getenv('ADMIN_ID')
    
    # Earning settings
    EARN_PER_AD = 0.02
    AD_DURATION = 30  # seconds
    
    # Withdrawal settings
    MIN_WITHDRAWAL = 1.00
    PAYMENT_METHODS = ['bkash', 'nagad', 'rocket', 'paypal']
    
    # Ad Smart Link
    AD_LINK = "https://saladattic.com/vdzzc7mhs6?key=ad6aa00be4469ae37878287b76fbb59e"
    
    # Database
    DATABASE_URL = 'sqlite:///users.db'