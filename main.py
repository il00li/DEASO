import os
import logging
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo, InputMediaDocument
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8496475334:AAFVBYMsb_d_K80YkD06V3ZlcASS2jzV0uQ')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7251748706'))
PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY', '51444506-bffefcaf12816bd85a20222d1')

# In-memory storage (for production, consider using a database)
users_data = {}
force_channels = []  # List of channel usernames
banned_users = set()
bot_stats = {
    'total_users': 0,
    'total_searches': 0,
    'start_date': datetime.now().isoformat()
}

class PixabayBot:
    def __init__(self):
        self.pixabay_base_url = "https://pixabay.com/api/"
        self.search_types = {
            'photo': '📷 الصور',
            'illustration': '🎨 الرسوم التوضيحية', 
            'vector': '📐 الرسوم المتجهة',
            'video': '🎬 الفيديو',
            'music': '🎵 الموسيقى',
            'gif': '🎞️ الصور المتحركة'
        }
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        # Check if user is banned
        if user_id in banned_users:
            await update.message.reply_text("❌ تم حظرك من استخدام البوت")
            return
        
        # Add user to database if not exists
        if user_id not in users_data:
            users_data[user_id] = {
                'username': username,
                'join_date': datetime.now().isoformat(),
                'search_count': 0,
                'current_search': None,
                'search_results': [],
                'current_result_index': 0,
                'selected_search_type': 'all',
                'waiting_for_search': False
            }
            bot_stats['total_users'] += 1
        
        # Check force subscription
        if not await self.check_user_subscriptions(user_id, context):
            await self.send_subscription_message(update)
            return
        
        # User is subscribed, show main menu
        await self.send_main_menu(update)
    
    async def check_user_subscriptions(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is subscribed to all mandatory channels"""
        if not force_channels:
            return True
        
        for channel in force_channels:
            try:
                member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
                if member.status in ['left', 'kicked']:
                    return False
            except Exception as e:
                logger.error(f"Error checking subscription for {channel}: {e}")
                # If we can't check, assume not subscribed
                return False
        
        return True
    
    async def send_subscription_message(self, update: Update):
        """Send subscription verification message"""
        message = """   (•_•)  
  <)   )╯  
   /   \\  
🎧 | اشترك في القنوات اولا"""
        
        keyboard = []
        
        # Add channel buttons
        for channel in force_channels:
            keyboard.append([InlineKeyboardButton(f"📢 {channel}", url=f"https://t.me/{channel.replace('@', '')}")])
        
        # Add verification button
        keyboard.append([InlineKeyboardButton("تحقق | Verify ✅", callback_data="verify_subscription")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)
    
    async def send_main_menu(self, update: Update):
        """Send main menu after successful verification"""
        message = """(⊙_☉)  
  /|\\
  / \\
هل تريد بدء بحث؟!"""
        
        keyboard = [
            [InlineKeyboardButton("بدء البحث 🎧", callback_data="start_search")],
            [InlineKeyboardButton("نوع البحث 💐", callback_data="search_type_menu")]
        ]
        
        # Add admin panel button for admin user
        if update.effective_user and update.effective_user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("🔧 لوحة التحكم", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(message, reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        # Check if user is banned
        if user_id in banned_users:
            await query.edit_message_text("❌ تم حظرك من استخدام البوت")
            return
        
        if data == "verify_subscription":
            if await self.check_user_subscriptions(user_id, context):
                await self.send_main_menu(update)
            else:
                await query.edit_message_text("❌ لم تشترك في جميع القنوات المطلوبة!")
        
        elif data == "start_search":
            await query.edit_message_text("🔍 ارسل كلمة البحث:")
            users_data[user_id]['waiting_for_search'] = True
        
        elif data == "search_type_menu":
            await self.show_search_type_menu(query, user_id)
        
        elif data.startswith("search_type_"):
            search_type = data.replace("search_type_", "")
            users_data[user_id]['selected_search_type'] = search_type
            await self.show_search_type_menu(query, user_id)
        
        elif data == "search_with_type":
            await query.edit_message_text("🔍 ارسل كلمة البحث:")
            users_data[user_id]['waiting_for_search'] = True
        
        elif data == "next_result":
            await self.navigate_results(query, user_id, 1)
        
        elif data == "prev_result":
            await self.navigate_results(query, user_id, -1)
        
        elif data == "select_result":
            await self.select_result(query, user_id)
        
        elif data == "back_to_main":
            await self.send_main_menu(update)
        
        # Admin callbacks
        elif data == "admin_panel":
            if user_id == ADMIN_ID:
                await self.show_admin_panel_buttons(query)
        
        elif data.startswith("admin_"):
            if user_id == ADMIN_ID:
                await self.handle_admin_callback(query, data)
    
    async def show_search_type_menu(self, query, user_id: int):
        """Show search type selection menu"""
        current_type = users_data[user_id].get('selected_search_type', 'all')
        
        keyboard = []
        for search_type, display_name in self.search_types.items():
            indicator = "👻" if current_type == search_type else ""
            keyboard.append([InlineKeyboardButton(f"{display_name} {indicator}", callback_data=f"search_type_{search_type}")])
        
        keyboard.append([InlineKeyboardButton("بدء البحث عن النوع المحدد 🔍", callback_data="search_with_type")])
        keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("اختر نوع البحث:", reply_markup=reply_markup)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        
        # Check if user is banned
        if user_id in banned_users:
            await update.message.reply_text("❌ تم حظرك من استخدام البوت")
            return
        
        # Check if user exists and is verified
        if user_id not in users_data:
            await update.message.reply_text("ارسل /start أولاً")
            return
        
        if not await self.check_user_subscriptions(user_id, context):
            await self.send_subscription_message(update)
            return
        
        # No more text commands needed - everything is now button-based
        
        # Handle search queries
        if users_data[user_id].get('waiting_for_search'):
            await self.perform_search(update, user_id)
            users_data[user_id]['waiting_for_search'] = False
        
        # Handle admin functions
        elif user_id == ADMIN_ID:
            if users_data[user_id].get('waiting_for_broadcast'):
                await self.send_broadcast_message(update, update.message.text)
                users_data[user_id]['waiting_for_broadcast'] = False
            elif users_data[user_id].get('waiting_for_channel_add'):
                await self.add_channel(update, update.message.text)
                users_data[user_id]['waiting_for_channel_add'] = False
            elif users_data[user_id].get('waiting_for_channel_remove'):
                await self.remove_channel(update, update.message.text)
                users_data[user_id]['waiting_for_channel_remove'] = False
            elif users_data[user_id].get('waiting_for_user_action'):
                await self.handle_user_action(update, update.message.text)
                users_data[user_id]['waiting_for_user_action'] = False
    
    async def perform_search(self, update: Update, user_id: int):
        """Perform Pixabay search"""
        search_query = update.message.text
        search_type = users_data[user_id].get('selected_search_type', 'all')
        
        # Pixabay API parameters
        params = {
            'key': PIXABAY_API_KEY,
            'q': search_query,
            'per_page': 100,  # Increased to 100 results
            'safesearch': 'true',
            'lang': 'ar'
        }
        
        # Set category based on search type
        if search_type != 'all' and search_type in self.search_types:
            if search_type == 'music':
                # Music search uses different endpoint
                url = "https://pixabay.com/api/music/"
            elif search_type == 'video':
                url = "https://pixabay.com/api/videos/"
            else:
                params['category'] = search_type
                url = self.pixabay_base_url
        else:
            url = self.pixabay_base_url
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('total', 0) == 0:
                await update.message.reply_text("""   ¯\\_(ツ)_/¯
    كلماتك غريبة يا غلام""")
                return
            
            # Store search results
            users_data[user_id]['search_results'] = data['hits']
            users_data[user_id]['current_result_index'] = 0
            users_data[user_id]['current_search'] = search_query
            
            # Update statistics
            users_data[user_id]['search_count'] += 1
            bot_stats['total_searches'] += 1
            
            # Show first result
            await self.show_search_result(update, user_id)
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            await update.message.reply_text("❌ حدث خطأ في البحث، حاول مرة أخرى")
    
    async def show_search_result(self, update: Update, user_id: int, edit_message=False):
        """Display search result with navigation - supports all media types"""
        results = users_data[user_id]['search_results']
        index = users_data[user_id]['current_result_index']
        
        if not results or index >= len(results):
            return
        
        result = results[index]
        
        # Determine media type and prepare message
        media_url = None
        media_type = None
        
        # Check for different media types
        if 'webformatURL' in result:  # Images, illustrations, vectors
            media_url = result['webformatURL']
            media_type = 'photo'
        elif 'videos' in result:  # Video results
            media_url = result['videos']['small']['url']
            media_type = 'video'
        elif 'url' in result and result.get('type') == 'music':  # Music
            media_url = result['url']
            media_type = 'audio'
        
        # Prepare caption based on media type
        caption = f"🔍 النتيجة {index + 1} من {len(results)}\n"
        
        if media_type in ['photo', 'video']:
            caption += f"👀 المشاهدات: {result.get('views', 'غير محدد')}\n"
            caption += f"👍 الإعجابات: {result.get('likes', 'غير محدد')}\n"
            caption += f"📥 التحميلات: {result.get('downloads', 'غير محدد')}\n"
            caption += f"🏷️ الكلمات المفتاحية: {result.get('tags', 'غير محدد')}"
        elif media_type == 'audio':
            caption += f"🎵 {result.get('name', 'غير محدد')}\n"
            caption += f"🎤 الفنان: {result.get('artist', 'غير محدد')}\n"
            caption += f"⏱️ المدة: {result.get('duration', 'غير محدد')} ثانية\n"
            caption += f"🏷️ النوع: {result.get('genre', 'غير محدد')}"
        
        # Navigation keyboard
        keyboard = []
        nav_row = []
        
        if index > 0:
            nav_row.append(InlineKeyboardButton("« السابق", callback_data="prev_result"))
        if index < len(results) - 1:
            nav_row.append(InlineKeyboardButton("التالي »", callback_data="next_result"))
        
        if nav_row:
            keyboard.append(nav_row)
        
        keyboard.append([InlineKeyboardButton("اختيار 🥇", callback_data="select_result")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            if not edit_message:
                # Send new message
                if media_type == 'photo':
                    await update.message.reply_photo(
                        photo=media_url,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                elif media_type == 'video':
                    await update.message.reply_video(
                        video=media_url,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                elif media_type == 'audio':
                    await update.message.reply_audio(
                        audio=media_url,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                else:
                    await update.message.reply_text(caption, reply_markup=reply_markup)
            else:
                # Edit existing message (handled in navigate_results)
                pass
                
        except Exception as e:
            logger.error(f"Error showing result: {e}")
            # Fallback to text message
            await update.message.reply_text(caption, reply_markup=reply_markup)
    
    async def navigate_results(self, query, user_id: int, direction: int):
        """Navigate through search results - supports all media types"""
        current_index = users_data[user_id]['current_result_index']
        results = users_data[user_id]['search_results']
        
        new_index = current_index + direction
        
        if 0 <= new_index < len(results):
            users_data[user_id]['current_result_index'] = new_index
            
            # Update the result display directly
            result = results[new_index]
            
            # Determine media type and prepare message
            media_url = None
            media_type = None
            
            if 'webformatURL' in result:  # Images, illustrations, vectors
                media_url = result['webformatURL']
                media_type = 'photo'
            elif 'videos' in result:  # Video results
                media_url = result['videos']['small']['url']
                media_type = 'video'
            elif 'url' in result and result.get('type') == 'music':  # Music
                media_url = result['url']
                media_type = 'audio'
            
            # Prepare caption based on media type
            caption = f"🔍 النتيجة {new_index + 1} من {len(results)}\n"
            
            if media_type in ['photo', 'video']:
                caption += f"👀 المشاهدات: {result.get('views', 'غير محدد')}\n"
                caption += f"👍 الإعجابات: {result.get('likes', 'غير محدد')}\n"
                caption += f"📥 التحميلات: {result.get('downloads', 'غير محدد')}\n"
                caption += f"🏷️ الكلمات المفتاحية: {result.get('tags', 'غير محدد')}"
            elif media_type == 'audio':
                caption += f"🎵 {result.get('name', 'غير محدد')}\n"
                caption += f"🎤 الفنان: {result.get('artist', 'غير محدد')}\n"
                caption += f"⏱️ المدة: {result.get('duration', 'غير محدد')} ثانية\n"
                caption += f"🏷️ النوع: {result.get('genre', 'غير محدد')}"
            
            # Navigation keyboard
            keyboard = []
            nav_row = []
            
            if new_index > 0:
                nav_row.append(InlineKeyboardButton("« السابق", callback_data="prev_result"))
            if new_index < len(results) - 1:
                nav_row.append(InlineKeyboardButton("التالي »", callback_data="next_result"))
            
            if nav_row:
                keyboard.append(nav_row)
            
            keyboard.append([InlineKeyboardButton("اختيار 🥇", callback_data="select_result")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                if media_type == 'photo':
                    # Update photo with new image and caption
                    media = InputMediaPhoto(
                        media=media_url,
                        caption=caption
                    )
                    await query.edit_message_media(
                        media=media,
                        reply_markup=reply_markup
                    )
                elif media_type == 'video':
                    # Update video with new video and caption
                    media = InputMediaVideo(
                        media=media_url,
                        caption=caption
                    )
                    await query.edit_message_media(
                        media=media,
                        reply_markup=reply_markup
                    )
                elif media_type == 'audio':
                    # For audio, we can't edit media, so we send a new message
                    await query.message.reply_audio(
                        audio=media_url,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                    # Delete the old message
                    try:
                        await query.message.delete()
                    except:
                        pass
                else:
                    # For text-only results
                    await query.edit_message_text(
                        text=caption,
                        reply_markup=reply_markup
                    )
            except Exception as e:
                logger.error(f"Error updating result: {e}")
                # Fallback to sending new message
                try:
                    if media_type == 'photo':
                        await query.message.reply_photo(
                            photo=media_url,
                            caption=caption,
                            reply_markup=reply_markup
                        )
                    elif media_type == 'video':
                        await query.message.reply_video(
                            video=media_url,
                            caption=caption,
                            reply_markup=reply_markup
                        )
                    elif media_type == 'audio':
                        await query.message.reply_audio(
                            audio=media_url,
                            caption=caption,
                            reply_markup=reply_markup
                        )
                    else:
                        await query.message.reply_text(caption, reply_markup=reply_markup)
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}")
    
    async def select_result(self, query, user_id: int):
        """Handle result selection"""
        results = users_data[user_id]['search_results']
        index = users_data[user_id]['current_result_index']
        
        if results and index < len(results):
            result = results[index]
            
            # Remove keyboard and show selected result
            if 'webformatURL' in result:
                caption = f"✅ تم اختيار النتيجة\n"
                caption += f"👀 المشاهدات: {result.get('views', 'غير محدد')}\n"
                caption += f"👍 الإعجابات: {result.get('likes', 'غير محدد')}\n"
                caption += f"📥 التحميلات: {result.get('downloads', 'غير محدد')}"
                
                await query.edit_message_caption(caption=caption)
            else:
                caption = f"✅ تم اختيار النتيجة\n"
                caption += f"🎵 {result.get('name', 'غير محدد')}\n"
                caption += f"🎤 الفنان: {result.get('artist', 'غير محدد')}\n"
                caption += f"⏱️ المدة: {result.get('duration', 'غير محدد')} ثانية"
                
                await query.edit_message_text(caption)
    
    async def show_admin_panel_buttons(self, query):
        """Show admin control panel with buttons"""
        message = """🔧 لوحة تحكم المدير
        
اختر العملية المطلوبة:"""
        
        keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("📢 إدارة القنوات", callback_data="admin_channels")],
            [InlineKeyboardButton("👤 إدارة المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("📡 إرسال إشعار", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def handle_admin_callback(self, query, data: str):
        """Handle admin callback queries"""
        if data == "admin_stats":
            await self.show_bot_stats_buttons(query)
        elif data == "admin_channels":
            await self.show_channels_management(query)
        elif data == "admin_users":
            await self.show_users_management(query)
        elif data == "admin_broadcast":
            await self.show_broadcast_menu(query)
        elif data == "admin_add_channel":
            await query.edit_message_text("📢 أرسل اسم القناة مع @ (مثال: @channelname)")
            users_data[query.from_user.id]['waiting_for_channel_add'] = True
        elif data == "admin_remove_channel":
            await query.edit_message_text("📢 أرسل اسم القناة مع @ المراد إزالتها")
            users_data[query.from_user.id]['waiting_for_channel_remove'] = True
        elif data.startswith("ban_user_"):
            user_id_to_ban = int(data.replace("ban_user_", ""))
            banned_users.add(user_id_to_ban)
            await query.edit_message_text(f"✅ تم حظر المستخدم {user_id_to_ban}")
        elif data.startswith("unban_user_"):
            user_id_to_unban = int(data.replace("unban_user_", ""))
            banned_users.discard(user_id_to_unban)
            await query.edit_message_text(f"✅ تم إلغاء حظر المستخدم {user_id_to_unban}")
    
    async def show_bot_stats_buttons(self, query):
        """Show bot statistics"""
        start_date = datetime.fromisoformat(bot_stats['start_date'])
        days_running = (datetime.now() - start_date).days
        
        message = f"""📊 إحصائيات البوت

👥 إجمالي المستخدمين: {bot_stats['total_users']}
🔍 إجمالي البحثات: {bot_stats['total_searches']}
📢 قنوات الاشتراك الإجباري: {len(force_channels)}
🚫 المستخدمون المحظورون: {len(banned_users)}
📅 أيام تشغيل البوت: {days_running}
🕐 تاريخ بدء البوت: {start_date.strftime('%Y-%m-%d %H:%M')}

القنوات المطلوبة للاشتراك:
{chr(10).join(force_channels) if force_channels else 'لا توجد قنوات'}"""
        
        keyboard = [[InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def show_channels_management(self, query):
        """Show channels management menu"""
        message = """📢 إدارة القنوات
        
القنوات الحالية:"""
        
        if force_channels:
            for i, channel in enumerate(force_channels, 1):
                message += f"\n{i}. {channel}"
        else:
            message += "\nلا توجد قنوات مضافة"
        
        keyboard = [
            [InlineKeyboardButton("➕ إضافة قناة", callback_data="admin_add_channel")],
            [InlineKeyboardButton("➖ إزالة قناة", callback_data="admin_remove_channel")],
            [InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="admin_panel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def show_users_management(self, query):
        """Show users management menu"""
        message = f"""👤 إدارة المستخدمين
        
إجمالي المستخدمين: {len(users_data)}
المستخدمون المحظورون: {len(banned_users)}

للحظر أو إلغاء الحظر، أرسل معرف المستخدم"""
        
        keyboard = [[InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def show_broadcast_menu(self, query):
        """Show broadcast message menu"""
        message = """📡 إرسال إشعار جماعي
        
أرسل الرسالة التي تريد إرسالها لجميع المستخدمين"""
        
        keyboard = [[InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
        
        # Set user state to wait for broadcast message
        users_data[query.from_user.id]['waiting_for_broadcast'] = True
    
    async def send_broadcast_message(self, update: Update, message: str):
        """Broadcast message to all users"""
        sent_count = 0
        failed_count = 0
        
        for user_id in users_data.keys():
            if user_id != update.effective_user.id:  # Don't send to admin
                try:
                    await update.get_bot().send_message(chat_id=user_id, text=message)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send broadcast to {user_id}: {e}")
                    failed_count += 1
        
        await update.message.reply_text(f"✅ تم إرسال الرسالة إلى {sent_count} مستخدم\n❌ فشل الإرسال إلى {failed_count} مستخدم")
    
    async def add_channel(self, update: Update, channel: str):
        """Add channel to force subscription list"""
        if not channel.startswith('@'):
            channel = '@' + channel
        
        if channel not in force_channels:
            force_channels.append(channel)
            await update.message.reply_text(f"✅ تم إضافة القناة {channel} للاشتراك الإجباري")
        else:
            await update.message.reply_text(f"❌ القناة {channel} موجودة بالفعل")
    
    async def remove_channel(self, update: Update, channel: str):
        """Remove channel from force subscription list"""
        if not channel.startswith('@'):
            channel = '@' + channel
        
        if channel in force_channels:
            force_channels.remove(channel)
            await update.message.reply_text(f"✅ تم إزالة القناة {channel} من الاشتراك الإجباري")
        else:
            await update.message.reply_text(f"❌ القناة {channel} غير موجودة في قائمة الاشتراك الإجباري")
    
    async def handle_user_action(self, update: Update, user_input: str):
        """Handle user ban/unban actions"""
        try:
            user_id = int(user_input)
            if user_id in banned_users:
                banned_users.discard(user_id)
                await update.message.reply_text(f"✅ تم إلغاء حظر المستخدم {user_id}")
            else:
                banned_users.add(user_id)
                await update.message.reply_text(f"✅ تم حظر المستخدم {user_id}")
        except ValueError:
            await update.message.reply_text("❌ معرف المستخدم غير صحيح")
    


def main():
    """Start the bot"""
    # Get port from environment for Render deployment
    port = int(os.environ.get('PORT', 8080))
    
    # Create bot instance
    bot = PixabayBot()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CallbackQueryHandler(bot.handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Start the bot
    logger.info("Starting Pixabay Telegram Bot...")
    logger.info(f"Bot running on port {port}")
    
    # Use webhook for production (Render) or polling for development
    if os.environ.get('RENDER'):
        # Production mode with webhook
        webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url,
            url_path=BOT_TOKEN
        )
    else:
        # Development mode with polling
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()