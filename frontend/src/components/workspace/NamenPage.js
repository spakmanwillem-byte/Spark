import React, { useEffect, useState, useCallback } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL;

const CATEGORIES = [
  { key: "voornaam_man", label: "Voornaam (man)", color: "bg-blue-500/20 text-blue-300" },
  { key: "voornaam_vrouw", label: "Voornaam (vrouw)", color: "bg-pink-500/20 text-pink-300" },
  { key: "voornaam_unisex", label: "Voornaam (unisex)", color: "bg-purple-500/20 text-purple-300" },
  { key: "achternaam", label: "Achternaam", color: "bg-amber-500/20 text-amber-300" },
  { key: "koosnaam", label: "Koosnaam", color: "bg-rose-500/20 text-rose-300" },
  { key: "gamertag", label: "Gamertag", color: "bg-emerald-500/20 text-emerald-300" },
  { key: "onbekend", label: "Onbekend", color: "bg-slate-500/20 text-slate-300" },
];

const catMeta = (c) => CATEGORIES.find((x) => x.key === c) || { label: c, color: "bg-slate-500/20" };

export function NamenPage() {
  const [namen, setNamen] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("");
  const [filterCat, setFilterCat] = useState("");
  const [newNaam, setNewNaam] = useState("");
  const [newCat, setNewCat] = useState("voornaam_man");
  const [newNotitie, setNewNotitie] = useState("");
  const [classifying, setClassifying] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const url = filterCat ? `${API}/api/namen/list?categorie=${filterCat}` : `${API}/api/namen/list`;
      const r = await fetch(url);
      const d = await r.json();
      setNamen(d.namen || []);
      setStats(d.stats?.per_categorie || {});
    } catch (e) {
      toast.error("Kon namen niet laden: " + e.message);
    } finally {
      setLoading(false);
    }
  }, [filterCat]);

  useEffect(() => {
    load();
  }, [load]);

  const handleAdd = async () => {
    if (!newNaam.trim()) return toast.error("Naam is leeg");
    try {
      const r = await fetch(`${API}/api/namen/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ naam: newNaam.trim(), categorie: newCat, notities: newNotitie }),
      });
      const d = await r.json();
      if (d.success) {
        toast.success(`${d.action === "created" ? "Toegevoegd" : "Bijgewerkt"}: ${d.naam}`);
        setNewNaam("");
        setNewNotitie("");
        load();
      } else {
        toast.error(d.detail || d.error || "Toevoegen mislukt");
      }
    } catch (e) {
      toast.error(e.message);
    }
  };

  const handleClassify = async () => {
    if (!newNaam.trim()) return toast.error("Vul een naam in om te classificeren");
    setClassifying(true);
    try {
      const r = await fetch(`${API}/api/namen/classify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ naam: newNaam.trim(), auto_add: false }),
      });
      const d = await r.json();
      if (d.success) {
        setNewCat(d.categorie);
        toast.success(`LLM zegt: ${d.categorie}`);
      } else {
        toast.error(d.error || "Classificatie mislukt");
      }
    } finally {
      setClassifying(false);
    }
  };

  const handleDelete = async (naam) => {
    if (!window.confirm(`Verwijder '${naam}'?`)) return;
    try {
      const r = await fetch(`${API}/api/namen/${encodeURIComponent(naam)}`, { method: "DELETE" });
      const d = await r.json();
      if (d.success) {
        toast.success(`${naam} verwijderd`);
        load();
      } else {
        toast.error(d.detail || "Verwijderen mislukt");
      }
    } catch (e) {
      toast.error(e.message);
    }
  };

  const filtered = namen.filter(
    (n) =>
      !filter ||
      n.naam.toLowerCase().includes(filter.toLowerCase()) ||
      (n.notities || "").toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6" data-testid="namen-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Namen-lade</h1>
          <p className="text-slate-400 text-sm mt-1">
            Spark's persoonlijke naam-classificatie. Voor- en achternamen, koosnamen en gamertags.
          </p>
        </div>
        <div className="text-right text-slate-300">
          <div className="text-2xl font-mono">{namen.length}</div>
          <div className="text-xs text-slate-500">namen totaal</div>
        </div>
      </div>

      {/* Stats-strook */}
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((c) => (
          <button
            key={c.key}
            onClick={() => setFilterCat(filterCat === c.key ? "" : c.key)}
            className={`px-3 py-1.5 rounded-full text-xs transition ${c.color} ${
              filterCat === c.key ? "ring-2 ring-white/50" : "hover:opacity-80"
            }`}
            data-testid={`filter-cat-${c.key}`}
          >
            {c.label} <span className="opacity-70 ml-1">{stats[c.key] || 0}</span>
          </button>
        ))}
      </div>

      {/* Add-form */}
      <Card className="p-4 bg-slate-900/50 border-slate-700 space-y-3">
        <h2 className="text-white font-semibold">Naam toevoegen / bijwerken</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <Input
            placeholder="Naam (bv. Sophie)"
            value={newNaam}
            onChange={(e) => setNewNaam(e.target.value)}
            data-testid="input-nieuwe-naam"
          />
          <select
            value={newCat}
            onChange={(e) => setNewCat(e.target.value)}
            className="bg-slate-800 text-white border border-slate-700 rounded px-3 py-2"
            data-testid="select-categorie"
          >
            {CATEGORIES.map((c) => (
              <option key={c.key} value={c.key}>
                {c.label}
              </option>
            ))}
          </select>
          <Input
            placeholder="Notitie (optioneel)"
            value={newNotitie}
            onChange={(e) => setNewNotitie(e.target.value)}
            data-testid="input-notitie"
          />
          <div className="flex gap-2">
            <Button
              onClick={handleClassify}
              disabled={classifying || !newNaam.trim()}
              variant="outline"
              data-testid="btn-classify-llm"
            >
              {classifying ? "..." : "AI-classificeer"}
            </Button>
            <Button onClick={handleAdd} disabled={!newNaam.trim()} data-testid="btn-add-naam">
              Opslaan
            </Button>
          </div>
        </div>
      </Card>

      {/* Filter */}
      <Input
        placeholder="Zoek in lijst..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        data-testid="input-filter"
      />

      {/* Lijst */}
      {loading ? (
        <div className="text-slate-400">Laden...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map((n) => {
            const meta = catMeta(n.categorie);
            return (
              <Card
                key={n.naam}
                className="p-3 bg-slate-900/40 border-slate-700 flex justify-between items-start"
                data-testid={`naam-card-${n.naam}`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium truncate">{n.naam}</span>
                    <Badge className={meta.color}>{meta.label}</Badge>
                  </div>
                  {n.notities && (
                    <div className="text-slate-400 text-xs mt-1 truncate">{n.notities}</div>
                  )}
                  <div className="text-slate-600 text-xs mt-1">
                    {n.bron} · {(n.toegevoegd || "").slice(0, 10)}
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(n.naam)}
                  className="text-red-400 hover:text-red-300 text-xs ml-2"
                  data-testid={`btn-delete-${n.naam}`}
                >
                  Verwijder
                </button>
              </Card>
            );
          })}
          {filtered.length === 0 && (
            <div className="col-span-full text-center text-slate-500 py-8">
              Geen namen gevonden{filterCat ? " in deze categorie" : ""}.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default NamenPage;
