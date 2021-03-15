import json
from pprint import pprint
import requests
from telegram import Update, Bot
from telegram.ext import CommandHandler

from tg_bot import dispatcher


api_url="http://api.openweathermap.org/data/2.5/forecast?"
api_key = "1408d15a21c820caa11a952c18b87675"
v1 = "Veri yok"
v2 = "Veri yok"
v3 = "Veri yok"

def sehirID(sehir):
    with open("turkey.json","r",encoding="utf-8") as dosya:
        veri = json.load(dosya)                                    #Buradan gelen veri JSON string'ler içeren bir liste
        for x in veri:
            if sehir == x["city"]["name"]:
                id= x["city"]["id"]["$numberLong"]
                return id
    
def anlikBilgi(id):
    site = api_url + "id=" + id + "&APPID=" + api_key
    bilgi = requests.get(site)
    bilgi = bilgi.json()
    sicaklik = bilgi["list"][0]["main"]["temp"] - 273.15
    hissedilen = bilgi["list"][0]["main"]["feels_like"] - 273.15
    nem = bilgi["list"][0]["main"]["humidity"]        
    gokyuzu = bilgi["list"][0]["weather"][0]["id"]
    veriListe=[sicaklik , hissedilen , nem, gokyuzu]
    return veriListe

    
def veriAl(sicaklik , hissedilen , nem , gokyuzu):
        
    if gokyuzu == 803:
        gokyuzu = "Çok bulutlu 51-84%"
    elif gokyuzu == 804:
            gokyuzu = "Kapalı 85-100%"
    elif gokyuzu == 802:
        gokyuzu = "Parçalı bulutlu 25-50%"
    elif gokyuzu == 801:
        gokyuzu = "Az bulutlu 11-25%"
    elif gokyuzu == 800:
        gokyuzu = "Hava açık"
    elif gokyuzu == 741:
        gokyuzu = "Sisli"
    elif gokyuzu == 500:
        gokyuzu = "Hafif yağmur"
    elif gokyuzu == 501:
        gokyuzu = "Aptal ıslatan yağmuru"
    elif gokyuzu == 502 or gokyuzu == 521:
        gokyuzu = "Sağanak yağmur"
    elif gokyuzu == 503 or gokyuzu == 522:
        gokyuzu = "Şiddetli sağanak yağmur"
    elif gokyuzu == 504:
        gokyuzu = "Çok şiddetli yağmur"    
    elif gokyuzu == 511:
        gokyuzu = "Dolu"   
    elif gokyuzu == 520:
         gokyuzu = "Hafif şiddetli sağanak yağmur"    
    elif gokyuzu == 531:
        gokyuzu = "Düzensiz aralıklarla yağış"   
    elif gokyuzu == 300 or gokyuzu == 301 or gokyuzu == 302 or gokyuzu == 310 or gokyuzu == 311 or gokyuzu == 312 or gokyuzu ==313 or gokyuzu==314 or gokyuzu==321:
        gokyuzu = "Çiseleme"  
    elif gokyuzu >= 200 and gokyuzu <= 210:
        gokyuzu = "Hafif ve ara ara rüzgarlı"
    elif gokyuzu >= 211 and gokyuzu <= 221:
        gokyuzu = "Çok şiddetli rüzgarlar"
    elif gokyuzu == 232:
        gokyuzu = "Çok şiddetli rüzgarlar"
    else:
        gokyuzu = "Tanımsız hava olayları"

    v1 = f"Sıcaklık: {round(sicaklik,2)} derece ; Hissedilen sıcaklık: {round(hissedilen,2)} derece"
    v2 = f"Nem oranı : %{round(nem,2)}"
    v3 = f"Hava durumu: {gokyuzu}"
    print(v1,v2,v3)


################################################    ANA KOD BLOĞU


def havanasil(bot: Bot, update: Update):
    if update.effective_message:
        
        msg = update.effective_message
        secim = msg.text
        try:
            secim2 = secim.strip()
            sehiradi = secim2.capitalize()
            veri = sehirID(sehiradi)
            veriListesi = anlikBilgi(veri)
            veriAl(veriListesi[0],veriListesi[1],veriListesi[2],veriListesi[3])
            update.effective_message.reply_text(sehiradi +" şehrinde hava bilgileri:")
            update.effective_message.reply_text(v1)
            update.effective_message.reply_text(v2)
            update.effective_message.reply_text(v3)
        except Exception:
            print("Hata")
            update.effective_message.reply_text("Geçerli bir şehir adı girmedin, Böyle bir şehir var mı??")
    else:
        msg.reply_text("Şehir adı girmen gerekiyor, değil mi??")


__help__ = """
Hava durumu öğrenin !
 - /hava <Şehir adı>
"""

__mod_name__ = "Hava durumu"
HAVA_HANDLER = CommandHandler('hava', havanasil)

dispatcher.add_handler(HAVA_HANDLER)


