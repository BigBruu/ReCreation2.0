import React from 'react';

const RESOURCE_ICONS = { plantage: '🌾', erzmine: '⚙️', elektrolysator: '⚡' };
const SPECIAL_ICONS = { werft: '🔧', raumhafen: '🚀', forschungslabor: '🔬' };

const ResourceBuildingCard = ({ building, totalMetal, onUpgrade }) => {
  const canAfford = totalMetal >= building.upgrade_cost_metal;
  const resourceLabel =
    building.current_bonus.resource_type === 'food' ? 'Nahrung' :
    building.current_bonus.resource_type === 'metal' ? 'Metall' : 'Wasserstoff';

  return (
    <div className="building-card">
      <div className="building-header">
        <span className="building-name">
          {RESOURCE_ICONS[building.building_type]} {building.name}
        </span>
        <span className="building-level">Level {building.level}</span>
      </div>
      <div className="building-description">{building.description}</div>
      <div className="building-bonus">
        {building.current_bonus.resource_per_tick > 0 ? (
          <span className="bonus-active">
            +{building.current_bonus.resource_per_tick} {resourceLabel}/Tick
          </span>
        ) : (
          <span className="bonus-inactive">Kein Bonus (Level 0)</span>
        )}
      </div>
      <div className="building-upgrade">
        <div className="upgrade-cost">
          Kosten: <span className={canAfford ? 'resource-metal' : 'resource-insufficient'}>
            ⚙️ {building.upgrade_cost_metal.toLocaleString()} Metall
          </span>
        </div>
        <div className="upgrade-time">Bauzeit: {building.upgrade_time_ticks} Ticks</div>
        {building.upgrading ? (
          <div className="upgrading-indicator">
            🔨 Ausbau läuft...
            <div className="upgrade-completion">
              Fertig: {new Date(building.upgrade_end_time).toLocaleString('de-DE')}
            </div>
          </div>
        ) : (
          <button
            onClick={() => onUpgrade(building.building_type)}
            disabled={!canAfford}
            className="btn-primary upgrade-btn"
          >
            Ausbauen → Level {building.level + 1}
          </button>
        )}
      </div>
    </div>
  );
};

const SpecialBuildingCard = ({ building, totalMetal, onUpgrade }) => {
  const canAfford = totalMetal >= building.upgrade_cost_metal;

  return (
    <div className={`building-card building-special building-${building.building_type}`}>
      <div className="building-header">
        <span className="building-name">
          {SPECIAL_ICONS[building.building_type]} {building.name}
        </span>
        <span className="building-level">Level {building.level}</span>
      </div>
      <div className="building-description">{building.description}</div>
      <div className="building-bonus">
        {building.building_type === 'werft' && (
          <span className="bonus-active">Max. Prototypen: {building.current_bonus.prototype_slots || 0}</span>
        )}
        {building.building_type === 'raumhafen' && (
          <span className="bonus-active">Max. Flotten: {building.current_bonus.fleet_slots || 0}</span>
        )}
        {building.building_type === 'forschungslabor' && (
          <span className="bonus-active">Forschungszeit: -{building.current_bonus.research_time_reduction || 0}%</span>
        )}
      </div>
      <div className="building-upgrade">
        <div className="upgrade-cost">
          Kosten: <span className={canAfford ? 'resource-metal' : 'resource-insufficient'}>
            ⚙️ {building.upgrade_cost_metal.toLocaleString()} Metall
          </span>
        </div>
        <div className="upgrade-time">Bauzeit: {building.upgrade_time_ticks} Ticks</div>
        {building.upgrading ? (
          <div className="upgrading-indicator">
            🔨 Ausbau läuft...
            <div className="upgrade-completion">
              Fertig: {new Date(building.upgrade_end_time).toLocaleString('de-DE')}
            </div>
          </div>
        ) : (
          <button
            onClick={() => onUpgrade(building.building_type)}
            disabled={!canAfford}
            className="btn-primary upgrade-btn"
          >
            Ausbauen → Level {building.level + 1}
          </button>
        )}
      </div>
    </div>
  );
};

const BuildingsTab = ({ userBuildings, userPlanets, onUpgrade }) => {
  const totalMetal = userPlanets.reduce((sum, p) => sum + p.resources.metal, 0);

  return (
    <div className="facilities-content">
      <h3>🏗️ Gebäude & Einrichtungen</h3>

      <div className="total-resources-display">
        <span>Verfügbares Metall: </span>
        <span className="resource-metal">⚙️ {totalMetal.toLocaleString()}</span>
      </div>

      <div className="buildings-section">
        <h4>📦 Ressourcen-Gebäude</h4>
        <div className="buildings-grid">
          {userBuildings.filter(b => b.category === 'resource').map(building => (
            <ResourceBuildingCard
              key={building.building_type}
              building={building}
              totalMetal={totalMetal}
              onUpgrade={onUpgrade}
            />
          ))}
        </div>
      </div>

      <div className="buildings-section">
        <h4>🏛️ Spezial-Gebäude</h4>
        <div className="buildings-grid">
          {userBuildings.filter(b => b.category === 'special').map(building => (
            <SpecialBuildingCard
              key={building.building_type}
              building={building}
              totalMetal={totalMetal}
              onUpgrade={onUpgrade}
            />
          ))}
        </div>
      </div>

      <div className="planets-section">
        <h4>🌍 Ihre Planeten</h4>
        <div className="planets-list">
          {userPlanets.map(planet => (
            <div key={planet.id} className={`planet-card planet-${planet.planet_type}`}>
              <h5>{planet.name}</h5>
              <div className="planet-position">({planet.position.x}:{planet.position.y})</div>
              <div className="planet-resources">
                <span>🌾 {planet.resources.food.toLocaleString()}</span>
                <span>⚙️ {planet.resources.metal.toLocaleString()}</span>
                <span>⚡ {planet.resources.hydrogen.toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default BuildingsTab;
