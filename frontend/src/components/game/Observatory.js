import React from 'react';

const PLANET_COLORS = {
  green: { core: '#22c55e', edge: '#14532d', label: '#86efac' },
  blue: { core: '#3b82f6', edge: '#1e3a8a', label: '#93c5fd' },
  brown: { core: '#d97706', edge: '#78350f', label: '#fcd34d' },
  orange: { core: '#fb923c', edge: '#7c2d12', label: '#fdba74' },
};

const PlanetSprite = ({ type, size = 38 }) => {
  const c = PLANET_COLORS[type] || PLANET_COLORS.green;
  const r = size / 2;
  const isRinged = type === 'orange';
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="planet-sprite">
      <defs>
        <radialGradient id={`grad-${type}`} cx="35%" cy="30%" r="70%">
          <stop offset="0%" stopColor={c.core} stopOpacity="1" />
          <stop offset="60%" stopColor={c.core} stopOpacity="0.95" />
          <stop offset="100%" stopColor={c.edge} stopOpacity="1" />
        </radialGradient>
        <radialGradient id={`glow-${type}`} cx="50%" cy="50%" r="50%">
          <stop offset="60%" stopColor={c.core} stopOpacity="0.25" />
          <stop offset="100%" stopColor={c.core} stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx={r} cy={r} r={r} fill={`url(#glow-${type})`} />
      {isRinged && (
        <ellipse
          cx={r}
          cy={r}
          rx={r * 0.95}
          ry={r * 0.25}
          fill="none"
          stroke={c.label}
          strokeWidth="1.5"
          opacity="0.85"
          transform={`rotate(-18 ${r} ${r})`}
        />
      )}
      <circle cx={r} cy={r} r={r * 0.62} fill={`url(#grad-${type})`} />
      {isRinged && (
        <ellipse
          cx={r}
          cy={r}
          rx={r * 0.95}
          ry={r * 0.25}
          fill="none"
          stroke={c.label}
          strokeWidth="1.5"
          opacity="0.85"
          strokeDasharray="22 100"
          strokeDashoffset="-46"
          transform={`rotate(-18 ${r} ${r})`}
        />
      )}
    </svg>
  );
};

const Observatory = ({
  centerPosition,
  onPositionChange,
  view,
  onFieldClick,
  userFleets = [],
  userPlanets = [],
  onNavigateToSpaceport,
  currentUsername,
}) => {
  const renderField = (x, y) => {
    const key = `${x},${y}`;
    const fieldData = view[key] || { planet: null, fleets: [] };
    const { planet, fleets } = fieldData;

    const centerX = Math.floor(centerPosition.x);
    const centerY = Math.floor(centerPosition.y);
    const isCenter = x === centerX && y === centerY;

    let ownership = 'neutral';
    if (planet && planet.owner_username) {
      ownership = planet.owner_username === currentUsername ? 'own' : 'enemy';
    }

    const dominantResource = planet
      ? Math.max(planet.resources.food, planet.resources.metal, planet.resources.hydrogen)
      : 0;

    const labelColorClass =
      ownership === 'own' ? 'label-own' : ownership === 'enemy' ? 'label-enemy' : 'label-neutral';

    return (
      <div
        key={key}
        className={`obs-cell ${planet ? 'has-planet' : 'empty'} ${isCenter ? 'center-cell' : ''}`}
        onClick={() => onFieldClick(x, y, fieldData)}
        title={`(${x}:${y}) ${planet ? planet.name : 'Leerer Raum'}${
          fleets.length ? ` - ${fleets.length} Flotte(n)` : ''
        }`}
      >
        <div className="obs-coord">{x}:{y}</div>

        {planet && (
          <div className={`obs-planet-wrap owner-${ownership}`}>
            <div className={`obs-label obs-label-top ${labelColorClass}`}>
              {planet.owner_username || planet.name}
            </div>
            <PlanetSprite type={planet.planet_type} />
            <div className={`obs-label obs-label-bottom ${labelColorClass}`}>
              {dominantResource.toLocaleString('de-DE')}
            </div>
          </div>
        )}

        {fleets.length > 0 && (
          <div className="obs-fleets">
            {fleets.slice(0, 3).map((fleet, i) => (
              <span key={i} className="obs-fleet-tag" title={fleet.name}>
                F.{i + 1}
                {fleet.movement_end_time ? '*' : ''}
              </span>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="observatory-container">
      <div className="observatory-header">
        <h3>Observatorium</h3>
        <div className="observatory-controls">
          <div className="fleet-selector">
            <label>Zu Flotte springen:</label>
            <select
              onChange={(e) => {
                if (e.target.value) {
                  const fleet = userFleets.find((f) => f.id === e.target.value);
                  if (fleet) {
                    onPositionChange({ x: fleet.position.x, y: fleet.position.y });
                  }
                }
              }}
              value=""
              className="fleet-select"
            >
              <option value="">Flotte wählen...</option>
              {userFleets.map((fleet) => (
                <option key={fleet.id} value={fleet.id}>
                  {fleet.name} ({fleet.position.x}:{fleet.position.y})
                  {fleet.movement_end_time ? '*' : ''}
                </option>
              ))}
            </select>
            <button
              onClick={() => {
                if (userPlanets.length > 0) {
                  const sp = userPlanets[0];
                  onPositionChange({ x: sp.position.x, y: sp.position.y });
                  if (onNavigateToSpaceport) onNavigateToSpaceport();
                }
              }}
              className="btn-secondary spaceport-btn"
            >
              🚀 Raumhafen
            </button>
          </div>
          <div className="current-coordinates">
            ({centerPosition.x}:{centerPosition.y})
          </div>
        </div>
      </div>

      <div className="obs-starfield">
        <div className="obs-grid">
          <div className="obs-row obs-header-row">
            <div className="obs-axis-corner"></div>
            {Array.from({ length: 7 }, (_, col) => {
              const x = centerPosition.x - 3 + col;
              return (
                <div key={col} className="obs-col-label">
                  {x}
                </div>
              );
            })}
          </div>

          {Array.from({ length: 7 }, (_, row) => {
            const y = centerPosition.y - 3 + row;
            return (
              <div key={row} className="obs-row">
                <div className="obs-row-label">{y}</div>
                {Array.from({ length: 7 }, (_, col) => {
                  const x = centerPosition.x - 3 + col;
                  if (x >= 0 && x < 47 && y >= 0 && y < 47) {
                    return renderField(x, y);
                  }
                  return <div key={col} className="obs-cell empty" />;
                })}
              </div>
            );
          })}
        </div>
      </div>

      <div className="observatory-legend">
        <div className="legend-item">
          <PlanetSprite type="green" size={16} />
          <span>Nahrung</span>
        </div>
        <div className="legend-item">
          <PlanetSprite type="blue" size={16} />
          <span>Wasserstoff</span>
        </div>
        <div className="legend-item">
          <PlanetSprite type="brown" size={16} />
          <span>Metall</span>
        </div>
        <div className="legend-item">
          <PlanetSprite type="orange" size={16} />
          <span>Wasserstoff</span>
        </div>
      </div>
    </div>
  );
};

export default Observatory;
