from flask import Flask, request
import asyncio
from threading import Thread
import logging
from main import bot
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Asterix Earnings Bot</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .status { color: green; font-size: 24px; margin-bottom: 20px; }
            .info { color: #666; margin-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="status">🤖 Asterix Earnings Bot is Running!</div>
        <div class="info">Your Telegram bot is ready to use.</div>
        <div class="info"><a href="/set_webhook">Set Webhook</a> | <a href="/health">Health Check</a></div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return "✅ Bot is healthy and running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Process the update
        update = request.get_json()
        if update:
            # Use run_coroutine_threadsafe for async processing
            future = asyncio.run_coroutine_threadsafe(
                bot.application.process_update(update), 
                bot.application._get_running_loop()
            )
            future.result(timeout=10)  # Wait for processing
        return 'ok'
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'error', 400

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    try:
        webhook_url = f"{Config.WEBHOOK_URL}/webhook"
        success = bot.application.bot.set_webhook(webhook_url)
        if success:
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Webhook Setup</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .success {{ color: green; font-size: 20px; }}
                    .url {{ color: blue; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="success">✅ Webhook Setup Successful!</div>
                <div class="url">Webhook URL: {webhook_url}</div>
                <div>Your bot is now ready to receive messages.</div>
            </body>
            </html>
            """
        else:
            return "❌ Webhook setup failed"
    except Exception as e:
        return f"❌ Error setting webhook: {e}"

@app.route('/delete_webhook', methods=['GET'])
def delete_webhook():
    try:
        success = bot.application.bot.delete_webhook()
        if success:
            return "✅ Webhook deleted successfully"
        else:
            return "❌ Failed to delete webhook"
    except Exception as e:
        return f"❌ Error deleting webhook: {e}"

def run_bot():
    """Run the bot in a separate thread"""
    try:
        logger.info("🤖 Starting Asterix Earnings Bot...")
        
        # Set webhook on startup
        webhook_url = f"{Config.WEBHOOK_URL}/webhook"
        success = bot.application.bot.set_webhook(webhook_url)
        
        if success:
            logger.info(f"✅ Webhook set successfully: {webhook_url}")
        else:
            logger.error("❌ Failed to set webhook")
            
    except Exception as e:
        logger.error(f"❌ Bot startup error: {e}")

# Start the bot when the app starts
@app.before_first_request
def startup():
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.PORT, debug=False)