import React from 'react';

const UsersTab = ({ users, onDeleteUser }) => (
  <div className="space-y-6">
    <h2 className="text-xl font-bold">Spielerverwaltung ({users.length})</h2>
    <div className="bg-gray-800 rounded border border-gray-700 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="px-4 py-2 text-left">Spielername</th>
              <th className="px-4 py-2 text-left">E-Mail</th>
              <th className="px-4 py-2 text-left">Planeten</th>
              <th className="px-4 py-2 text-left">Flotten</th>
              <th className="px-4 py-2 text-left">Registriert</th>
              <th className="px-4 py-2 text-left">Aktionen</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id} className="border-t border-gray-700">
                <td className="px-4 py-2 font-semibold">{user.username}</td>
                <td className="px-4 py-2 text-sm text-gray-400">{user.email}</td>
                <td className="px-4 py-2">{user.planets}</td>
                <td className="px-4 py-2">{user.fleets}</td>
                <td className="px-4 py-2 text-sm">
                  {new Date(user.created_at).toLocaleDateString('de-DE')}
                </td>
                <td className="px-4 py-2">
                  <button
                    onClick={() => onDeleteUser(user.id, user.username)}
                    className="bg-red-600 hover:bg-red-700 px-2 py-1 rounded text-xs"
                  >
                    Löschen
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

export default UsersTab;
