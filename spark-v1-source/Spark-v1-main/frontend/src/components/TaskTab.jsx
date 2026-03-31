import React, { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/tasks`;  // Core API (niet sandbox)

function TaskTab() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newTask, setNewTask] = useState({
    task: "",
    priority: "medium"
  });
  const [saving, setSaving] = useState(false);
  const [filter, setFilter] = useState("all"); // all, todo, done

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await axios.get(API);
      setTasks(response.data.tasks || []);
    } catch (error) {
      console.error("Error fetching tasks:", error);
    } finally {
      setLoading(false);
    }
  };

  const addTask = async () => {
    if (!newTask.task.trim()) {
      alert("Task mag niet leeg zijn");
      return;
    }

    setSaving(true);
    try {
      await axios.post(API, {
        task: newTask.task,
        priority: newTask.priority
      });
      
      // Clear form
      setNewTask({ task: "", priority: "medium" });
      
      // Reload tasks
      await fetchTasks();
    } catch (error) {
      console.error("Error adding task:", error);
      alert("Kon task niet opslaan");
    } finally {
      setSaving(false);
    }
  };

  const toggleTaskStatus = async (taskId, currentStatus) => {
    try {
      const newStatus = currentStatus === "todo" ? "done" : "todo";
      await axios.patch(`${API}/${taskId}/status?status=${newStatus}`);
      await fetchTasks();
    } catch (error) {
      console.error("Error updating task:", error);
      alert("Kon status niet wijzigen");
    }
  };

  const deleteTask = async (taskId) => {
    if (!window.confirm("Weet je zeker dat je deze task wilt verwijderen?")) {
      return;
    }

    try {
      await axios.delete(`${API}/${taskId}`);
      await fetchTasks();
    } catch (error) {
      console.error("Error deleting task:", error);
      alert("Kon task niet verwijderen");
    }
  };

  const filteredTasks = tasks.filter(task => {
    if (filter === "all") return true;
    return task.status === filter;
  });

  const getPriorityColor = (priority) => {
    switch (priority) {
      case "high": return "#ef4444";
      case "medium": return "#f59e0b";
      case "low": return "#10b981";
      default: return "#6b7280";
    }
  };

  const getPriorityLabel = (priority) => {
    switch (priority) {
      case "high": return "Hoog";
      case "medium": return "Gemiddeld";
      case "low": return "Laag";
      default: return priority;
    }
  };

  if (loading) {
    return (
      <div style={{ padding: "20px", textAlign: "center" }}>
        <p>Taken laden...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
      <h2 style={{ marginBottom: "20px", color: "#fff" }}>📋 Taken</h2>

      {/* Add Task Form */}
      <div style={{
        backgroundColor: "#1e293b",
        padding: "20px",
        borderRadius: "8px",
        marginBottom: "30px",
        border: "1px solid #334155"
      }}>
        <h3 style={{ marginBottom: "15px", color: "#94a3b8", fontSize: "16px" }}>Nieuwe Taak</h3>
        
        <div style={{ marginBottom: "15px" }}>
          <input
            type="text"
            placeholder="Wat moet er gebeuren?"
            value={newTask.task}
            onChange={(e) => setNewTask({ ...newTask, task: e.target.value })}
            onKeyPress={(e) => e.key === "Enter" && addTask()}
            style={{
              width: "100%",
              padding: "12px",
              backgroundColor: "#0f172a",
              border: "1px solid #334155",
              borderRadius: "6px",
              color: "#fff",
              fontSize: "14px"
            }}
          />
        </div>

        <div style={{ 
          display: "flex", 
          gap: "10px", 
          alignItems: "center",
          marginBottom: "15px"
        }}>
          <label style={{ color: "#94a3b8", fontSize: "14px" }}>Prioriteit:</label>
          <select
            value={newTask.priority}
            onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
            style={{
              padding: "8px 12px",
              backgroundColor: "#0f172a",
              border: "1px solid #334155",
              borderRadius: "6px",
              color: "#fff",
              fontSize: "14px"
            }}
          >
            <option value="low">Laag</option>
            <option value="medium">Gemiddeld</option>
            <option value="high">Hoog</option>
          </select>
        </div>

        <button
          onClick={addTask}
          disabled={saving}
          style={{
            padding: "10px 20px",
            backgroundColor: saving ? "#475569" : "#3b82f6",
            color: "#fff",
            border: "none",
            borderRadius: "6px",
            cursor: saving ? "not-allowed" : "pointer",
            fontSize: "14px",
            fontWeight: "500"
          }}
        >
          {saving ? "Opslaan..." : "Taak Toevoegen"}
        </button>
      </div>

      {/* Filter Tabs */}
      <div style={{ 
        display: "flex", 
        gap: "10px", 
        marginBottom: "20px",
        borderBottom: "1px solid #334155",
        paddingBottom: "10px"
      }}>
        {[
          { id: "all", label: "Alles", count: tasks.length },
          { id: "todo", label: "Te doen", count: tasks.filter(t => t.status === "todo").length },
          { id: "done", label: "Klaar", count: tasks.filter(t => t.status === "done").length }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setFilter(tab.id)}
            style={{
              padding: "8px 16px",
              backgroundColor: filter === tab.id ? "#3b82f6" : "transparent",
              color: filter === tab.id ? "#fff" : "#94a3b8",
              border: "1px solid",
              borderColor: filter === tab.id ? "#3b82f6" : "#334155",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "14px",
              fontWeight: "500"
            }}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      {/* Tasks List */}
      {filteredTasks.length === 0 ? (
        <div style={{ 
          textAlign: "center", 
          padding: "40px", 
          color: "#64748b" 
        }}>
          <p>Geen taken {filter !== "all" ? `met status "${filter}"` : ""}</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {filteredTasks.map(task => (
            <div
              key={task.id}
              style={{
                backgroundColor: "#1e293b",
                padding: "15px",
                borderRadius: "8px",
                border: "1px solid #334155",
                display: "flex",
                alignItems: "center",
                gap: "15px"
              }}
            >
              {/* Checkbox */}
              <input
                type="checkbox"
                checked={task.status === "done"}
                onChange={() => toggleTaskStatus(task.id, task.status)}
                style={{
                  width: "20px",
                  height: "20px",
                  cursor: "pointer",
                  accentColor: "#10b981"
                }}
              />

              {/* Task Text */}
              <div style={{ flex: 1 }}>
                <p style={{
                  margin: 0,
                  color: task.status === "done" ? "#64748b" : "#fff",
                  textDecoration: task.status === "done" ? "line-through" : "none",
                  fontSize: "14px"
                }}>
                  {task.task}
                </p>
                {/* Note Link Indicator */}
                {task.note_id && (
                  <div style={{
                    marginTop: "4px",
                    display: "flex",
                    alignItems: "center",
                    gap: "5px",
                    color: "#94a3b8",
                    fontSize: "12px"
                  }}>
                    <span>📝</span>
                    <span>Gekoppeld aan notitie</span>
                  </div>
                )}
              </div>

              {/* Priority Badge */}
              <span style={{
                padding: "4px 12px",
                backgroundColor: getPriorityColor(task.priority) + "20",
                color: getPriorityColor(task.priority),
                borderRadius: "12px",
                fontSize: "12px",
                fontWeight: "500"
              }}>
                {getPriorityLabel(task.priority)}
              </span>

              {/* Delete Button */}
              <button
                onClick={() => deleteTask(task.id)}
                style={{
                  padding: "6px 12px",
                  backgroundColor: "transparent",
                  color: "#ef4444",
                  border: "1px solid #ef4444",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontSize: "12px",
                  pointerEvents: 'auto',
                  zIndex: 9999
                }}
                type="button"
              >
                🗑️
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Stats */}
      <div style={{ 
        marginTop: "30px", 
        padding: "15px",
        backgroundColor: "#0f172a",
        borderRadius: "8px",
        border: "1px solid #334155"
      }}>
        <div style={{ 
          display: "flex", 
          justifyContent: "space-around",
          fontSize: "14px",
          color: "#94a3b8"
        }}>
          <div>
            <strong style={{ color: "#fff" }}>{tasks.filter(t => t.status === "todo").length}</strong> te doen
          </div>
          <div>
            <strong style={{ color: "#10b981" }}>{tasks.filter(t => t.status === "done").length}</strong> klaar
          </div>
          <div>
            <strong style={{ color: "#fff" }}>{tasks.length}</strong> totaal
          </div>
        </div>
      </div>
    </div>
  );
}

export default TaskTab;
