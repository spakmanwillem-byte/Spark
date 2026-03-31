from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from utils.data_manager import DataManager

router = APIRouter()

class ProfileUpdate(BaseModel):
    user_id: str
    
    # Basis informatie
    naam: Optional[str] = None
    volledige_naam: Optional[str] = None
    roepnaam: Optional[str] = None
    achternaam: Optional[str] = None
    tussenvoegsel: Optional[str] = None
    
    # Contact
    email: Optional[str] = None
    telefoon: Optional[str] = None
    mobiel: Optional[str] = None
    noodcontact_naam: Optional[str] = None
    noodcontact_telefoon: Optional[str] = None
    
    # Persoonlijk
    geboortedatum: Optional[str] = None
    geboorteplaats: Optional[str] = None
    geslacht: Optional[str] = None
    nationaliteit: Optional[str] = None
    burgerlijke_staat: Optional[str] = None
    
    # Adres
    straat: Optional[str] = None
    huisnummer: Optional[str] = None
    toevoeging: Optional[str] = None
    postcode: Optional[str] = None
    plaats: Optional[str] = None
    provincie: Optional[str] = None
    land: Optional[str] = None
    
    # Familie
    partner_naam: Optional[str] = None
    aantal_kinderen: Optional[int] = None
    kinderen_namen: Optional[str] = None
    ouders_naam: Optional[str] = None
    broers_zussen: Optional[str] = None
    
    # Werk & Carrière
    beroep: Optional[str] = None
    werkgever: Optional[str] = None
    functie: Optional[str] = None
    werkervaring_jaren: Optional[int] = None
    sector: Optional[str] = None
    vaardigheden: Optional[str] = None
    cv_link: Optional[str] = None
    linkedin_profiel: Optional[str] = None
    
    # Opleiding
    opleiding: Optional[str] = None
    school_universiteit: Optional[str] = None
    studierichting: Optional[str] = None
    diploma: Optional[str] = None
    certificaten: Optional[str] = None
    cursussen: Optional[str] = None
    
    # Hobby's & Interesses
    hobbies: Optional[str] = None
    muziek_voorkeur: Optional[str] = None
    film_voorkeur: Optional[str] = None
    game_voorkeur: Optional[str] = None
    boeken_voorkeur: Optional[str] = None
    sport: Optional[str] = None
    favoriete_activiteiten: Optional[str] = None
    
    # Gezondheid
    medicatie: Optional[str] = None
    allergieen: Optional[str] = None
    aandoeningen: Optional[str] = None
    bloedgroep: Optional[str] = None
    huisarts: Optional[str] = None
    zorgverzekering: Optional[str] = None
    
    # Persoonlijkheid & Doelen
    mbti_type: Optional[str] = None
    sterke_punten: Optional[str] = None
    zwakke_punten: Optional[str] = None
    leerdoelen: Optional[str] = None
    levensvisie: Optional[str] = None
    dromen_ambities: Optional[str] = None
    waarden: Optional[str] = None
    
    # Financieel (optioneel, gevoelige info)
    inkomen: Optional[str] = None
    spaardoelen: Optional[str] = None
    schulden: Optional[str] = None
    financiele_situatie: Optional[str] = None
    
    # Social & Netwerk
    beste_vrienden: Optional[str] = None
    communities: Optional[str] = None
    social_media: Optional[str] = None
    verenigingen: Optional[str] = None
    
    # Overig
    over_mij: Optional[str] = None
    levens_motto: Optional[str] = None
    favoriete_citaat: Optional[str] = None
    bijzonderheden: Optional[str] = None
    privacy_niveau: Optional[str] = None  # 'public', 'private', 'friends_only'

class PasswordChange(BaseModel):
    user_id: str
    new_password: str

@router.put("/me")
async def update_profile(profile: ProfileUpdate):
    """Update user profile information"""
    try:
        users = DataManager.load_users()
        user = next((u for u in users if u["id"] == profile.user_id), None)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Initialize nested structures
        if "persoonlijke_info" not in user:
            user["persoonlijke_info"] = {}
        if "contact" not in user:
            user["contact"] = {}
        if "adres" not in user:
            user["adres"] = {}
        if "werk_carriere" not in user:
            user["werk_carriere"] = {}
        if "opleiding" not in user:
            user["opleiding"] = {}
        if "hobbies_interesses" not in user:
            user["hobbies_interesses"] = {}
        
        # Update fields
        if profile.naam is not None:
            user["naam"] = profile.naam
        if profile.volledige_naam is not None:
            user["persoonlijke_info"]["volledige_naam"] = profile.volledige_naam
        if profile.geboortedatum is not None:
            user["persoonlijke_info"]["geboortedatum"] = profile.geboortedatum
        if profile.geslacht is not None:
            user["persoonlijke_info"]["geslacht"] = profile.geslacht
        
        if profile.email is not None:
            user["email"] = profile.email
        if profile.telefoon is not None:
            user["contact"]["telefoon"] = profile.telefoon
        
        if profile.straat is not None:
            user["adres"]["straat"] = profile.straat
        if profile.huisnummer is not None:
            user["adres"]["huisnummer"] = profile.huisnummer
        if profile.postcode is not None:
            user["adres"]["postcode"] = profile.postcode
        if profile.plaats is not None:
            user["adres"]["plaats"] = profile.plaats
        if profile.land is not None:
            user["adres"]["land"] = profile.land
        
        if profile.beroep is not None:
            user["werk_carriere"]["beroep"] = profile.beroep
        if profile.werkgever is not None:
            user["werk_carriere"]["werkgever"] = profile.werkgever
        
        if profile.opleiding is not None:
            user["opleiding"]["opleiding"] = profile.opleiding
        if profile.studierichting is not None:
            user["opleiding"]["studierichting"] = profile.studierichting
        
        if profile.over_mij is not None:
            user["bio"] = profile.over_mij
        if profile.hobbies is not None:
            user["hobbies_interesses"]["hobbies"] = profile.hobbies
        
        # BELANGRIJK: Ook top-level volledige_naam updaten voor backwards compatibility
        if profile.volledige_naam is not None:
            user["volledige_naam"] = profile.volledige_naam
        
        # Save
        DataManager.save_users(users)
        
        return {"success": True, "message": "Profile updated", "user": user}
        DataManager.save_users(users)
        
        return {
            "success": True,
            "message": "Profiel bijgewerkt",
            "user": user
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
        # Update nieuwe profielvelden
        if profile.beroep is not None:
            user["persoonlijke_info"]["beroep"] = profile.beroep
        if profile.opleiding is not None:
            user["persoonlijke_info"]["opleiding"] = profile.opleiding
        if profile.hobbies is not None:
            user["persoonlijke_info"]["hobbies"] = profile.hobbies
        if profile.muziek_voorkeur is not None:
            user["persoonlijke_info"]["muziek_voorkeur"] = profile.muziek_voorkeur
        if profile.film_voorkeur is not None:
            user["persoonlijke_info"]["film_voorkeur"] = profile.film_voorkeur
        if profile.game_voorkeur is not None:
            user["persoonlijke_info"]["game_voorkeur"] = profile.game_voorkeur
        if profile.over_mij is not None:
            user["persoonlijke_info"]["over_mij"] = profile.over_mij
        
        DataManager.save_users(users)
        
        return {
            "success": True,
            "message": "Profiel bijgewerkt",
            "user": user
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/change-password")
async def change_password(data: PasswordChange):
    """
    Change user password (sleutelwoord)
    """
    try:
        users = DataManager.load_users()
        user = next((u for u in users if u["id"] == data.user_id), None)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if len(data.new_password) < 3:
            raise HTTPException(status_code=400, detail="Sleutelwoord moet minimaal 3 tekens zijn")
        
        user["sleutelwoord"] = data.new_password
        DataManager.save_users(users)
        
        return {
            "success": True,
            "message": "Sleutelwoord gewijzigd"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete-account")
async def delete_account(user_id: str, sleutelwoord: str):
    """
    Delete user account (Vergeet Mij)
    User data is removed, but their contributions (knowledge cards) remain
    """
    try:
        users = DataManager.load_users()
        user = next((u for u in users if u["id"] == user_id), None)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify password
        if user["sleutelwoord"] != sleutelwoord:
            raise HTTPException(status_code=401, detail="Incorrect sleutelwoord")
        
        # Create backup before deletion
        backup_file = DataManager.backup_user(user)
        
        # Remove user from list
        users = [u for u in users if u["id"] != user_id]
        DataManager.save_users(users)
        
        # Note: Knowledge cards remain in the system (they don't have user_id attribution)
        # This preserves the user's contributions to Spark's knowledge base
        
        return {
            "success": True,
            "message": "Account verwijderd, contributions bewaard",
            "backup_file": backup_file
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
