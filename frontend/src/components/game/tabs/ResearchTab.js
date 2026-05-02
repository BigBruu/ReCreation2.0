import React from 'react';

const CATEGORY_LABELS = {
  drives: '🚀 Antriebe',
  shields: '🛡️ Schilde',
  weapons: '⚔️ Waffen',
};

const calculateResearchCost = (baseCost, currentLevel) => {
  const reductionFactor = Math.pow(0.85, currentLevel);
  return Math.floor(baseCost * reductionFactor * (currentLevel + 1));
};

const ResearchTab = ({ userResearch, researchCosts, onStartResearch }) => {
  const anyResearching = userResearch?.research_levels.some(r => r.researching);

  return (
    <div className="research-content">
      <h3>Forschung - Alle starten bei Level 0</h3>
      <div className="research-categories">
        {['drives', 'shields', 'weapons'].map(category => (
          <div key={category} className="research-category">
            <h4>{CATEGORY_LABELS[category]}</h4>
            <div className="research-techs">
              {userResearch?.research_levels
                .filter(tech => tech.category === category)
                .map(tech => {
                  const baseCost = researchCosts?.[category]?.[tech.technology]?.base_cost || 0;
                  const actualCost = calculateResearchCost(baseCost, tech.level);

                  return (
                    <div key={tech.technology} className="research-tech">
                      <div className="tech-header">
                        <span className="tech-name">
                          {tech.technology.charAt(0).toUpperCase() + tech.technology.slice(1)}
                        </span>
                        <span className="tech-level">Level {tech.level}</span>
                      </div>

                      <div className="tech-details">
                        <div className="tech-cost">
                          Kosten: <span className="resource-food">{actualCost.toLocaleString()} Nahrung</span>
                        </div>
                        {tech.level > 0 && (
                          <div className="tech-reduction">15% Kostenreduktion erreicht</div>
                        )}
                      </div>

                      {tech.researching ? (
                        <div className="research-progress">
                          <span className="researching-indicator">🔬 Erforscht...</span>
                          <div className="research-time">
                            Fertig: {tech.research_end_time
                              ? new Date(tech.research_end_time).toLocaleString('de-DE')
                              : 'Berechne...'}
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => onStartResearch(category, tech.technology)}
                          className="btn-primary research-btn"
                          disabled={anyResearching}
                        >
                          Erforschen
                        </button>
                      )}
                    </div>
                  );
                })}
            </div>
          </div>
        ))}
      </div>

      <div className="research-info">
        <h4>📚 Forschungs-Regeln:</h4>
        <ul>
          <li>• Alle Technologien starten bei Level 0</li>
          <li>• Nur eine Forschung gleichzeitig möglich</li>
          <li>• Kostenverringerung pro Level: 15%</li>
          <li>• Forschung kostet nur Nahrung</li>
          <li>• Forschungszeit steigt mit Level</li>
        </ul>
      </div>
    </div>
  );
};

export default ResearchTab;
