import React from 'react';

const codeStatusClass = (code) => {
  if (code.current_uses >= code.max_uses) return 'bg-red-600';
  if (code.expires_at && new Date(code.expires_at) < new Date()) return 'bg-orange-600';
  return 'bg-green-600';
};

const codeStatusLabel = (code) => {
  if (code.current_uses >= code.max_uses) return 'Aufgebraucht';
  if (code.expires_at && new Date(code.expires_at) < new Date()) return 'Abgelaufen';
  return 'Aktiv';
};

const InvitesTab = ({ inviteCodes, loading, onCreateInviteCode }) => (
  <div className="space-y-6">
    <h2 className="text-xl font-bold">Einladungscodes</h2>
    <div className="flex space-x-4">
      <button
        onClick={() => onCreateInviteCode(1, 24)}
        disabled={loading}
        className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-4 py-2 rounded"
      >
        1x Code (24h)
      </button>
      <button
        onClick={() => onCreateInviteCode(5, 168)}
        disabled={loading}
        className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-4 py-2 rounded"
      >
        5x Code (7 Tage)
      </button>
      <button
        onClick={() => onCreateInviteCode(1, null)}
        disabled={loading}
        className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-4 py-2 rounded"
      >
        Permanent
      </button>
    </div>
    <div className="bg-gray-800 rounded border border-gray-700 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="px-4 py-2 text-left">Code</th>
              <th className="px-4 py-2 text-left">Verwendet</th>
              <th className="px-4 py-2 text-left">Benutzer</th>
              <th className="px-4 py-2 text-left">Läuft ab</th>
              <th className="px-4 py-2 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {inviteCodes.map(code => (
              <tr key={code.id} className="border-t border-gray-700">
                <td className="px-4 py-2 font-mono font-bold text-green-400">{code.code}</td>
                <td className="px-4 py-2">{code.current_uses}/{code.max_uses}</td>
                <td className="px-4 py-2 text-sm">{code.used_by_username || '-'}</td>
                <td className="px-4 py-2 text-sm">
                  {code.expires_at ? new Date(code.expires_at).toLocaleDateString('de-DE') : 'Nie'}
                </td>
                <td className="px-4 py-2">
                  <span className={`px-2 py-1 rounded text-xs ${codeStatusClass(code)}`}>
                    {codeStatusLabel(code)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

export default InvitesTab;
