import React from 'react';
import { useToast } from '../../../hooks/use-toast';

const ShipyardTab = ({ shipDesigns, userPlanets, onShowCalculator, onBuildShips }) => {
  const { toast } = useToast();

  const handleBuild = async (designId) => {
    const planetSelect = document.getElementById(`planet-${designId}`);
    const quantityInput = document.getElementById(`quantity-${designId}`);

    const planetId = planetSelect.value;
    const quantity = parseInt(quantityInput.value);

    if (!planetId) {
      toast({ title: 'Fehler', description: 'Bitte wählen Sie einen Planeten', variant: 'destructive' });
      return;
    }
    if (!quantity || quantity < 1) {
      toast({ title: 'Fehler', description: 'Bitte geben Sie eine gültige Anzahl ein', variant: 'destructive' });
      return;
    }

    const ok = await onBuildShips(designId, planetId, quantity);
    if (ok) {
      planetSelect.value = '';
      quantityInput.value = '';
    }
  };

  return (
    <div className="werft-content">
      <div className="werft-header">
        <h3>Werft - Raumschiff-Prototypen</h3>
        <button onClick={onShowCalculator} className="btn-primary">
          Rechner - Prototypen entwerfen
        </button>
      </div>

      <div className="prototypes-list">
        <h4>Ihre Prototypen ({shipDesigns.length})</h4>
        {shipDesigns.map(design => (
          <div key={design.id} className="prototype-card">
            <h5>{design.name}</h5>
            <div className="prototype-stats">
              <div>Antrieb: {design.drive.component_name} (L{design.drive.level}) x{design.drive.quantity}</div>
              <div>Schild: {design.shield.component_name} (L{design.shield.level}) x{design.shield.quantity}</div>
              <div>Waffe: {design.weapon.component_name} (L{design.weapon.level}) x{design.weapon.quantity}</div>
              <div className="stats-row">
                <span>Geschwindigkeit: {design.calculated_stats.speed} pc/tick</span>
                <span>Kampfwert: {design.calculated_stats.combat_value}</span>
                {design.calculated_stats.mining_capacity > 0 &&
                  <span>Abbau: {design.calculated_stats.mining_capacity}/tick</span>}
                <span>Bauzeit: {design.calculated_stats.build_time_ticks} Ticks</span>
              </div>
            </div>

            <div className="production-section">
              <h6>Schiffe produzieren:</h6>
              <div className="production-controls">
                {userPlanets.length > 0 ? (
                  <div className="production-form">
                    <select id={`planet-${design.id}`} className="production-select">
                      <option value="">Planet wählen...</option>
                      {userPlanets.map(planet => (
                        <option key={planet.id} value={planet.id}>
                          {planet.name} ({planet.position.x}:{planet.position.y})
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      placeholder="Anzahl"
                      min="1"
                      max="1000"
                      id={`quantity-${design.id}`}
                      className="production-input"
                    />
                    <button onClick={() => handleBuild(design.id)} className="btn-success production-btn">
                      Im Raumhafen bauen
                    </button>
                  </div>
                ) : (
                  <p className="text-sm text-gray-400">Keine Planeten verfügbar für Produktion</p>
                )}
              </div>

              <div className="build-costs">
                <h6>Baukosten pro Schiff:</h6>
                <div className="cost-display">
                  <span className="resource-food">🌾 {design.calculated_stats.build_cost?.food || 0}</span>
                  <span className="resource-metal">⚙️ {design.calculated_stats.build_cost?.metal || 0}</span>
                  <span className="resource-hydrogen">⚡ {design.calculated_stats.build_cost?.hydrogen || 0}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ShipyardTab;
