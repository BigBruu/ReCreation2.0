import React from 'react';

const fieldCls = 'w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white';
const labelCls = 'block text-sm font-medium mb-1 text-gray-300';

const NewRoundTab = ({ newRound, setNewRound, loading, newRoundResult, onStartNewRound }) => (
  <div className="space-y-6 max-w-2xl">
    <h2 className="text-xl font-bold">Neue Runde starten</h2>
    <p className="text-sm text-gray-400">
      Alle laufenden Daten (Spieler, Planeten, Flotten) werden gelöscht und das Universum
      mit den unten angegebenen Einstellungen neu generiert.
    </p>

    <div className="bg-gray-800 p-6 rounded border border-gray-700 space-y-5">
      <div>
        <label className={labelCls}>Ressourcen pro Planet</label>
        <input
          type="number"
          min="1000000"
          max="500000000"
          step="1000000"
          value={newRound.resources_per_planet}
          onChange={e => setNewRound({ ...newRound, resources_per_planet: e.target.value })}
          className={fieldCls}
        />
        <p className="text-xs text-gray-500 mt-1">
          Empfehlung: 10.000.000 – 100.000.000 · Aktuell: {Number(newRound.resources_per_planet).toLocaleString('de-DE')}
        </p>
      </div>

      <div>
        <label className={labelCls}>Anzahl Planeten mit Ressourcen</label>
        <input
          type="number"
          min="1"
          max={newRound.universe_size * newRound.universe_size}
          value={newRound.planet_count}
          onChange={e => setNewRound({ ...newRound, planet_count: e.target.value })}
          className={fieldCls}
        />
        <p className="text-xs text-gray-500 mt-1">
          Max. bei {newRound.universe_size}×{newRound.universe_size}: {newRound.universe_size * newRound.universe_size} Felder
        </p>
      </div>

      <div>
        <label className={labelCls}>Spielfeldgröße: {newRound.universe_size}×{newRound.universe_size}</label>
        <input
          type="range"
          min="15"
          max="50"
          value={newRound.universe_size}
          onChange={e => setNewRound({ ...newRound, universe_size: Number(e.target.value) })}
          className="w-full accent-red-500"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>15×15 (klein)</span>
          <span>50×50 (groß)</span>
        </div>
      </div>

      <div>
        <label className={labelCls}>Tick-Dauer: {newRound.tick_duration} Sekunden</label>
        <input
          type="range"
          min="10"
          max="60"
          step="5"
          value={newRound.tick_duration}
          onChange={e => setNewRound({ ...newRound, tick_duration: Number(e.target.value) })}
          className="w-full accent-red-500"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>10s (schnell)</span>
          <span>60s (langsam)</span>
        </div>
      </div>

      <div>
        <label className={labelCls}>Maximale Spieleranzahl</label>
        <input
          type="number"
          min="1"
          max="100"
          value={newRound.max_players}
          onChange={e => setNewRound({ ...newRound, max_players: e.target.value })}
          className={fieldCls}
        />
      </div>

      <div className="bg-gray-900 rounded p-4 text-sm space-y-1 border border-gray-600">
        <p className="font-semibold text-gray-300 mb-2">Zusammenfassung der neuen Runde:</p>
        <p>🗺️ Spielfeld: <span className="text-white font-mono">{newRound.universe_size}×{newRound.universe_size}</span></p>
        <p>🪐 Planeten: <span className="text-white font-mono">{Number(newRound.planet_count).toLocaleString('de-DE')}</span></p>
        <p>💎 Ressourcen/Planet: <span className="text-white font-mono">{Number(newRound.resources_per_planet).toLocaleString('de-DE')}</span></p>
        <p>⏱️ Tick-Dauer: <span className="text-white font-mono">{newRound.tick_duration}s</span></p>
        <p>👥 Max. Spieler: <span className="text-white font-mono">{newRound.max_players}</span></p>
      </div>

      <button
        onClick={onStartNewRound}
        disabled={loading}
        className="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-6 py-3 rounded font-bold text-lg transition-colors"
      >
        {loading ? '⏳ Wird gestartet...' : '🚀 Neue Runde starten'}
      </button>
    </div>

    {newRoundResult && (
      <div className="bg-green-900 border border-green-500 rounded p-4 space-y-1 text-sm">
        <p className="font-bold text-green-400 text-base">✅ {newRoundResult.message}</p>
        <p>Spielfeld: {newRoundResult.universe_size}</p>
        <p>Erstellte Planeten: <span className="font-mono text-white">{newRoundResult.planets_created}</span></p>
        <p>Ressourcen pro Planet: <span className="font-mono text-white">{Number(newRoundResult.resources_per_planet).toLocaleString('de-DE')}</span></p>
        <p>Tick-Dauer: {newRoundResult.tick_duration}</p>
        <p>Max. Spieler: {newRoundResult.max_players}</p>
      </div>
    )}
  </div>
);

export default NewRoundTab;
