# 🎯 SPARK TRIGGER OVERZICHT
**Laatst bijgewerkt:** 16 maart 2026

Alle triggers in het Spark systeem voor admin overzicht.

---

## 🤖 BOT TRIGGERS

### **Madelief Stouten** (bot-madelief)
```
Event Triggers:
✅ user_join      → "Hallo {user}! Welkom bij Spark! 👋"
✅ user_leave     → "Pheeuw, {user} is weg... 😅"
✅ silence (5min) → "Zo stil hier... Iedereen nog wakker? 😴"

Keyword Triggers:
✅ "hallo", "hey", "hi", "hoi" → Begroeting terug
```

### **Harry Klokkenmaker** (bot-harry)
```
Schedule Triggers:
⏰ Elk uur (00:00) → "🕐 Het is nu {hour}:00 uur!"

Keyword Triggers:
✅ "hoe laat", "tijd", "klok", "uur" → Huidige tijd
✅ "te laat", "vergeten" → Tijd advies
```

### **Mr Smith** (bot-smith)
```
Schedule Triggers:
🔒 Elk uur → Security check announcement

Keyword Triggers:
✅ "bug", "error", "crash", "hack", "probleem" → System scan
✅ "veilig", "security", "beveiliging" → Security status
✅ suspicious_activity → Alert & onderzoek
```

---

## 📚 KENNISKAART TRIGGERS (Placeholder)

```
⚠️ PLACEHOLDER - Komt binnenkort:

Concept Triggers:
- Als user vraagt naar concept X → Open kaart X
- Als kaart Y gerelateerd is → Suggestie tonen
- Als user vaak over topic Z praat → Reminder quiz

Relatie Triggers:
- Parent kaart bekeken → Toon children
- Similar concepts → Auto-link suggesties
```

---

## 🎓 LEARNING TRIGGERS

```
Spaced Repetition:
✅ Quiz due date reached → Reminder naar user
✅ Mastery < 50% → Extra practice suggestie
✅ 7 dagen geen practice → Gentle reminder

Achievements:
✅ 10 kaarten geleerd → Badge unlock
✅ 7 dagen streak → Achievement
✅ 100% mastery op kaart → Celebration
```

---

## ⏰ SCHEDULE TRIGGERS

```
Hourly:
✅ Harry's tijd announcement (elk uur op :00)
✅ Mr Smith security check (elk uur)

Daily:
⚠️ PLACEHOLDER:
- Daily summary (23:00)
- Backup reminder (02:00)
- Learning streak check (08:00)

Weekly:
⚠️ PLACEHOLDER:
- Progress report (Zondag 20:00)
- Inactive user check (Maandag 10:00)
```

---

## 👥 USER EVENT TRIGGERS

```
Authentication:
✅ user_login → Welcome message
✅ user_logout → Goodbye message
⚠️ user_inactive_7d → Re-engagement (PLACEHOLDER)

Community:
✅ user_join_chat → Madelief begroet
✅ user_leave_chat → Madelief reactie
⚠️ user_first_message → Onboarding tips (PLACEHOLDER)

Progress:
✅ achievement_unlock → Celebration
✅ level_up → Congratulations
⚠️ milestone_reached → Reward (PLACEHOLDER)
```

---

## 💰 ECONOMY TRIGGERS

```
Wallet:
✅ deposit_approved → Credit toegevoegd notification
✅ withdrawal_completed → Payment confirmation
⚠️ balance_low → Top-up reminder (PLACEHOLDER)

Donations:
✅ donation_received → Thank you message
⚠️ recurring_donation_due → Reminder (PLACEHOLDER)

Spark Vermogen:
⚠️ bitcoin_price_change_10% → Alert (PLACEHOLDER)
⚠️ portfolio_milestone → Celebration (PLACEHOLDER)
```

---

## 🔔 SYSTEM TRIGGERS

```
Health Checks:
⚠️ knowledge_base_corrupt → Auto-repair (PLACEHOLDER)
⚠️ user_data_invalid → Validation fix (PLACEHOLDER)
⚠️ graph_out_of_sync → Rebuild trigger (PLACEHOLDER)

Security:
⚠️ suspicious_login → Mr Smith alert (PLACEHOLDER)
⚠️ rate_limit_exceeded → Throttle user (PLACEHOLDER)
⚠️ system_error → Admin notification (PLACEHOLDER)

Backups:
⚠️ daily_backup_time → Auto-backup (PLACEHOLDER)
⚠️ backup_failed → Admin alert (PLACEHOLDER)
```

---

## 📊 ANALYTICS TRIGGERS (Placeholder)

```
⚠️ Komt later:
- User engagement drop → Re-activation campaign
- Popular content → Featured suggestions
- Search patterns → Auto-create related content
```

---

## ⚙️ ADMIN ACTIONS

```
Manual Triggers (Admin Panel):
✅ Approve deposit
✅ Approve withdrawal
✅ Trigger bot response (test)
✅ Simulate bot activity

⚠️ Coming:
- Force sync graph
- Rebuild index
- Send system announcement
- Emergency stop all bots
```

---

## 📝 NOTES

**Legenda:**
- ✅ = Geïmplementeerd & werkend
- ⚠️ = Placeholder (nog bouwen)
- 🔒 = Security gerelateerd
- ⏰ = Tijd-gebaseerd
- 💰 = Economy gerelateerd

**Trigger toevoegen?**
1. Definieer in `/app/backend/data/bots/bot_users.json` (voor bots)
2. Of programmeer in backend services
3. Update dit document
4. Test via admin panel

---

**Einde Trigger Overzicht**
