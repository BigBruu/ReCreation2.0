import React from 'react';

const ActionsTab = ({ onResetGame }) => (
  <div className="space-y-6">
    <h2 className="text-xl font-bold">Aktionen</h2>
    <div className="bg-gray-800 p-6 rounded border border-gray-700 space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-red-400 mb-2">⚠️ Gefährliche Aktionen</h3>
        <button
          onClick={onResetGame}
          className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded"
        >
          Spiel komplett zurücksetzen
        </button>
        <p className="text-sm text-gray-500 mt-2">
          Löscht alle Spieler, Planeten, Flotten und startet neu
        </p>
      </div>
    </div>
  </div>
);

export default ActionsTab;
