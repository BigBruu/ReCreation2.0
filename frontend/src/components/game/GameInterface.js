import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useGameData } from '../../hooks/useGameData';
import Observatory from './Observatory';
import ShipDesignCalculator from './ShipDesignCalculator';
import SpaceportTab from './tabs/SpaceportTab';
import ShipyardTab from './tabs/ShipyardTab';
import BuildingsTab from './tabs/BuildingsTab';
import ResearchTab from './tabs/ResearchTab';

const SIDEBAR_TABS = [
  { id: 'observatorium', label: 'Observatorium' },
  { id: 'raumhafen', label: 'Raumhafen' },
  { id: 'einrichtungen', label: 'Einrichtungen' },
  { id: 'technologie', label: 'Technologie' },
  { id: 'werft', label: 'Werft' },
];

const GameInterface = () => {
  const { user, logout } = useAuth();
  const game = useGameData(user);

  const [activeTab, setActiveTab] = useState('observatorium');
  const [selectedField, setSelectedField] = useState(null);
  const [targetCoordinates, setTargetCoordinates] = useState(null);
  const [showShipCalculator, setShowShipCalculator] = useState(false);

  useEffect(() => {
    if (targetCoordinates && activeTab === 'raumhafen') {
      setTimeout(() => {
        game.userFleets.forEach(fleet => {
          if (!fleet.movement_end_time) {
            const xInput = document.getElementById(`fleet-${fleet.id}-x`);
            const yInput = document.getElementById(`fleet-${fleet.id}-y`);
            if (xInput && yInput) {
              xInput.value = targetCoordinates.x;
              yInput.value = targetCoordinates.y;
            }
          }
        });
      }, 100);
    }
  }, [targetCoordinates, activeTab, game.userFleets]);

  const handleFieldClick = (x, y) => {
    setActiveTab('raumhafen');
    setTargetCoordinates({ x, y });
  };

  const handleSaveShipDesign = async (designData) => {
    const ok = await game.saveShipDesign(designData);
    if (ok) setShowShipCalculator(false);
  };

  const formatNextTick = () => {
    if (!game.gameState?.next_tick_time) return 'Unbekannt';
    const nextTick = new Date(game.gameState.next_tick_time);
    const diff = Math.max(0, Math.floor((nextTick - game.currentTime) / 1000));
    const minutes = Math.floor(diff / 60);
    const seconds = diff % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const formatTickDuration = () => {
    if (!game.gameState?.tick_duration) return '0:00';
    const duration = game.gameState.tick_duration;
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const totalResource = (key) => game.userPlanets.reduce((sum, p) => sum + p.resources[key], 0);

  return (
    <div className="game-layout starfield">
      <div className="game-header authentic-header">
        <div className="header-left">
          <div className="game-info">
            <div>Uhrzeit: {game.currentTime.toLocaleString('de-DE')}</div>
            <div>nexttick: {game.gameState?.next_tick_time ? new Date(game.gameState.next_tick_time).toLocaleString('de-DE') : 'Lade...'} ({formatNextTick()})</div>
            <div>Tickdauer: {formatTickDuration()}</div>
          </div>
        </div>

        <div className="header-center">
          <h1 className="game-title">TheReCreation</h1>
          <div className="game-subtitle">Runde 10 • Tick: {game.gameState?.current_tick || 0}</div>
        </div>

        <div className="header-right">
          <div className="user-resources">
            {game.userPlanets.length > 0 && (
              <div className="resource-display">
                <div className="resource-item">
                  <span className="resource-label">Nahrung</span>
                  <span className="resource-value resource-food">{totalResource('food').toLocaleString()}</span>
                </div>
                <div className="resource-item">
                  <span className="resource-label">Metall</span>
                  <span className="resource-value resource-metal">{totalResource('metal').toLocaleString()}</span>
                </div>
                <div className="resource-item">
                  <span className="resource-label">Wasserstoff</span>
                  <span className="resource-value resource-hydrogen">{totalResource('hydrogen').toLocaleString()}</span>
                </div>
              </div>
            )}
          </div>
          <button onClick={logout} className="logout-btn">Logout</button>
        </div>
      </div>

      <div className="game-main-layout">
        <div className="game-sidebar authentic-sidebar">
          <div className="sidebar-nav">
            {SIDEBAR_TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`sidebar-tab ${activeTab === tab.id ? 'active' : ''}`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="sidebar-actions">
            <button onClick={game.processTick} className="btn-primary">Tick verarbeiten</button>
          </div>
        </div>

        <div className="game-content">
          {activeTab === 'observatorium' && (
            <Observatory
              centerPosition={game.centerPosition}
              onPositionChange={game.setCenterPosition}
              view={game.observatoryView}
              onFieldClick={handleFieldClick}
              userFleets={game.userFleets}
              userPlanets={game.userPlanets}
              onNavigateToSpaceport={() => setActiveTab('raumhafen')}
            />
          )}

          {activeTab === 'raumhafen' && (
            <SpaceportTab
              spaceportShips={game.spaceportShips}
              userFleets={game.userFleets}
              shipDesigns={game.shipDesigns}
              battleReports={game.battleReports}
              debrisFields={game.debrisFields}
              targetCoordinates={targetCoordinates}
              setTargetCoordinates={setTargetCoordinates}
              onSetFleetStance={game.setFleetStance}
              onCollectDebris={game.collectDebris}
              onMoveFleet={game.moveFleet}
              onCreateFleet={game.createFleet}
            />
          )}

          {activeTab === 'werft' && (
            <ShipyardTab
              shipDesigns={game.shipDesigns}
              userPlanets={game.userPlanets}
              onShowCalculator={() => setShowShipCalculator(true)}
              onBuildShips={game.buildShips}
            />
          )}

          {activeTab === 'einrichtungen' && (
            <BuildingsTab
              userBuildings={game.userBuildings}
              userPlanets={game.userPlanets}
              onUpgrade={game.upgradeBuilding}
            />
          )}

          {activeTab === 'technologie' && (
            <ResearchTab
              userResearch={game.userResearch}
              researchCosts={game.researchCosts}
              onStartResearch={game.startResearch}
            />
          )}
        </div>

        {selectedField && (
          <div className="field-info-panel">
            <h4>Feld ({selectedField.x}:{selectedField.y})</h4>
            {selectedField.planet ? (
              <div className="planet-info">
                <h5>{selectedField.planet.name}</h5>
                <div>Typ: {selectedField.planet.planet_type}</div>
                {selectedField.planet.owner_username && (
                  <div>Besitzer: {selectedField.planet.owner_username}</div>
                )}
                <div className="planet-resources">
                  <div>🌾 {selectedField.planet.resources.food.toLocaleString()}</div>
                  <div>⚙️ {selectedField.planet.resources.metal.toLocaleString()}</div>
                  <div>⚡ {selectedField.planet.resources.hydrogen.toLocaleString()}</div>
                </div>
              </div>
            ) : (
              <div>Leerer Raum</div>
            )}

            {selectedField.fleets?.length > 0 && (
              <div className="fleets-info">
                <h5>Flotten ({selectedField.fleets.length})</h5>
                {selectedField.fleets.map((fleet, i) => (
                  <div key={i} className="fleet-info">
                    <div>{fleet.name}</div>
                    <div>von {fleet.username}</div>
                  </div>
                ))}
              </div>
            )}

            <button onClick={() => setSelectedField(null)} className="close-panel">×</button>
          </div>
        )}
      </div>

      {showShipCalculator && (
        <ShipDesignCalculator
          onClose={() => setShowShipCalculator(false)}
          onSave={handleSaveShipDesign}
          componentLevels={game.componentLevels}
          userResearch={game.userResearch}
        />
      )}
    </div>
  );
};

export default GameInterface;
