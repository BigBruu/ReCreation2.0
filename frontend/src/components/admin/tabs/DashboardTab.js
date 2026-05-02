import React from 'react';

const StatCard = ({ color, label, value }) => (
  <div className="bg-gray-800 p-6 rounded border border-gray-700">
    <h3 className={`text-lg font-semibold text-${color}-400`}>{label}</h3>
    <p className="text-2xl font-bold">{value}</p>
  </div>
);

const DashboardTab = ({ stats }) => {
  if (!stats) return null;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard color="blue" label="Spieler" value={`${stats.players.current}/${stats.players.max}`} />
        <StatCard color="green" label="Planeten" value={`${stats.planets.occupied}/${stats.planets.total}`} />
        <StatCard color="purple" label="Flotten" value={stats.fleets} />
        <StatCard color="yellow" label="Einladungen" value={stats.invite_codes} />
      </div>
      <div className="bg-gray-800 p-6 rounded border border-gray-700">
        <h3 className="text-lg font-semibold mb-4">Spiel-Infos</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>Universum: {stats.universe_size}</div>
          <div>Tick-Dauer: {stats.tick_duration}</div>
        </div>
      </div>
    </div>
  );
};

export default DashboardTab;
