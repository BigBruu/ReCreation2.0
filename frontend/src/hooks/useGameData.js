import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API, getAuthHeaders } from '../lib/api';
import { useToast } from './use-toast';

export function useGameData(user) {
  const { toast } = useToast();

  const [gameState, setGameState] = useState(null);
  const [observatoryView, setObservatoryView] = useState({});
  const [centerPosition, setCenterPosition] = useState({ x: 23, y: 23 });
  const [userPlanets, setUserPlanets] = useState([]);
  const [userFleets, setUserFleets] = useState([]);
  const [shipDesigns, setShipDesigns] = useState([]);
  const [spaceportShips, setSpaceportShips] = useState({});
  const [userResearch, setUserResearch] = useState(null);
  const [researchCosts, setResearchCosts] = useState(null);
  const [componentLevels, setComponentLevels] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [userBuildings, setUserBuildings] = useState([]);
  const [battleReports, setBattleReports] = useState([]);
  const [debrisFields, setDebrisFields] = useState([]);
  const [currentTime, setCurrentTime] = useState(new Date());

  const fetchGameData = useCallback(async () => {
    try {
      const headers = getAuthHeaders();
      const [
        gameStateRes, planetsRes, fleetsRes, designsRes, componentRes, rankingsRes,
        researchRes, costsRes, spaceportRes, buildingsRes, battleReportsRes, debrisRes
      ] = await Promise.all([
        axios.get(`${API}/game/state`, { headers }),
        axios.get(`${API}/game/planets`, { headers }),
        axios.get(`${API}/game/fleets`, { headers }),
        axios.get(`${API}/game/ship-designs`, { headers }),
        axios.get(`${API}/game/component-levels`, { headers }),
        axios.get(`${API}/game/rankings`, { headers }),
        axios.get(`${API}/game/research`, { headers }),
        axios.get(`${API}/game/research/costs`, { headers }),
        axios.get(`${API}/game/spaceport-ships`, { headers }),
        axios.get(`${API}/game/buildings`, { headers }),
        axios.get(`${API}/game/battle-reports`, { headers }),
        axios.get(`${API}/game/debris-fields`, { headers }),
      ]);

      setGameState(gameStateRes.data);
      setUserPlanets(planetsRes.data);
      setUserFleets(fleetsRes.data);
      setShipDesigns(designsRes.data);
      setComponentLevels(componentRes.data);
      setRankings(rankingsRes.data);
      setUserResearch(researchRes.data);
      setResearchCosts(costsRes.data);
      setSpaceportShips(spaceportRes.data);
      setUserBuildings(buildingsRes.data);
      setBattleReports(battleReportsRes.data);
      setDebrisFields(debrisRes.data);
    } catch (error) {
      console.error('Failed to fetch game data:', error);
    }
  }, []);

  const fetchObservatoryView = useCallback(async () => {
    try {
      const response = await axios.post(
        `${API}/game/observatory`,
        { center_x: centerPosition.x, center_y: centerPosition.y },
        { headers: getAuthHeaders() }
      );
      setObservatoryView(response.data.view);
    } catch (error) {
      console.error('Failed to fetch observatory view:', error);
    }
  }, [centerPosition]);

  useEffect(() => {
    fetchGameData();
    const interval = setInterval(fetchGameData, 15000);
    return () => clearInterval(interval);
  }, [fetchGameData]);

  useEffect(() => {
    const clockInterval = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(clockInterval);
  }, []);

  useEffect(() => {
    if (user?.spaceport_position && user.spaceport_position.x !== -1) {
      setCenterPosition(user.spaceport_position);
    }
  }, [user]);

  useEffect(() => {
    if (centerPosition.x !== -1) {
      fetchObservatoryView();
    }
  }, [centerPosition, fetchObservatoryView]);

  const handleError = (error, fallback) => {
    toast({
      title: 'Fehler',
      description: error.response?.data?.detail || fallback,
      variant: 'destructive',
    });
  };

  const processTick = async () => {
    try {
      await axios.post(`${API}/game/tick`, {}, { headers: getAuthHeaders() });
      toast({ title: 'Erfolg', description: 'Tick verarbeitet!' });
      fetchGameData();
    } catch (error) {
      handleError(error, 'Fehler beim Verarbeiten des Ticks');
    }
  };

  const saveShipDesign = async (designData) => {
    try {
      await axios.post(`${API}/game/ship-design`, designData, { headers: getAuthHeaders() });
      toast({ title: 'Erfolg', description: 'Prototyp erstellt!' });
      fetchGameData();
      return true;
    } catch (error) {
      handleError(error, 'Fehler beim Erstellen des Prototyps');
      return false;
    }
  };

  const buildShips = async (designId, planetId, quantity) => {
    try {
      await axios.post(
        `${API}/game/build-ships`,
        { planet_id: planetId, design_id: designId, quantity },
        { headers: getAuthHeaders() }
      );
      toast({ title: 'Erfolg', description: `${quantity} Schiffe im Raumhafen produziert!` });
      fetchGameData();
      return true;
    } catch (error) {
      handleError(error, 'Schiffsproduktion fehlgeschlagen');
      return false;
    }
  };

  const startResearch = async (category, technology) => {
    try {
      const response = await axios.post(
        `${API}/game/research/start`,
        { category, technology },
        { headers: getAuthHeaders() }
      );
      toast({
        title: 'Forschung gestartet!',
        description: `${technology} wird erforscht. Kosten: ${response.data.cost.toLocaleString()} Nahrung`,
      });
      fetchGameData();
    } catch (error) {
      handleError(error, 'Forschung konnte nicht gestartet werden');
    }
  };

  const upgradeBuilding = async (buildingType) => {
    try {
      const response = await axios.post(
        `${API}/game/buildings/upgrade`,
        { building_type: buildingType },
        { headers: getAuthHeaders() }
      );
      toast({ title: 'Ausbau gestartet!', description: response.data.message });
      fetchGameData();
    } catch (error) {
      handleError(error, 'Gebäude konnte nicht ausgebaut werden');
    }
  };

  const setFleetStance = async (fleetId, stance) => {
    try {
      await axios.post(
        `${API}/game/fleet/stance`,
        { fleet_id: fleetId, stance },
        { headers: getAuthHeaders() }
      );
      toast({
        title: 'Erfolg!',
        description: `Flotten-Haltung auf "${stance === 'aggressive' ? 'Aggressiv' : 'Defensiv'}" gesetzt`,
      });
      fetchGameData();
    } catch (error) {
      handleError(error, 'Haltung konnte nicht geändert werden');
    }
  };

  const collectDebris = async (debrisId) => {
    try {
      const response = await axios.post(
        `${API}/game/collect-debris?debris_id=${debrisId}`,
        {},
        { headers: getAuthHeaders() }
      );
      toast({ title: 'Trümmer gesammelt!', description: response.data.message });
      fetchGameData();
    } catch (error) {
      handleError(error, 'Trümmer konnten nicht gesammelt werden');
    }
  };

  const moveFleet = async (fleetId, x, y) => {
    if (isNaN(x) || isNaN(y) || x < 0 || x > 46 || y < 0 || y > 46) {
      toast({
        title: 'Fehler',
        description: 'Bitte geben Sie gültige Koordinaten ein (0-46)',
        variant: 'destructive',
      });
      return false;
    }
    try {
      await axios.post(
        `${API}/game/move-fleet`,
        { fleet_id: fleetId, target_position: { x, y } },
        { headers: getAuthHeaders() }
      );
      toast({ title: 'Erfolg', description: `Flotte bewegt sich zu (${x}:${y})!` });
      fetchGameData();
      return true;
    } catch (error) {
      handleError(error, 'Flottenbewegung fehlgeschlagen');
      return false;
    }
  };

  const createFleet = async (planetId, fleetName, ships) => {
    try {
      await axios.post(
        `${API}/game/create-fleet`,
        { planet_id: planetId, fleet_name: fleetName, ships },
        { headers: getAuthHeaders() }
      );
      toast({ title: 'Erfolg', description: `Flotte "${fleetName}" erstellt!` });
      fetchGameData();
      return true;
    } catch (error) {
      handleError(error, 'Flottenerstellung fehlgeschlagen');
      return false;
    }
  };

  return {
    gameState, observatoryView, centerPosition, setCenterPosition,
    userPlanets, userFleets, shipDesigns, spaceportShips, userResearch, researchCosts,
    componentLevels, rankings, userBuildings, battleReports, debrisFields, currentTime,
    fetchGameData,
    processTick, saveShipDesign, buildShips, startResearch, upgradeBuilding,
    setFleetStance, collectDebris, moveFleet, createFleet,
  };
}
