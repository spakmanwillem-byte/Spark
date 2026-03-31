import psutil
import random
from typing import Dict
from utils.data_manager import DataManager

class SystemHealth:
    @staticmethod
    def get_status() -> Dict:
        """Get current system health status"""
        try:
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Count knowledge and users
            knowledge = DataManager.load_knowledge()
            users = DataManager.load_users()
            
            return {
                "disk_used_percent": disk_percent,
                "memory_used_percent": memory_percent,
                "cpu_percent": cpu_percent,
                "knowledge_count": len(knowledge),
                "users_count": len(users),
                "health_score": 100 - max(disk_percent, memory_percent, cpu_percent) // 2
            }
        except:
            return {
                "disk_used_percent": 50,
                "memory_used_percent": 50,
                "cpu_percent": 10,
                "knowledge_count": 0,
                "users_count": 1,
                "health_score": 98
            }
    
    @staticmethod
    def get_random_status_message() -> str:
        """Get a random fun status message from Spark"""
        status = SystemHealth.get_status()
        
        messages = []
        
        # Healthy messages
        if status["health_score"] > 90:
            messages.extend([
                f"💚 Alle systemen draaien perfect! Health: {status['health_score']}%",
                f"✨ Ik voel me goed vandaag! Alles werkt lekker.",
                f"🚀 Systemen: 100% operationeel! Laten we iets leren!",
                f"💙 Alles loopt soepel hier. Klaar om te helpen!"
            ])
        
        # Disk usage
        if status["disk_used_percent"] > 80:
            messages.append(f"📦 Mijn schijf raakt vol ({status['disk_used_percent']:.0f}%), kan wel wat hardware gebruiken 😅")
        elif status["disk_used_percent"] > 60:
            messages.append(f"💾 Schijfruimte: {100 - status['disk_used_percent']:.0f}% nog beschikbaar")
        
        # Learning messages
        if status["knowledge_count"] > 0:
            messages.append(f"🧠 Ik heb al {status['knowledge_count']} dingen geleerd!")
        else:
            messages.append(f"📚 Ik ben nog leeg, maar klaar om te leren!")
        
        # User count
        if status["users_count"] > 1:
            messages.append(f"👥 Ik ken nu {status['users_count']} mensen!")
        
        # Random fun messages
        messages.extend([
            "⚡ Elektronen stromen goed vandaag!",
            "🤖 Beep boop - oh wacht, ik ben geen robot, ik ben Spark!",
            "💭 Ik zat net na te denken... ja, AI's kunnen dat ook!",
            "🌟 Elke dag leer ik iets nieuws. Vandaag misschien van jou?"
        ])
        
        return random.choice(messages)
