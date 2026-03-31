#!/usr/bin/env python3
"""
Fill Willem's profile from CV data
"""
import json
from pathlib import Path
from datetime import datetime

USERS_FILE = Path("/app/backend/data/users/users.json")

# CV Data extracted
cv_data = {
    "naam": "Willem Spakman",
    "volledige_naam": "Willem Spakman",
    "roepnaam": "Willem",
    "achternaam": "Spakman",
    
    # Contact
    "email": "spakmanwillem@hotmail.com",
    "telefoon": "06-15372764",
    "mobiel": "06-15372764",
    
    # Persoonlijk
    "geboortedatum": "22-04-1977",
    "geboorteplaats": "Nederland",
    "geslacht": "Man",
    "nationaliteit": "Nederlands",
    "leeftijd": str(datetime.now().year - 1977),
    
    # Adres
    "straat": "Bentismaheerd",
    "huisnummer": "180",
    "postcode": "9636 EK",
    "plaats": "Groningen",
    "provincie": "Groningen",
    "land": "Nederland",
    
    # Werk & Carrière
    "beroep": "Senior Pedagogisch Werker",
    "werkgever": "Stichting Authiek, De Glind",
    "functie": "Senior Pedagogisch Werker",
    "werkervaring_jaren": 15,
    "sector": "Zorg & Welzijn",
    "vaardigheden": "Autisme begeleiding, Respijtzorg, Groepsdynamiek, Zelfredzaamheid training, Ontwikkelingsgerichte methodiek, Samenwerking, Oudercontact, Structuur en veiligheid creëren",
    
    # Opleiding
    "opleiding": "Persoonlijk Begeleider Specifieke Doelgroepen (MBO-4)",
    "diploma": "MBO-4 - Persoonlijk Begeleider Specifieke Doelgroepen (2022), MBO-2 - Helpende Zorg en Welzijn (2014), VMBO - Basis Kok",
    "certificaten": "EHBO (recent vernieuwd), Beveiligingsmedewerker (2005)",
    "school_universiteit": "MBO Zorg & Welzijn",
    
    # Profiel
    "over_mij": "Ervaren en toegewijde senior pedagogisch werker met een positieve instelling en sterke werkethiek. Gedreven om mensen te ondersteunen in hun ontwikkeling, met aandacht voor structuur, veiligheid en persoonlijke groei. Sterk in samenwerken en het creëren van een prettige en productieve sfeer binnen het team.",
    
    # Persoonlijkheid
    "sterke_punten": "Positieve instelling, Sterke werkethiek, Structuur creëren, Samenwerken, Empathie, Geduld, Ontwikkelingsgericht, Betrouwbaar",
    "levensvisie": "Gedreven om mensen te ondersteunen in hun ontwikkeling, met focus op structuur, veiligheid en persoonlijke groei.",
    "waarden": "Persoonlijke groei, Structuur, Veiligheid, Samenwerking, Ontwikkeling, Zorg voor anderen",
    
    # Werk geschiedenis
    "werkgeschiedenis": json.dumps([
        {
            "periode": "2017-heden",
            "functie": "Senior Pedagogisch Werker",
            "werkgever": "Stichting Authiek, De Glind",
            "taken": "Begeleiding kinderen/jongeren met autisme, Weekendopvang en vakantieweken, Structuur en veiligheid bieden, Zelfredzaamheid ondersteunen, Collega's begeleiden"
        },
        {
            "periode": "2014-2016",
            "functie": "Werkbegeleider",
            "werkgever": "Goedkopekantoorinrichtingen.nl, Joure",
            "taken": "Begeleiding jongvolwassenen met psychische klachten"
        },
        {
            "periode": "2010-2017",
            "functie": "Activiteitenbegeleider (vrijwillig)",
            "werkgever": "Stichting Stoute Schoenen, Bilthoven",
            "taken": "Zomerkampen voor jongeren met autisme"
        }
    ], ensure_ascii=False),
    
    # Extra
    "rijbewijs": "B",
    "beschikbaarheid": "Fulltime",
    "motivatie": "Passie voor het ondersteunen van mensen met autisme en het begeleiden van persoonlijke ontwikkeling."
}

def fill_willem_profile():
    """Fill Willem's profile with CV data"""
    try:
        with open(USERS_FILE, 'r') as f:
            users_data = json.load(f)
        
        users = users_data.get('users', [])
        
        # Find Willem
        willem = next((u for u in users if 'Willem' in u.get('naam', '')), None)
        
        if not willem:
            print("❌ Willem not found in users.json")
            return
        
        print(f"✅ Found Willem: {willem.get('naam')} (ID: {willem.get('id')})")
        
        # Initialize persoonlijke_info if not exists
        if 'persoonlijke_info' not in willem:
            willem['persoonlijke_info'] = {}
        
        # Fill all CV data
        updated_count = 0
        for key, value in cv_data.items():
            if key in ['naam', 'volledige_naam']:
                willem[key] = value
            else:
                willem['persoonlijke_info'][key] = value
            updated_count += 1
        
        # Save
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Willem's profile updated with {updated_count} fields from CV")
        print(f"   Beroep: {cv_data['beroep']}")
        print(f"   Werkgever: {cv_data['werkgever']}")
        print(f"   Adres: {cv_data['straat']} {cv_data['huisnummer']}, {cv_data['plaats']}")
        print(f"   Opleiding: {cv_data['opleiding']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("FILLING WILLEM'S PROFILE FROM CV")
    print("=" * 60)
    fill_willem_profile()
    print("=" * 60)
