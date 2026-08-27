"""
Test Suite for Spark Core 2.0 - Five Modules CRUD Testing
Modules: Agenda, Notes/Tasks, Dagboek, Triggers, Persons
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAgendaModule:
    """Agenda (Events) CRUD tests"""
    
    def test_get_events_returns_array(self):
        """GET /api/agenda/events/user-001 returns events array"""
        response = requests.get(f"{BASE_URL}/api/agenda/events/user-001")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert isinstance(data["events"], list)
        print(f"✓ Agenda: Found {len(data['events'])} events")
    
    def test_create_event(self):
        """POST /api/agenda/events/user-001 creates new event"""
        payload = {
            "titel": f"TEST_Event_{uuid.uuid4().hex[:6]}",
            "beschrijving": "Test event description",
            "date": "2026-04-15T10:00:00"
        }
        response = requests.post(
            f"{BASE_URL}/api/agenda/events/user-001",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "event" in data
        assert data["event"]["titel"] == payload["titel"]
        assert "id" in data["event"]
        print(f"✓ Agenda: Created event with id {data['event']['id']}")
        return data["event"]["id"]
    
    def test_create_and_delete_event(self):
        """DELETE /api/agenda/events/user-001/{id} deletes event"""
        # Create first
        payload = {
            "titel": f"TEST_ToDelete_{uuid.uuid4().hex[:6]}",
            "date": "2026-04-20T14:00:00"
        }
        create_res = requests.post(
            f"{BASE_URL}/api/agenda/events/user-001",
            json=payload
        )
        assert create_res.status_code == 200
        event_id = create_res.json()["event"]["id"]
        
        # Delete
        delete_res = requests.delete(f"{BASE_URL}/api/agenda/events/user-001/{event_id}")
        assert delete_res.status_code == 200
        data = delete_res.json()
        assert data["success"] == True
        print(f"✓ Agenda: Deleted event {event_id}")


class TestNotesModule:
    """Notes CRUD tests"""
    
    def test_get_notes_returns_array(self):
        """GET /api/notes/all returns notes array"""
        response = requests.get(f"{BASE_URL}/api/notes/all")
        assert response.status_code == 200
        data = response.json()
        assert "notes" in data
        assert isinstance(data["notes"], list)
        print(f"✓ Notes: Found {len(data['notes'])} notes")
    
    def test_create_note(self):
        """POST /api/notes/create creates new note"""
        payload = {
            "titel": f"TEST_Note_{uuid.uuid4().hex[:6]}",
            "inhoud": "Test note content",
            "categorie": "Observatie",
            "priority": "medium"
        }
        response = requests.post(f"{BASE_URL}/api/notes/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["note"]["titel"] == payload["titel"]
        print(f"✓ Notes: Created note with id {data['note']['id']}")
        return data["note"]["id"]
    
    def test_create_and_delete_note(self):
        """DELETE /api/notes/delete/{id} deletes note"""
        # Create
        payload = {"titel": f"TEST_ToDelete_{uuid.uuid4().hex[:6]}", "inhoud": "Delete me"}
        create_res = requests.post(f"{BASE_URL}/api/notes/create", json=payload)
        note_id = create_res.json()["note"]["id"]
        
        # Delete
        delete_res = requests.delete(f"{BASE_URL}/api/notes/delete/{note_id}")
        assert delete_res.status_code == 200
        assert delete_res.json()["success"] == True
        print(f"✓ Notes: Deleted note {note_id}")


class TestTasksModule:
    """Tasks CRUD tests"""
    
    def test_get_tasks_returns_array(self):
        """GET /api/notes/tasks returns tasks array"""
        response = requests.get(f"{BASE_URL}/api/notes/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert isinstance(data["tasks"], list)
        print(f"✓ Tasks: Found {len(data['tasks'])} tasks")
    
    def test_create_task(self):
        """POST /api/notes/tasks/create creates new task"""
        payload = {
            "task": f"TEST_Task_{uuid.uuid4().hex[:6]}",
            "priority": "high"
        }
        response = requests.post(f"{BASE_URL}/api/notes/tasks/create", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["task"]["task"] == payload["task"]
        assert data["task"]["status"] == "todo"
        print(f"✓ Tasks: Created task with id {data['task']['id']}")
        return data["task"]["id"]
    
    def test_toggle_task_status(self):
        """PUT /api/notes/tasks/update/{id} toggles task status"""
        # Create task
        create_res = requests.post(
            f"{BASE_URL}/api/notes/tasks/create",
            json={"task": f"TEST_Toggle_{uuid.uuid4().hex[:6]}", "priority": "medium"}
        )
        task_id = create_res.json()["task"]["id"]
        
        # Toggle to done
        update_res = requests.put(
            f"{BASE_URL}/api/notes/tasks/update/{task_id}",
            json={"status": "done"}
        )
        assert update_res.status_code == 200
        data = update_res.json()
        assert data["success"] == True
        assert data["task"]["status"] == "done"
        assert data["task"]["completed_at"] is not None
        print(f"✓ Tasks: Toggled task {task_id} to done")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/notes/tasks/delete/{task_id}")
    
    def test_create_and_delete_task(self):
        """DELETE /api/notes/tasks/delete/{id} deletes task"""
        # Create
        create_res = requests.post(
            f"{BASE_URL}/api/notes/tasks/create",
            json={"task": f"TEST_ToDelete_{uuid.uuid4().hex[:6]}"}
        )
        task_id = create_res.json()["task"]["id"]
        
        # Delete
        delete_res = requests.delete(f"{BASE_URL}/api/notes/tasks/delete/{task_id}")
        assert delete_res.status_code == 200
        assert delete_res.json()["success"] == True
        print(f"✓ Tasks: Deleted task {task_id}")


class TestDagboekModule:
    """Dagboek (Diary) CRUD tests"""
    
    def test_get_entries_returns_array(self):
        """GET /api/dagboek/entries/user-001 returns entries array"""
        response = requests.get(f"{BASE_URL}/api/dagboek/entries/user-001")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert isinstance(data["entries"], list)
        print(f"✓ Dagboek: Found {len(data['entries'])} entries")
    
    def test_create_entry(self):
        """POST /api/dagboek/entries/user-001 creates new entry"""
        payload = {
            "content": f"TEST_Entry_{uuid.uuid4().hex[:6]} - Dit is een test dagboek entry",
            "mood": "blij"
        }
        response = requests.post(
            f"{BASE_URL}/api/dagboek/entries/user-001",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "entry" in data
        assert data["entry"]["mood"] == "blij"
        assert data["entry"]["word_count"] > 0
        print(f"✓ Dagboek: Created entry with id {data['entry']['id']}")
        return data["entry"]["id"]
    
    def test_create_and_delete_entry(self):
        """DELETE /api/dagboek/entries/user-001/{id} deletes entry"""
        # Create
        create_res = requests.post(
            f"{BASE_URL}/api/dagboek/entries/user-001",
            json={"content": f"TEST_ToDelete_{uuid.uuid4().hex[:6]}", "mood": "neutraal"}
        )
        entry_id = create_res.json()["entry"]["id"]
        
        # Delete
        delete_res = requests.delete(f"{BASE_URL}/api/dagboek/entries/user-001/{entry_id}")
        assert delete_res.status_code == 200
        assert delete_res.json()["success"] == True
        print(f"✓ Dagboek: Deleted entry {entry_id}")


class TestTriggersModule:
    """Triggers read-only tests (no CRUD, just consolidated view)"""
    
    def test_get_all_triggers(self):
        """GET /api/triggers/all returns trigger_groups and stats"""
        response = requests.get(f"{BASE_URL}/api/triggers/all")
        assert response.status_code == 200
        data = response.json()
        assert "trigger_groups" in data
        assert "stats" in data
        assert isinstance(data["trigger_groups"], dict)
        assert "total_groups" in data["stats"]
        assert "total_triggers" in data["stats"]
        print(f"✓ Triggers: Found {data['stats']['total_groups']} groups with {data['stats']['total_triggers']} triggers")
    
    def test_triggers_have_types(self):
        """Triggers have correct type categorization"""
        response = requests.get(f"{BASE_URL}/api/triggers/all")
        data = response.json()
        types_found = set()
        for key, group in data["trigger_groups"].items():
            assert "type" in group
            assert "label" in group
            assert "triggers" in group
            types_found.add(group["type"])
        
        expected_types = {"conversation", "calendar", "emotion", "admin", "system"}
        assert types_found == expected_types, f"Expected {expected_types}, got {types_found}"
        print(f"✓ Triggers: All 5 types present: {types_found}")
    
    def test_triggers_by_type_filter(self):
        """GET /api/triggers/by-type/{type} filters correctly"""
        response = requests.get(f"{BASE_URL}/api/triggers/by-type/emotion")
        assert response.status_code == 200
        data = response.json()
        for key, group in data["trigger_groups"].items():
            assert group["type"] == "emotion"
        print(f"✓ Triggers: Filter by type works, found {len(data['trigger_groups'])} emotion groups")


class TestPersonsModule:
    """Persoonskaarten (Person Cards) CRUD tests"""
    
    def test_get_persons_returns_array(self):
        """GET /api/persons/cards/user-001 returns persons array"""
        response = requests.get(f"{BASE_URL}/api/persons/cards/user-001")
        assert response.status_code == 200
        data = response.json()
        assert "persons" in data
        assert isinstance(data["persons"], list)
        print(f"✓ Persons: Found {len(data['persons'])} persons")
    
    def test_create_person(self):
        """POST /api/persons/cards/user-001 creates new person"""
        payload = {
            "naam": f"TEST_Person_{uuid.uuid4().hex[:6]}",
            "relatie": "kennis",
            "gradatie": 4,
            "tags": ["test", "automated"]
        }
        response = requests.post(
            f"{BASE_URL}/api/persons/cards/user-001",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["person"]["naam"] == payload["naam"]
        assert data["person"]["gradatie"] == 4
        print(f"✓ Persons: Created person with id {data['person']['id']}")
        return data["person"]["id"]
    
    def test_create_and_delete_person(self):
        """DELETE /api/persons/cards/user-001/{id} deletes person"""
        # Create
        create_res = requests.post(
            f"{BASE_URL}/api/persons/cards/user-001",
            json={"naam": f"TEST_ToDelete_{uuid.uuid4().hex[:6]}", "gradatie": 5}
        )
        person_id = create_res.json()["person"]["id"]
        
        # Delete
        delete_res = requests.delete(f"{BASE_URL}/api/persons/cards/user-001/{person_id}")
        assert delete_res.status_code == 200
        assert delete_res.json()["success"] == True
        print(f"✓ Persons: Deleted person {person_id}")
    
    def test_get_relationships(self):
        """GET /api/persons/relationships/user-001 returns relationships"""
        response = requests.get(f"{BASE_URL}/api/persons/relationships/user-001")
        assert response.status_code == 200
        data = response.json()
        assert "relationships" in data
        assert isinstance(data["relationships"], list)
        print(f"✓ Persons: Found {len(data['relationships'])} relationships")


# Cleanup fixture to remove TEST_ prefixed data after tests
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup TEST_ prefixed data after all tests"""
    yield
    # Cleanup notes
    try:
        notes_res = requests.get(f"{BASE_URL}/api/notes/all")
        for note in notes_res.json().get("notes", []):
            if note.get("titel", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/notes/delete/{note['id']}")
    except Exception:
        pass
    
    # Cleanup tasks
    try:
        tasks_res = requests.get(f"{BASE_URL}/api/notes/tasks")
        for task in tasks_res.json().get("tasks", []):
            if task.get("task", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/notes/tasks/delete/{task['id']}")
    except Exception:
        pass
    
    # Cleanup events
    try:
        events_res = requests.get(f"{BASE_URL}/api/agenda/events/user-001")
        for event in events_res.json().get("events", []):
            if event.get("titel", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/agenda/events/user-001/{event['id']}")
    except Exception:
        pass
    
    # Cleanup dagboek entries
    try:
        entries_res = requests.get(f"{BASE_URL}/api/dagboek/entries/user-001")
        for entry in entries_res.json().get("entries", []):
            if entry.get("content", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/dagboek/entries/user-001/{entry['id']}")
    except Exception:
        pass
    
    # Cleanup persons
    try:
        persons_res = requests.get(f"{BASE_URL}/api/persons/cards/user-001")
        for person in persons_res.json().get("persons", []):
            if person.get("naam", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/persons/cards/user-001/{person['id']}")
    except Exception:
        pass
    
    print("\n✓ Cleanup: Removed all TEST_ prefixed data")
