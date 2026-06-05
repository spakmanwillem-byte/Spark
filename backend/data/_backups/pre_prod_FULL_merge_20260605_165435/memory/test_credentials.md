# Spark Core 2.0 - Test Credentials

## Admin Account (BESCHERMD — kan niet verwijderd worden)
- **Naam**: Willem (of "De Willem")
- **Sleutelwoord**: Appelsap
- **User ID**: user-001
- **Gradatie**: 1 (Beheerder)
- **Masterkey**: SAMEN
- **Admin rol** (v6_admin_role_001): ✅ admin:true (seed)

## Spark (system user)
- **User ID**: user-000
- **Naam**: Spark
- **Gradatie**: 1
- **Admin rol**: ✅ admin:true (seed)

## Admin-wachtwoord (v6_admin_role_001) — voor admin grant/revoke
- **Default ADMIN_PASSWORD**: `AppelsapAdmin2026` (env-var, override via UI/Admin tab)
- **Endpoint reset**: `POST /api/admin/password/reset` met `{user_id, old_password, new_password}`
- **UI-toegang**: Instellingen → Admin-tab → "Admin-wachtwoord wijzigen"

## Non-admin Test Account (voor gradatie-tests)
- **Naam**: Marieke
- **Sleutelwoord**: Welkom01 (default reset)
- **User ID**: user-c609d7d1
- **Gradatie**: 3 (Vriend)

## Nieuw aangemaakt (v5_self_password_001 test)
- **Naam**: Gijs
- **Sleutelwoord**: Welkom01
- **User ID**: user-a0ee2d7e
- **Gradatie**: 3 (Vriend)
- **ROAR balance**: 1 (welkomstgift van Willem)

## Andere Test Accounts
Zie /app/backend/data/system/users.json voor volledige lijst.

## Password Reset
Beheerder kan sleutelwoord van elke user resetten via Gebruikers > Acties > **Reset WW**.
Default reset-waarde: `Welkom01`

## API Endpoints

### Auth Module
```
POST /api/auth/login
Body: {"naam": "Willem", "sleutelwoord": "Appelsap"}

POST /api/auth/session/heartbeat?user_id=user-001
GET  /api/auth/session/validate?user_id=user-001
GET  /api/auth/users
POST /api/auth/users           (create)
PUT  /api/auth/users/{user_id} (update)
DELETE /api/auth/users/{user_id}                      (admin user-001 beschermd, 403)
POST /api/auth/users/{user_id}/reset-password         (default Welkom01)
POST /api/auth/users/{user_id}/reset-password?new_sleutelwoord=...
GET  /api/auth/gradaties
```
