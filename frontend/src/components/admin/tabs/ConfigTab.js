import React from 'react';

const inputCls = 'w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded';

const ConfigField = ({ label, value, min, max, step, onChange }) => (
  <div>
    <label className="block text-sm font-medium mb-2">{label}</label>
    <input
      type="number"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={onChange}
      className={inputCls}
    />
  </div>
);

const ConfigTab = ({ config, setConfig, onSave }) => {
  if (!config) return null;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Spielkonfiguration</h2>
      <div className="bg-gray-800 p-6 rounded border border-gray-700">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ConfigField
            label="Max. Spieler (5-30)"
            value={config.max_players}
            min="5" max="30"
            onChange={(e) => setConfig({ ...config, max_players: parseInt(e.target.value) })}
          />
          <ConfigField
            label="Universum-Größe (35-50)"
            value={config.universe_size}
            min="35" max="50"
            onChange={(e) => setConfig({ ...config, universe_size: parseInt(e.target.value) })}
          />
          <ConfigField
            label="Tick-Dauer (1-60s)"
            value={config.tick_duration}
            min="1" max="60"
            onChange={(e) => setConfig({ ...config, tick_duration: parseInt(e.target.value) })}
          />
          <ConfigField
            label="Mining-Effizienz (0.1-3.0)"
            value={config.mining_efficiency}
            min="0.1" max="3.0" step="0.1"
            onChange={(e) => setConfig({ ...config, mining_efficiency: parseFloat(e.target.value) })}
          />
          <ConfigField
            label="Kolonisierungszeit (1-168h)"
            value={config.colonization_time_hours}
            min="1" max="168"
            onChange={(e) => setConfig({ ...config, colonization_time_hours: parseInt(e.target.value) })}
          />
        </div>
        <button onClick={() => onSave(config)} className="mt-4 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">
          Konfiguration speichern
        </button>
      </div>
    </div>
  );
};

export default ConfigTab;
