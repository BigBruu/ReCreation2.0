import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../hooks/use-toast';
import { API, getAuthHeaders } from '../lib/api';
import DashboardTab from './admin/tabs/DashboardTab';
import NewRoundTab from './admin/tabs/NewRoundTab';
import ConfigTab from './admin/tabs/ConfigTab';
import UsersTab from './admin/tabs/UsersTab';
import InvitesTab from './admin/tabs/InvitesTab';
import ActionsTab from './admin/tabs/ActionsTab';

const DEFAULT_NEW_ROUND = {
  resources_per_planet: 50000000,
  planet_count: 180,
  universe_size: 47,
  tick_duration: 60,
  max_players: 20,
};

const SIDEBAR_TABS = [
  { id: 'dashboard',  label: 'Dashboard',     icon: '📊' },
  { id: 'neue-runde', label: 'Neue Runde',    icon: '🚀' },
  { id: 'config',     label: 'Konfiguration', icon: '⚙️' },
  { id: 'users',      label: 'Spieler',       icon: '👥' },
  { id: 'invites',    label: 'Einladungen',   icon: '🎫' },
  { id: 'actions',    label: 'Aktionen',      icon: '🛠️' },
];

const AdminPanel = () => {
  const { logout } = useAuth();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [config, setConfig] = useState(null);
  const [users, setUsers] = useState([]);
  const [inviteCodes, setInviteCodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newRound, setNewRound] = useState(DEFAULT_NEW_ROUND);
  const [newRoundResult, setNewRoundResult] = useState(null);

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    try {
      const headers = getAuthHeaders();
      const [statsRes, configRes, usersRes, codesRes] = await Promise.all([
        axios.get(`${API}/admin/stats`, { headers }),
        axios.get(`${API}/admin/config`, { headers }),
        axios.get(`${API}/admin/users`, { headers }),
        axios.get(`${API}/admin/invite-codes`, { headers }),
      ]);
      setStats(statsRes.data);
      setConfig(configRes.data);
      setUsers(usersRes.data);
      setInviteCodes(codesRes.data);
    } catch (error) {
      toast({ title: 'Fehler', description: 'Admin-Daten konnten nicht geladen werden', variant: 'destructive' });
    }
  };

  const createInviteCode = async (maxUses = 1, expiresInHours = 24) => {
    try {
      setLoading(true);
      const response = await axios.post(
        `${API}/admin/invite-codes`,
        { max_uses: maxUses, expires_in_hours: expiresInHours },
        { headers: getAuthHeaders() }
      );
      toast({ title: 'Erfolg', description: `Einladungscode erstellt: ${response.data.code}` });
      fetchAdminData();
    } catch (error) {
      toast({ title: 'Fehler', description: 'Code konnte nicht erstellt werden', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const deleteUser = async (userId, username) => {
    if (!window.confirm(`Spieler "${username}" wirklich löschen?`)) return;
    try {
      await axios.delete(`${API}/admin/users/${userId}`, { headers: getAuthHeaders() });
      toast({ title: 'Erfolg', description: `Spieler "${username}" gelöscht` });
      fetchAdminData();
    } catch (error) {
      toast({ title: 'Fehler', description: 'Spieler konnte nicht gelöscht werden', variant: 'destructive' });
    }
  };

  const resetGame = async () => {
    if (!window.confirm('ACHTUNG: Spiel komplett zurücksetzen? Alle Spieler und Daten werden gelöscht!')) return;
    try {
      await axios.post(`${API}/admin/reset-game`, {}, { headers: getAuthHeaders() });
      toast({ title: 'Erfolg', description: 'Spiel wurde zurückgesetzt' });
      fetchAdminData();
    } catch (error) {
      toast({ title: 'Fehler', description: 'Spiel konnte nicht zurückgesetzt werden', variant: 'destructive' });
    }
  };

  const startNewRound = async () => {
    if (!window.confirm(
      `ACHTUNG: Neue Runde starten?\n\n` +
      `Spielfeld: ${newRound.universe_size}x${newRound.universe_size}\n` +
      `Planeten: ${newRound.planet_count}\n` +
      `Ressourcen/Planet: ${Number(newRound.resources_per_planet).toLocaleString('de-DE')}\n` +
      `Tick-Dauer: ${newRound.tick_duration}s\n` +
      `Max. Spieler: ${newRound.max_players}\n\n` +
      `Alle aktuellen Daten (Spieler, Planeten, Flotten) werden gelöscht!`
    )) return;

    try {
      setLoading(true);
      setNewRoundResult(null);
      const response = await axios.post(
        `${API}/admin/new-round`,
        {
          resources_per_planet: Number(newRound.resources_per_planet),
          planet_count:         Number(newRound.planet_count),
          universe_size:        Number(newRound.universe_size),
          tick_duration:        Number(newRound.tick_duration),
          max_players:          Number(newRound.max_players),
        },
        { headers: getAuthHeaders() }
      );
      setNewRoundResult(response.data);
      toast({ title: 'Erfolg', description: response.data.message });
      fetchAdminData();
    } catch (error) {
      const detail = error.response?.data?.detail || 'Neue Runde konnte nicht gestartet werden';
      toast({ title: 'Fehler', description: detail, variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const updateConfig = async (newConfig) => {
    try {
      await axios.post(`${API}/admin/config`, newConfig, { headers: getAuthHeaders() });
      toast({ title: 'Erfolg', description: 'Konfiguration aktualisiert' });
      fetchAdminData();
    } catch (error) {
      toast({ title: 'Fehler', description: 'Konfiguration konnte nicht aktualisiert werden', variant: 'destructive' });
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="bg-red-900 border-b-2 border-red-500 p-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-red-400">TheReCreation - Admin Panel</h1>
            <p className="text-sm text-gray-400">Vollzugriff auf Spielkonfiguration</p>
          </div>
          <button onClick={logout} className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded">
            Logout
          </button>
        </div>
      </div>

      <div className="flex">
        <div className="w-64 bg-gray-900 border-r-2 border-red-500 h-screen p-4">
          <div className="space-y-2">
            {SIDEBAR_TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full text-left p-3 rounded transition-colors ${
                  activeTab === tab.id ? 'bg-red-600' : 'bg-gray-800 hover:bg-gray-700'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 p-6">
          {activeTab === 'dashboard' && <DashboardTab stats={stats} />}
          {activeTab === 'neue-runde' && (
            <NewRoundTab
              newRound={newRound}
              setNewRound={setNewRound}
              loading={loading}
              newRoundResult={newRoundResult}
              onStartNewRound={startNewRound}
            />
          )}
          {activeTab === 'config' && (
            <ConfigTab config={config} setConfig={setConfig} onSave={updateConfig} />
          )}
          {activeTab === 'users' && <UsersTab users={users} onDeleteUser={deleteUser} />}
          {activeTab === 'invites' && (
            <InvitesTab inviteCodes={inviteCodes} loading={loading} onCreateInviteCode={createInviteCode} />
          )}
          {activeTab === 'actions' && <ActionsTab onResetGame={resetGame} />}
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
