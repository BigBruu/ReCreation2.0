import React from 'react';
import { useToast } from '../../../hooks/use-toast';

const SpaceportTab = ({
  spaceportShips,
  userFleets,
  shipDesigns,
  battleReports,
  debrisFields,
  targetCoordinates,
  setTargetCoordinates,
  onSetFleetStance,
  onCollectDebris,
  onMoveFleet,
  onCreateFleet,
}) => {
  const { toast } = useToast();

  const handleCreateFleet = (planetData) => {
    const fleetNameInput = document.getElementById(`fleet-name-${planetData.planet_id}`);
    const fleetName = fleetNameInput.value.trim();

    if (!fleetName) {
      toast({ title: 'Fehler', description: 'Bitte geben Sie einen Flottennamen ein', variant: 'destructive' });
      return;
    }

    const ships = [];
    for (const ship of planetData.ships) {
      const quantityInput = document.getElementById(`ship-${ship.id}-quantity`);
      const quantity = parseInt(quantityInput.value) || 0;
      if (quantity > 0) {
        ships.push({ design_id: ship.design_id, quantity });
      }
    }

    if (ships.length === 0) {
      toast({ title: 'Fehler', description: 'Bitte wählen Sie mindestens ein Schiff für die Flotte', variant: 'destructive' });
      return;
    }

    onCreateFleet(planetData.planet_id, fleetName, ships);
  };

  const handleMoveFleet = async (fleetId) => {
    const xInput = document.getElementById(`fleet-${fleetId}-x`);
    const yInput = document.getElementById(`fleet-${fleetId}-y`);
    const x = parseInt(xInput.value);
    const y = parseInt(yInput.value);
    const ok = await onMoveFleet(fleetId, x, y);
    if (ok) setTargetCoordinates(null);
  };

  return (
    <div className="spaceport-content">
      <h3>🚀 Raumhafen - Schiffe & Flotten</h3>

      <div className="spaceport-ships">
        <h4>Schiffe im Raumhafen</h4>
        {Object.keys(spaceportShips).length > 0 ? (
          Object.entries(spaceportShips).map(([planetKey, planetData]) => (
            <div key={planetKey} className="spaceport-planet">
              <h5>{planetData.planet_name} ({planetData.position.x}:{planetData.position.y})</h5>
              <div className="spaceport-ships-list">
                {planetData.ships.map(ship => (
                  <div key={ship.id} className="spaceport-ship">
                    <span className="ship-design">{ship.design_name}</span>
                    <span className="ship-quantity">x{ship.quantity}</span>
                    <span className="ship-date">{new Date(ship.created_at).toLocaleDateString('de-DE')}</span>
                  </div>
                ))}
              </div>

              <div className="fleet-creation">
                <h6>Flotte erstellen:</h6>
                <input
                  type="text"
                  placeholder="Flottenname"
                  id={`fleet-name-${planetData.planet_id}`}
                  className="fleet-name-input"
                />
                <div className="ship-selection">
                  {planetData.ships.map(ship => (
                    <div key={ship.id} className="ship-selector">
                      <label>{ship.design_name}:</label>
                      <input
                        type="number"
                        min="0"
                        max={ship.quantity}
                        defaultValue="0"
                        id={`ship-${ship.id}-quantity`}
                        className="ship-quantity-input"
                      />
                      <span className="max-available">/{ship.quantity}</span>
                    </div>
                  ))}
                </div>
                <button onClick={() => handleCreateFleet(planetData)} className="btn-primary create-fleet-btn">
                  Flotte erstellen
                </button>
              </div>
            </div>
          ))
        ) : (
          <p className="text-gray-400">Keine Schiffe im Raumhafen. Produzieren Sie Schiffe in der Werft.</p>
        )}
      </div>

      <div className="active-fleets">
        <h4>Aktive Flotten ({userFleets.length})</h4>
        {userFleets.map(fleet => (
          <div key={fleet.id} className={`fleet-card ${fleet.stance === 'aggressive' ? 'fleet-aggressive' : 'fleet-defensive'}`}>
            <h5>{fleet.name}{fleet.movement_end_time ? '*' : ''}</h5>
            <div className="fleet-position">Position: ({fleet.position.x}:{fleet.position.y})</div>

            <div className="fleet-stance">
              <label>Haltung:</label>
              <select
                value={fleet.stance || 'defensive'}
                onChange={(e) => onSetFleetStance(fleet.id, e.target.value)}
                className={`stance-select ${fleet.stance === 'aggressive' ? 'stance-aggressive' : 'stance-defensive'}`}
              >
                <option value="defensive">🛡️ Defensiv</option>
                <option value="aggressive">⚔️ Aggressiv</option>
              </select>
            </div>

            <div className="fleet-ships">
              {fleet.ships.map((shipGroup, i) => {
                const design = shipDesigns.find(d => d.id === shipGroup.design_id);
                return (
                  <div key={i} className="fleet-ship-group">
                    {design?.name || 'Unbekanntes Design'}: {shipGroup.quantity}
                  </div>
                );
              })}
            </div>
            <div className="fleet-stats">
              Geschwindigkeit: {fleet.fleet_speed} pc/tick
              {fleet.movement_end_time && (
                <div className="movement-info">
                  Ankunft: {new Date(fleet.movement_end_time).toLocaleString('de-DE')}
                </div>
              )}
            </div>

            {!fleet.movement_end_time && (
              <div className="fleet-movement">
                <h6>Flotte bewegen:</h6>
                <div className="movement-controls">
                  <input
                    type="number"
                    placeholder="X"
                    min="0"
                    max="46"
                    id={`fleet-${fleet.id}-x`}
                    className="coordinate-input"
                    key={`${fleet.id}-x-${targetCoordinates?.x || 'empty'}`}
                    defaultValue={targetCoordinates?.x || ''}
                  />
                  <span>:</span>
                  <input
                    type="number"
                    placeholder="Y"
                    min="0"
                    max="46"
                    id={`fleet-${fleet.id}-y`}
                    className="coordinate-input"
                    key={`${fleet.id}-y-${targetCoordinates?.y || 'empty'}`}
                    defaultValue={targetCoordinates?.y || ''}
                  />
                  <button onClick={() => handleMoveFleet(fleet.id)} className="btn-primary move-fleet-btn">
                    Bewegen
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {battleReports.length > 0 && (
        <div className="battle-reports-section">
          <h4>⚔️ Kampfberichte ({battleReports.length})</h4>
          <div className="battle-reports-list">
            {battleReports.slice(0, 5).map(report => (
              <div key={report.id} className={`battle-report ${report.winner === 'attacker' ? 'report-attacker-won' : 'report-defender-won'}`}>
                <div className="report-header">
                  <span className="report-tick">Tick {report.tick}</span>
                  <span className="report-position">({report.position.x}:{report.position.y})</span>
                </div>
                <div className="report-combatants">
                  <div className={`combatant attacker ${report.winner === 'attacker' ? 'winner' : 'loser'}`}>
                    <span className="combatant-name">⚔️ {report.attacker_username}</span>
                    <span className="combatant-fleet">{report.attacker_fleet_name}</span>
                    <span className="combatant-cv">KW: {report.attacker_combat_value}</span>
                    <span className="combatant-losses">
                      Verluste: {report.attacker_ships_lost.reduce((sum, s) => sum + s.quantity, 0)} Schiffe
                    </span>
                  </div>
                  <div className="vs">VS</div>
                  <div className={`combatant defender ${report.winner === 'defender' ? 'winner' : 'loser'}`}>
                    <span className="combatant-name">🛡️ {report.defender_username}</span>
                    <span className="combatant-fleet">{report.defender_fleet_name}</span>
                    <span className="combatant-cv">KW: {report.defender_combat_value}</span>
                    <span className="combatant-losses">
                      Verluste: {report.defender_ships_lost.reduce((sum, s) => sum + s.quantity, 0)} Schiffe
                    </span>
                  </div>
                </div>
                {report.debris_created && (
                  <div className="report-debris">
                    💥 Trümmerfeld: {report.debris_created.amount.toLocaleString()} {
                      report.debris_created.resource_type === 'food' ? 'Nahrung' :
                      report.debris_created.resource_type === 'metal' ? 'Metall' : 'Wasserstoff'
                    }
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {debrisFields.length > 0 && (
        <div className="debris-section">
          <h4>💥 Trümmerfelder ({debrisFields.length})</h4>
          <div className="debris-list">
            {debrisFields.map(debris => {
              const hasFleetAtPosition = userFleets.some(
                f => f.position.x === debris.position.x &&
                     f.position.y === debris.position.y &&
                     !f.movement_end_time
              );
              return (
                <div key={debris.id} className="debris-card">
                  <div className="debris-position">({debris.position.x}:{debris.position.y})</div>
                  <div className="debris-amount">
                    {debris.resource_type === 'food' && '🌾'}
                    {debris.resource_type === 'metal' && '⚙️'}
                    {debris.resource_type === 'hydrogen' && '⚡'}
                    {' '}{debris.amount.toLocaleString()} {
                      debris.resource_type === 'food' ? 'Nahrung' :
                      debris.resource_type === 'metal' ? 'Metall' : 'Wasserstoff'
                    }
                  </div>
                  {hasFleetAtPosition ? (
                    <button onClick={() => onCollectDebris(debris.id)} className="btn-success collect-btn">
                      Sammeln
                    </button>
                  ) : (
                    <span className="no-fleet-warning">Keine Flotte vor Ort</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default SpaceportTab;
