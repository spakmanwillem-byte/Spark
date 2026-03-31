import React from "react";

const MoodSelector = ({ selectedMood, onMoodChange }) => {
  const moods = [
    { value: "blij", emoji: "😊", label: "Blij", color: "bg-yellow-500/20 text-yellow-300 border-yellow-500/50" },
    { value: "gespannen", emoji: "😰", label: "Gespannen", color: "bg-orange-500/20 text-orange-300 border-orange-500/50" },
    { value: "verdrietig", emoji: "😢", label: "Verdrietig", color: "bg-blue-500/20 text-blue-300 border-blue-500/50" },
    { value: "boos", emoji: "😠", label: "Boos", color: "bg-red-500/20 text-red-300 border-red-500/50" },
    { value: "enthousiast", emoji: "🤩", label: "Enthousiast", color: "bg-purple-500/20 text-purple-300 border-purple-500/50" },
    { value: "moe", emoji: "😴", label: "Moe", color: "bg-gray-500/20 text-gray-300 border-gray-500/50" },
    { value: "neutraal", emoji: "😐", label: "Neutraal", color: "bg-slate-500/20 text-slate-300 border-slate-500/50" },
    { value: "energiek", emoji: "⚡", label: "Energiek", color: "bg-green-500/20 text-green-300 border-green-500/50" }
  ];

  return (
    <div className="space-y-2">
      <label className="text-sm text-gray-300 font-medium">
        🎭 Hoe voel je je?
      </label>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {moods.map((mood) => (
          <button
            key={mood.value}
            type="button"
            onClick={() => onMoodChange(mood.value)}
            className={`px-4 py-3 rounded-lg border-2 transition-all font-medium text-sm ${
              selectedMood === mood.value
                ? mood.color + " scale-105"
                : "bg-slate-700/30 text-gray-400 border-slate-600/30 hover:border-slate-500/50"
            }`}
          >
            <div className="flex flex-col items-center gap-1">
              <span className="text-2xl">{mood.emoji}</span>
              <span>{mood.label}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default MoodSelector;
