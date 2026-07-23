import React, { useEffect, useState, useCallback } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL;

const TYPES = [
  { key: "wijsheid", label: "Wijsheid", color: "bg-amber-500/20 text-amber-300", icon: "💎" },
  { key: "patroon", label: "Patroon", color: "bg-cyan-500/20 text-cyan-300", icon: "🔁" },
  { key: "mentaal_model", label: "Mentaal model", color: "bg-purple-500/20 text-purple-300", icon: "🧠" },
  { key: "anker", label: "Anker", color: "bg-emerald-500/20 text-emerald-300", icon: "⚓" },
];

const typeMeta = (t) => TYPES.find((x) => x.key === t) || { label: t, color: "bg-slate-500/20", icon: "•" };

export function BijbelPage() {
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState({ per_type: {}, top_begrippen: [] });
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState("");
  const [filterBegrip, setFilterBegrip] = useState("");
  const [filterText, setFilterText] = useState("");

  // Form
  const [newTekst, setNewTekst] = useState("");
  const [newType, setNewType] = useState("wijsheid");
  const [newBegrippen, setNewBegrippen] = useState("");
  const [newTags, setNewTags] = useState("");
  const [newNotities, setNewNotities] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterType) params.append("type", filterType);
      if (filterBegrip) params.append("begrip", filterBegrip);
      const r = await fetch(`${API}/api/bijbel/list?${params}`);
      const d = await r.json();
      setEntries(d.entries || []);
      setStats(d.stats || {});
    } catch (e) {
      toast.error("Kon Bijbel niet laden: " + e.message);
    } finally {
      setLoading(false);
    }
  }, [filterType, filterBegrip]);

  useEffect(() => {
    load();
  }, [load]);

  const handleAdd = async () => {
    if (!newTekst.trim()) return toast.error("Tekst is leeg");
    const begrippen = newBegrippen.split(",").map((s) => s.trim()).filter(Boolean);
    const tags = newTags.split(",").map((s) => s.trim()).filter(Boolean);
    try {
      const r = await fetch(`${API}/api/bijbel/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tekst: newTekst.trim(),
          type: newType,
          gerelateerde_begrippen: begrippen,
          tags,
          notities: newNotities,
        }),
      });
      const d = await r.json();
      if (d.success) {
        toast.success("Toegevoegd aan Bijbel");
        setNewTekst("");
        setNewBegrippen("");
        setNewTags("");
        setNewNotities("");
        load();
      } else {
        toast.error(d.detail || "Toevoegen mislukt");
      }
    } catch (e) {
      toast.error(e.message);
    }
  };

  const handleDelete = async (id, tekst) => {
    if (!window.confirm(`Verwijder: "${tekst.slice(0, 60)}..."?`)) return;
    try {
      const r = await fetch(`${API}/api/bijbel/${id}`, { method: "DELETE" });
      const d = await r.json();
      if (d.success) {
        toast.success("Verwijderd");
        load();
      } else {
        toast.error(d.detail || "Verwijderen mislukt");
      }
    } catch (e) {
      toast.error(e.message);
    }
  };

  const filtered = entries.filter(
    (e) =>
      !filterText ||
      (e.tekst || "").toLowerCase().includes(filterText.toLowerCase()) ||
      (e.gerelateerde_begrippen || []).some((b) => b.toLowerCase().includes(filterText.toLowerCase()))
  );

  return (
    <div className="p-6 space-y-6" data-testid="bijbel-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Bijbel — semantische laag</h1>
          <p className="text-slate-400 text-sm mt-1">
            Wijsheden, patronen, mentale modellen en ankers. Elke entry kan aan meerdere begrippen gekoppeld zijn.
          </p>
        </div>
        <div className="text-right text-slate-300">
          <div className="text-2xl font-mono">{entries.length}</div>
          <div className="text-xs text-slate-500">entries</div>
        </div>
      </div>

      {/* Type filters */}
      <div className="flex flex-wrap gap-2">
        {TYPES.map((t) => (
          <button
            key={t.key}
            onClick={() => setFilterType(filterType === t.key ? "" : t.key)}
            className={`px-3 py-1.5 rounded-full text-xs transition ${t.color} ${
              filterType === t.key ? "ring-2 ring-white/50" : "hover:opacity-80"
            }`}
            data-testid={`filter-type-${t.key}`}
          >
            {t.icon} {t.label} <span className="opacity-70 ml-1">{stats.per_type?.[t.key] || 0}</span>
          </button>
        ))}
        {(filterType || filterBegrip) && (
          <button
            onClick={() => {
              setFilterType("");
              setFilterBegrip("");
            }}
            className="px-3 py-1.5 rounded-full text-xs bg-slate-700/50 text-slate-300 hover:bg-slate-700"
            data-testid="btn-clear-filters"
          >
            × Reset filters
          </button>
        )}
      </div>

      {/* Top begrippen chips */}
      {stats.top_begrippen && stats.top_begrippen.length > 0 && (
        <div className="bg-slate-900/40 p-3 rounded-lg border border-slate-800">
          <div className="text-xs text-slate-500 mb-2">Top begrippen (klik om te filteren):</div>
          <div className="flex flex-wrap gap-1.5">
            {stats.top_begrippen.map((b) => (
              <button
                key={b.begrip}
                onClick={() => setFilterBegrip(filterBegrip === b.begrip ? "" : b.begrip)}
                className={`px-2 py-0.5 text-xs rounded transition ${
                  filterBegrip === b.begrip
                    ? "bg-purple-500/40 text-white ring-1 ring-purple-300"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
                data-testid={`chip-begrip-${b.begrip}`}
              >
                {b.begrip} <span className="opacity-60">{b.count}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Add form */}
      <Card className="p-4 bg-slate-900/50 border-slate-700 space-y-3">
        <h2 className="text-white font-semibold">Nieuwe entry toevoegen</h2>
        <textarea
          className="w-full bg-slate-800 text-white border border-slate-700 rounded p-3 text-sm min-h-[80px]"
          placeholder='Bv. "Belofte maakt schuld. Belofte geeft hoop. Hoop kan omslaan in teleurstelling."'
          value={newTekst}
          onChange={(e) => setNewTekst(e.target.value)}
          data-testid="input-tekst"
        />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <select
            value={newType}
            onChange={(e) => setNewType(e.target.value)}
            className="bg-slate-800 text-white border border-slate-700 rounded px-3 py-2 text-sm"
            data-testid="select-type"
          >
            {TYPES.map((t) => (
              <option key={t.key} value={t.key}>
                {t.icon} {t.label}
              </option>
            ))}
          </select>
          <Input
            placeholder="Gerelateerde begrippen (komma-separated)"
            value={newBegrippen}
            onChange={(e) => setNewBegrippen(e.target.value)}
            data-testid="input-begrippen"
          />
          <Input
            placeholder="Tags (optioneel)"
            value={newTags}
            onChange={(e) => setNewTags(e.target.value)}
            data-testid="input-tags"
          />
        </div>
        <Input
          placeholder="Extra notities (optioneel)"
          value={newNotities}
          onChange={(e) => setNewNotities(e.target.value)}
          data-testid="input-notities"
        />
        <Button onClick={handleAdd} disabled={!newTekst.trim()} data-testid="btn-add-entry">
          Toevoegen
        </Button>
      </Card>

      {/* Text-filter */}
      <Input
        placeholder="Zoek in lijst..."
        value={filterText}
        onChange={(e) => setFilterText(e.target.value)}
        data-testid="input-filter-text"
      />

      {/* Lijst */}
      {loading ? (
        <div className="text-slate-400">Laden...</div>
      ) : (
        <div className="space-y-3">
          {filtered.map((e) => {
            const tm = typeMeta(e.type);
            return (
              <Card
                key={e.id}
                className="p-4 bg-slate-900/40 border-slate-700"
                data-testid={`entry-card-${e.id}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge className={tm.color}>
                        {tm.icon} {tm.label}
                      </Badge>
                      {e.bron && <span className="text-slate-500 text-xs">— {e.bron}</span>}
                    </div>
                    <p className="text-white text-sm leading-relaxed italic">"{e.tekst}"</p>
                    {e.gerelateerde_begrippen && e.gerelateerde_begrippen.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {e.gerelateerde_begrippen.map((b) => (
                          <button
                            key={b}
                            onClick={() => setFilterBegrip(b)}
                            className="text-xs bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded"
                            data-testid={`begrip-link-${e.id}-${b}`}
                          >
                            → {b}
                          </button>
                        ))}
                      </div>
                    )}
                    {e.notities && (
                      <div className="text-slate-400 text-xs mt-2 italic">{e.notities}</div>
                    )}
                    {e.tags && e.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {e.tags.map((t) => (
                          <span key={t} className="text-[10px] text-slate-500">
                            #{t}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="text-slate-600 text-[10px] mt-2">
                      {(e.aangemaakt || "").slice(0, 10)}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(e.id, e.tekst)}
                    className="text-red-400 hover:text-red-300 text-xs shrink-0"
                    data-testid={`btn-delete-${e.id}`}
                  >
                    Verwijder
                  </button>
                </div>
              </Card>
            );
          })}
          {filtered.length === 0 && (
            <div className="text-center text-slate-500 py-8">
              Nog geen entries{filterType || filterBegrip ? " met deze filters" : ""}.
              <br />
              <span className="text-xs">Voeg je eerste wijsheid, patroon of anker toe hierboven.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default BijbelPage;
