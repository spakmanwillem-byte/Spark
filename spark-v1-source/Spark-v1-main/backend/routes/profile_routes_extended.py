from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from utils.data_manager import DataManager

router = APIRouter()

class ProfileUpdateExtended(BaseModel):
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
    privacy_niveau: Optional[str] = None


@router.put("/extended")
async def update_profile_extended(profile: ProfileUpdateExtended):
    """
    Update user profile with ALL extended fields
    """
    try:
        users = DataManager.load_users()
        user = next((u for u in users if u["id"] == profile.user_id), None)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Initialize persoonlijke_info if not exists
        if "persoonlijke_info" not in user:
            user["persoonlijke_info"] = {}
        
        info = user["persoonlijke_info"]
        
        # Update all fields dynamically
        for field, value in profile.dict(exclude={'user_id'}, exclude_none=True).items():
            if field in ['naam', 'volledige_naam']:
                user[field] = value
            else:
                info[field] = value
        
        # Save
        DataManager.save_users(users)
        
        return {
            "success": True,
            "message": "Profiel succesvol bijgewerkt",
            "updated_fields": list(profile.dict(exclude_none=True).keys())
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")


@router.get("/{user_id}/extended")
async def get_profile_extended(user_id: str):
    """
    Get full extended profile
    """
    try:
        users = DataManager.load_users()
        user = next((u for u in users if u["id"] == user_id), None)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "user_id": user["id"],
            "naam": user.get("naam"),
            "volledige_naam": user.get("volledige_naam"),
            "gradatie": user.get("gradatie"),
            "xp": user.get("xp", 0),
            "persoonlijke_info": user.get("persoonlijke_info", {})
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")
