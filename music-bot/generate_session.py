"""
Asistan hesabı oturum (session) oluşturucu.

Bu script'i Shell'de çalıştırın:
    cd music-bot && python generate_session.py

Müzik çalacak GERÇEK kullanıcı hesabınızla giriş yapın (bot hesabıyla DEĞİL).
İşlem bitince ekranda çıkan uzun metni (SESSION STRING) kopyalayıp
TELEGRAM_SESSION_STRING adıyla Secret olarak ekleyin.
"""
import asyncio
import os

from pyrogram import Client

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]


async def main():
    print("=" * 60)
    print("  ASİSTAN HESABI OTURUM OLUŞTURUCU")
    print("=" * 60)
    print()
    print("⚠️  Bu hesap sesli sohbete katılıp müziği çalacak.")
    print("⚠️  Bot hesabıyla DEĞİL, gerçek bir Telegram hesabıyla giriş yapın.")
    print()
    print("Telefon numaranızı +90... formatında girin.")
    print("Telegram'a gelen kodu girin (gerekirse 2FA şifrenizi de).")
    print()

    async with Client(
        "gen_session",
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True,
    ) as app:
        session_string = await app.export_session_string()
        me = await app.get_me()
        print()
        print("=" * 60)
        print(f"✅ Giriş başarılı: {me.first_name} (@{me.username})")
        print("=" * 60)
        print()
        print("👇 Aşağıdaki SESSION STRING'i kopyalayın ve")
        print("   TELEGRAM_SESSION_STRING adıyla Secret olarak ekleyin:")
        print()
        print("-" * 60)
        print(session_string)
        print("-" * 60)
        print()
        print("⚠️  Bu metni kimseyle paylaşmayın — hesabınıza tam erişim sağlar!")


if __name__ == "__main__":
    asyncio.run(main())
