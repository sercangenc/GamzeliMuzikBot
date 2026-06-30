#!/usr/bin/env python3
from pyrogram import Client
from pyrogram.session import StringSession

api_id = int(input("API_ID: ").strip())
api_hash = input("API_HASH: ").strip()

with Client(":memory:", api_id=api_id, api_hash=api_hash) as app:
    print("Oturum oluşturuluyor... Telefon/Doğrulama isteyen ekran gelecek.")
    print("SESSION STRING:\n")
    print(StringSession.save(app.session))
    print("\nBu STRING'i ASSISTANT_SESSION olarak sample.env'e veya .env'e koy.")
