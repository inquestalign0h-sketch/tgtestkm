import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ================= 🔐 安全加密做法：從雲端保險箱讀取密碼 =================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
# ======================================================================

ai_client = OpenAI(
    base_url="https://openrouter.ai",
    api_key=OPENROUTER_API_KEY
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **歡迎使用您的個人 AI 文書助理！**\n\n"
        "你可以隨時叫我幫手做嘢，例如：\n"
        "✍️ 『幫我寫一封同客開會嘅 Email』\n"
        "📰 『幫我寫篇新產品發佈嘅新聞稿』\n"
        "📝 『幫我出 3 個 IG Marketing 嘅橋』\n\n"
        "🎨 **需要整圖？**\n"
        "請使用 `/draw [英文提示詞]`，例如：\n"
        "`/draw A glass of refreshing iced coffee on a sunny Hong Kong beach, photorealistic`"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ 請輸入你想畫嘅嘢（建議用英文描述效果更好喔！）\n例如：`/draw a cute robot`")
        return
    prompt = " ".join(context.args)
    await update.message.reply_text("🎨 收到！正在為您設計圖片，請稍候...")
    image_url = f"https://pollinations.ai{requests.utils.quote(prompt)}?width=1024&height=1024&nologo=true"
    try:
        await update.message.reply_photo(photo=image_url, caption=f"✨ 根據您的提示詞生成的圖片：\n`{prompt}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ 繪圖失敗：{str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_chat_action(action="typing")
    try:
        completion = ai_client.chat.completions.create(
            model="google/gemma-2-9b-it:free",
            messages=[
                {
                    "role": "system", 
                    "content": "你是一個專業的個人文書與 Marketing 助理。請主要使用香港繁體中文（廣東話）回答，語氣專業而親切。如果用戶要求寫報告、電郵或新聞稿，請提供結構清晰、排版美觀的內容。"
                },
                {"role": "user", "content": user_text}
            ]
        )
        ai_response = completion.choices.message.content
        if len(ai_response) > 1000:
            file_path = "ai_output.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(ai_response)
            await update.message.reply_text("📝 由於內容較長，我已為您整理並打包成文字檔案：")
            with open(file_path, "rb") as f:
                await update.message.reply_document(document=f, filename="助理文書報告.txt")
            os.remove(file_path)
        else:
            await update.message.reply_text(ai_response, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ 呼叫 AI 時發生錯誤：{str(e)}")

def main():
    print("🚀 AI 助理正在啟動中...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("draw", draw_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🟢 助理已成功上線！")
    app.run_polling()

if __name__ == "__main__":
    main()
