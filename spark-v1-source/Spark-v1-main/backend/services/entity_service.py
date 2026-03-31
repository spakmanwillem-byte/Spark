import spacy
from typing import List, Dict, Optional
from utils.data_manager import DataManager

class EntityService:
    def __init__(self):
        # Lazy loading: don't load spaCy model during __init__
        self._nlp = None
        
        # Custom entities from base knowledge
        self.custom_entities = self._load_custom_entities()
    
    @property
    def nlp(self):
        """Lazy load spaCy model only when first accessed"""
        if self._nlp is None:
            try:
                self._nlp = spacy.load("nl_core_news_sm")
            except Exception as e:
                print(f"Warning: Failed to load spaCy model: {e}")
                self._nlp = False  # Mark as failed
        return self._nlp if self._nlp is not False else None
    
    def _load_custom_entities(self) -> Dict:
        """Load custom entities from Willem's world"""
        willem_data = DataManager.load_json("base_knowledge/willem_profile.json")
        
        entities = {
            "PERSOON": ["Willem", "Willem Spakman", "Roadkill"],
            "ORGANISATIE": ["Spark Your Life", "Roadkill Community"],
            "PRODUCT": []
        }
        
        # Add Lotus
        if willem_data.get("relaties", {}).get("dochter"):
            lotus = willem_data["relaties"]["dochter"]
            entities["PERSOON"].extend([lotus.get("naam"), lotus.get("volledige_naam")])
        
        return entities
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text
        Returns: {entity_type: [entities]}
        """
        entities = {
            "personen": [],
            "locaties": [],
            "organisaties": [],
            "datums": [],
            "getallen": [],
            "custom": []
        }
        
        if not self.nlp:
            return entities
        
        # Process with spaCy
        doc = self.nlp(text)
        
        for ent in doc.ents:
            if ent.label_ == "PER" or ent.label_ == "PERSON":
                entities["personen"].append(ent.text)
            elif ent.label_ == "LOC" or ent.label_ == "GPE":
                entities["locaties"].append(ent.text)
            elif ent.label_ == "ORG":
                entities["organisaties"].append(ent.text)
            elif ent.label_ == "DATE" or ent.label_ == "TIME":
                entities["datums"].append(ent.text)
            elif ent.label_ in ["CARDINAL", "QUANTITY"]:
                entities["getallen"].append(ent.text)
        
        # Check custom entities
        text_lower = text.lower()
        for entity_type, entity_list in self.custom_entities.items():
            for entity in entity_list:
                if entity and entity.lower() in text_lower:
                    if entity_type == "PERSOON":
                        if entity not in entities["personen"]:
                            entities["personen"].append(entity)
                    elif entity_type == "ORGANISATIE":
                        if entity not in entities["organisaties"]:
                            entities["organisaties"].append(entity)
                    entities["custom"].append(entity)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def extract_relationships(self, text: str, entities: Dict) -> List[Dict]:
        """
        Extract relationships between entities
        Returns: [{"subject": str, "verb": str, "object": str}]
        """
        relationships = []
        
        if not self.nlp:
            return relationships
        
        doc = self.nlp(text)
        
        # Simple subject-verb-object extraction
        for token in doc:
            if token.dep_ == "ROOT":  # Main verb
                subject = None
                obj = None
                
                # Find subject
                for child in token.children:
                    if child.dep_ in ["nsubj", "nsubjpass"]:
                        subject = child.text
                    elif child.dep_ in ["dobj", "pobj", "attr"]:
                        obj = child.text
                
                if subject and obj:
                    relationships.append({
                        "subject": subject,
                        "verb": token.text,
                        "object": obj
                    })
        
        return relationships
