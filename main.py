import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sqlalchemy

from config import Config
from database import Database

# Initialize database
db = Database()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AsterixEarningsBot:
    def __init__(self):
        self.application = Application.builder().token(Config.BOT_TOKEN).build()
        self.scheduler = AsyncIOScheduler()
        self.user_ad_sessions = {}
        self.setup_handlers()
        self.setup_scheduler()
    
    def setup_scheduler(self):
        self.scheduler.add_job(self.cleanup_expired_sessions, 'interval', minutes=5)
    
    def setup_handlers(self):
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("withdraw", self.withdraw_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_data = {
            'user_id': user.id,
            'first_name': user.first_name,
            'username': user.username,
            'phone_number': None
        }
        
        # Create or get user
        db_user = db.create_user(user_data)
        
        welcome_text = f"""
🤖 *Welcome to Asterix Earnings Bot* 💰

*Hi {user.first_name}!* 👋

Earn real money by watching simple ads! Here's how it works:

📱 *Features:*
• Watch ads and earn $0.02 per ad
• Minimum withdrawal: ${Config.MIN_WITHDRAWAL}
• Multiple payment methods
• Real-time balance tracking

⚡ *Quick Start:*
1. Click *'📺 Watch Ads'* to start earning
2. Open the ad link and wait 30 seconds
3. Get paid automatically!
4. Withdraw when you reach ${Config.MIN_WITHDRAWAL}

📞 *Support:* Contact admin for help
        """
        
        keyboard = [
            [KeyboardButton("💰 Balance"), KeyboardButton("📺 Watch Ads")],
            [KeyboardButton("💳 Withdraw"), KeyboardButton("📋 Instructions")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = db.get_user(update.effective_user.id)
        if user:
            balance_text = f"""
💼 *Your Account Balance*

💰 *Available Balance:* `${user.balance:.2f}`
🏆 *Total Earned:* `${user.total_earned:.2f}`
📊 *Ads Watched:* `{user.ads_watched}`

💡 *Withdrawal Minimum:* `${Config.MIN_WITHDRAWAL}`
            """
            await update.message.reply_text(balance_text, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Please use /start to register first.")
    
    async def watch_ads_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = db.get_user(user_id)
        
        if not user:
            await update.message.reply_text("❌ Please use /start to register first.")
            return
        
        if user.is_watching_ad:
            await update.message.reply_text("⏳ You are already watching an ad. Please complete it first.")
            return
        
        # Set user as watching ad
        db.set_watching_ad(user_id, True)
        
        ad_message = f"""
🎬 *Watch Ad & Earn ${Config.EARN_PER_AD}*

💰 *Earning Per Ad:* `${Config.EARN_PER_AD}`
⏰ *Required Time:* `{Config.AD_DURATION} seconds`

📋 *Instructions:*
1. Click [👉 Click Here 👈]({Config.AD_LINK}) below to open the ad
2. Wait for *{Config.AD_DURATION} seconds* on the ad page
3. Do NOT close the ad window early
4. Return here and click *'✅ I Completed Watching'*

⚠️ *Important Rules:*
• You must stay on the ad page for full {Config.AD_DURATION} seconds
• Payment is automatic after verification
• Any cheating will result in permanent ban

Click the button below to open the ad link:
        """
        
        keyboard = [
            [InlineKeyboardButton("🎬 👉 Click Here 👈 - Watch & Earn $0.02", url=Config.AD_LINK)],
            [InlineKeyboardButton("✅ I Completed Watching", callback_data="confirm_ad")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_ad")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = await update.message.reply_text(
            ad_message,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=False
        )
        
        # Store the session
        self.user_ad_sessions[user_id] = {
            'message_id': message.message_id,
            'start_time': datetime.now(),
            'completed': False
        }
    
    async def withdraw_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = db.get_user(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("❌ Please use /start to register first.")
            return
        
        if user.balance < Config.MIN_WITHDRAWAL:
            await update.message.reply_text(
                f"❌ *Withdrawal Failed*\n\n"
                f"Your balance (${user.balance:.2f}) is below the minimum withdrawal amount (${Config.MIN_WITHDRAWAL}).\n\n"
                f"💡 Watch more ads to reach the minimum amount!",
                parse_mode='Markdown'
            )
            return
        
        keyboard = []
        for method in Config.PAYMENT_METHODS:
            keyboard.append([InlineKeyboardButton(f"📱 {method.upper()}", callback_data=f"withdraw_{method}")])
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_withdraw")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"💳 *Withdrawal Request*\n\n"
            f"💰 *Available Balance:* `${user.balance:.2f}`\n"
            f"📋 *Minimum Withdrawal:* `${Config.MIN_WITHDRAWAL}`\n\n"
            f"Please choose your withdrawal method:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
📋 *Asterix Earnings - Instructions*

🎯 *How to Earn Money:*
1. Click *'📺 Watch Ads'* button
2. Click *'👉 Click Here 👈'* to open ad link
3. Wait on the ad page for *30 seconds*
4. Return and click *'✅ I Completed Watching'*
5. Get *$0.02* automatically credited

💰 *Withdrawal Information:*
- *Minimum:* $1.00
- *Methods:* bKash, Nagad, Rocket, PayPal
- *Processing:* 24-48 hours
- *Fees:* No hidden fees

📊 *Balance & Statistics:*
- Check your balance anytime
- Track total earnings
- See ads watched count

⚠️ *Important Rules:*
- One account per person only
- No cheating or automation
- Must watch ads completely
- Be patient with withdrawals

📞 *Support:* Contact admin for any issues
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        user_id = update.effective_user.id
        
        if text == "💰 Balance":
            await self.balance_command(update, context)
        elif text == "📺 Watch Ads":
            await self.watch_ads_command(update, context)
        elif text == "💳 Withdraw":
            await self.withdraw_command(update, context)
        elif text == "📋 Instructions":
            await self.help_command(update, context)
        else:
            await update.message.reply_text(
                "Please use the menu buttons below or type /help for instructions.",
                reply_markup=ReplyKeyboardMarkup([
                    [KeyboardButton("💰 Balance"), KeyboardButton("📺 Watch Ads")],
                    [KeyboardButton("💳 Withdraw"), KeyboardButton("📋 Instructions")]
                ], resize_keyboard=True)
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        data = query.data
        
        if data == "confirm_ad":
            await self.confirm_ad_watching(query, context)
        elif data == "cancel_ad":
            await self.cancel_ad_watching(query, context)
        elif data.startswith("withdraw_"):
            method = data.replace("withdraw_", "")
            await self.handle_withdrawal_method(query, context, method)
        elif data == "cancel_withdraw":
            await query.edit_message_text("❌ Withdrawal request cancelled.")
    
    async def confirm_ad_watching(self, query, context):
        user_id = query.from_user.id
        user = db.get_user(user_id)
        
        if not user:
            await query.edit_message_text("❌ User not found. Please use /start first.")
            return
        
        # Check if user was actually watching an ad
        if not user.is_watching_ad:
            await query.answer("❌ You haven't started watching an ad yet!", show_alert=True)
            return
        
        # Credit the user
        user = db.update_user_balance(user_id, Config.EARN_PER_AD)
        
        if user:
            success_text = f"""
✅ *Payment Credited Successfully!* 🎉

💰 *Earned:* `${Config.EARN_PER_AD}`
📊 *New Balance:* `${user.balance:.2f}`
🏆 *Total Ads Watched:* `{user.ads_watched}`
🎯 *Total Earnings:* `${user.total_earned:.2f}`

💡 Keep watching more ads to increase your earnings!
💳 Withdraw anytime when you reach ${Config.MIN_WITHDRAWAL}
            """
            
            # Clear the session
            if user_id in self.user_ad_sessions:
                del self.user_ad_sessions[user_id]
            
            await query.edit_message_text(
                success_text,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ Error processing payment. Please try again.")
    
    async def cancel_ad_watching(self, query, context):
        user_id = query.from_user.id
        db.set_watching_ad(user_id, False)
        
        if user_id in self.user_ad_sessions:
            del self.user_ad_sessions[user_id]
        
        await query.edit_message_text("❌ Ad watching session cancelled.")
    
    async def handle_withdrawal_method(self, query, context, method):
        user = db.get_user(query.from_user.id)
        
        instruction_text = f"""
💳 *Withdrawal - {method.upper()}*

💰 *Your Balance:* `${user.balance:.2f}`
📱 *Payment Method:* {method.upper()}

To process your withdrawal, please send:
`/{method} [your_account_number] [amount]`

*Example:*
`/{method} 01XXXXXX {user.balance:.2f}`

📋 *Requirements:*
• Minimum: ${Config.MIN_WITHDRAWAL}
• Account must be in your name
• Processing time: 24-48 hours

⚠️ *Note:* Replace with your actual {method.upper()} account number
        """
        
        await query.edit_message_text(
            instruction_text,
            parse_mode='Markdown'
        )
    
    async def cleanup_expired_sessions(self):
        """Clean up expired ad sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for user_id, session in self.user_ad_sessions.items():
            if (current_time - session['start_time']).total_seconds() > 600:  # 10 minutes
                expired_sessions.append(user_id)
        
        for user_id in expired_sessions:
            db.set_watching_ad(user_id, False)
            del self.user_ad_sessions[user_id]
    
    def run(self):
        """Start the bot"""
        if not Config.BOT_TOKEN:
            logger.error("❌ BOT_TOKEN not found in environment variables!")
            return
        
        self.scheduler.start()
        logger.info("🤖 Asterix Earnings Bot is starting...")
        logger.info("💼 Database initialized")
        logger.info("⏰ Scheduler started")
        
        try:
            self.application.run_polling()
        except Exception as e:
            logger.error(f"❌ Bot crashed: {e}")

if __name__ == '__main__':
    bot = AsterixEarningsBot()
    bot.run()