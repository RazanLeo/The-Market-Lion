'use client';
import { useState, useEffect, useCallback } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const AUTH = process.env.NEXT_PUBLIC_AUTH_URL || 'http://localhost:8001';
const USER_SVC = process.env.NEXT_PUBLIC_USER_SVC_URL || 'http://localhost:8011';

interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  plan: string;
  status: string;
  is_2fa_enabled: boolean;
  kyc_status: string;
  created_at: string;
  last_login: string;
  total_referrals: number;
}

interface AdminStats {
  total_users: number;
  active_users: number;
  pro_users: number;
  vip_users: number;
  kyc_pending: number;
  total_referrals: number;
}

const PLAN_COLORS: Record<string, string> = {
  free: 'text-gray-400',
  starter: 'text-blue-400',
  pro: 'text-green-400',
  vip: 'text-yellow-400',
  enterprise: 'text-purple-400',
};

const STATUS_COLORS: Record<string, string> = {
  active: 'text-green-400',
  suspended: 'text-red-400',
  pending: 'text-yellow-400',
};

export default function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string>('');
  const [search, setSearch] = useState('');
  const [tab, setTab] = useState<'users' | 'kyc' | 'stats' | 'system'>('stats');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [planModal, setPlanModal] = useState(false);
  const [newPlan, setNewPlan] = useState('');
  const [actionMsg, setActionMsg] = useState('');
  const [systemHealth, setSystemHealth] = useState<Record<string, string>>({});

  useEffect(() => {
    const stored = localStorage.getItem('access_token') || '';
    setToken(stored);
  }, []);

  const authHeaders = useCallback(() => ({
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }), [token]);

  const fetchStats = useCallback(async () => {
    if (!token) return;
    try {
      const r = await fetch(`${USER_SVC}/admin/stats`, { headers: authHeaders() });
      if (r.ok) setStats(await r.json());
    } catch {}
  }, [token, authHeaders]);

  const fetchUsers = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const r = await fetch(`${USER_SVC}/admin/users?limit=100`, { headers: authHeaders() });
      if (r.ok) {
        const data = await r.json();
        setUsers(data.users || data || []);
      }
    } catch {}
    setLoading(false);
  }, [token, authHeaders]);

  const checkSystemHealth = useCallback(async () => {
    const services: Record<string, string> = {
      Gateway: `${API}/api/v1/health`,
      Auth: `${AUTH}/auth/health`,
      Users: `${USER_SVC}/health`,
    };
    const results: Record<string, string> = {};
    for (const [name, url] of Object.entries(services)) {
      try {
        const r = await fetch(url, { signal: AbortSignal.timeout(3000) });
        results[name] = r.ok ? '🟢 صحي' : '🟡 خطأ';
      } catch {
        results[name] = '🔴 غير متاح';
      }
    }
    setSystemHealth(results);
  }, [API, AUTH, USER_SVC]);

  useEffect(() => {
    if (!token) return;
    fetchStats();
    fetchUsers();
    checkSystemHealth();
  }, [token, fetchStats, fetchUsers, checkSystemHealth]);

  const updateUserPlan = async (userId: string, plan: string) => {
    try {
      const r = await fetch(`${USER_SVC}/admin/users/${userId}/plan`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify({ plan }),
      });
      if (r.ok) {
        setActionMsg(`✅ تم تحديث الخطة إلى ${plan}`);
        fetchUsers();
        fetchStats();
      } else {
        setActionMsg('❌ فشل تحديث الخطة');
      }
    } catch {
      setActionMsg('❌ خطأ في الاتصال');
    }
    setPlanModal(false);
    setTimeout(() => setActionMsg(''), 3000);
  };

  const updateUserStatus = async (userId: string, status: string) => {
    try {
      const r = await fetch(`${USER_SVC}/admin/users/${userId}/status`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify({ status }),
      });
      if (r.ok) {
        setActionMsg(`✅ تم تحديث الحالة`);
        fetchUsers();
      }
    } catch {}
    setTimeout(() => setActionMsg(''), 3000);
  };

  const filteredUsers = users.filter(u =>
    u.email?.toLowerCase().includes(search.toLowerCase()) ||
    u.username?.toLowerCase().includes(search.toLowerCase()) ||
    u.full_name?.toLowerCase().includes(search.toLowerCase())
  );

  const kycPending = users.filter(u => u.kyc_status === 'pending');

  return (
    <div className="min-h-screen bg-gray-950 text-white font-mono">
      {/* Header */}
      <div className="bg-gray-900 border-b border-yellow-500/30 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🦁</span>
          <div>
            <h1 className="text-yellow-400 font-bold text-lg">أسد السوق — لوحة الإدارة</h1>
            <p className="text-gray-400 text-xs">The Market Lion Admin Panel</p>
          </div>
        </div>
        {actionMsg && (
          <div className="bg-gray-800 border border-yellow-500/40 px-4 py-2 rounded text-sm">
            {actionMsg}
          </div>
        )}
      </div>

      <div className="flex">
        {/* Sidebar */}
        <div className="w-48 bg-gray-900 border-r border-gray-800 min-h-screen p-4 space-y-2">
          {[
            { key: 'stats', label: '📊 الإحصاءات' },
            { key: 'users', label: '👥 المستخدمون' },
            { key: 'kyc', label: `🪪 KYC ${kycPending.length > 0 ? `(${kycPending.length})` : ''}` },
            { key: 'system', label: '⚙️ النظام' },
          ].map(item => (
            <button
              key={item.key}
              onClick={() => setTab(item.key as typeof tab)}
              className={`w-full text-right px-3 py-2 rounded text-sm transition-colors ${
                tab === item.key
                  ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40'
                  : 'text-gray-400 hover:bg-gray-800'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          {/* Stats Tab */}
          {tab === 'stats' && stats && (
            <div>
              <h2 className="text-yellow-400 font-bold text-xl mb-6">📊 إحصاءات المنصة</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
                {[
                  { label: 'إجمالي المستخدمين', value: stats.total_users, color: 'text-blue-400' },
                  { label: 'مستخدمون نشطون', value: stats.active_users, color: 'text-green-400' },
                  { label: 'مشتركو Pro', value: stats.pro_users, color: 'text-yellow-400' },
                  { label: 'مشتركو VIP', value: stats.vip_users, color: 'text-purple-400' },
                  { label: 'KYC معلّق', value: stats.kyc_pending, color: 'text-red-400' },
                  { label: 'إجمالي الإحالات', value: stats.total_referrals, color: 'text-cyan-400' },
                ].map(s => (
                  <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                    <div className={`text-3xl font-bold ${s.color}`}>{s.value?.toLocaleString() ?? '—'}</div>
                    <div className="text-gray-400 text-sm mt-1">{s.label}</div>
                  </div>
                ))}
              </div>

              {/* Plan Distribution */}
              <h3 className="text-gray-300 font-semibold mb-3">توزيع الخطط</h3>
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                {['free', 'starter', 'pro', 'vip', 'enterprise'].map(plan => {
                  const count = users.filter(u => u.plan?.toLowerCase() === plan).length;
                  const pct = users.length ? (count / users.length * 100).toFixed(1) : 0;
                  return (
                    <div key={plan} className="flex items-center gap-3 mb-2">
                      <span className={`w-20 text-right text-sm ${PLAN_COLORS[plan]}`}>{plan.toUpperCase()}</span>
                      <div className="flex-1 bg-gray-800 rounded-full h-3">
                        <div
                          className="h-3 rounded-full bg-yellow-500/60 transition-all"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-gray-400 text-sm w-16">{count} ({pct}%)</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Users Tab */}
          {tab === 'users' && (
            <div>
              <div className="flex items-center gap-4 mb-4">
                <h2 className="text-yellow-400 font-bold text-xl">👥 إدارة المستخدمين</h2>
                <input
                  type="text"
                  placeholder="بحث بالاسم أو البريد..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-200 flex-1 max-w-xs"
                />
                <button onClick={fetchUsers} className="bg-yellow-500/20 border border-yellow-500/40 text-yellow-400 px-3 py-1.5 rounded text-sm hover:bg-yellow-500/30">
                  🔄 تحديث
                </button>
              </div>

              {loading ? (
                <div className="text-gray-500 py-12 text-center">جارٍ التحميل...</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-gray-400 border-b border-gray-800">
                        <th className="py-2 px-3 text-right">المستخدم</th>
                        <th className="py-2 px-3 text-right">البريد</th>
                        <th className="py-2 px-3 text-right">الخطة</th>
                        <th className="py-2 px-3 text-right">الحالة</th>
                        <th className="py-2 px-3 text-right">2FA</th>
                        <th className="py-2 px-3 text-right">KYC</th>
                        <th className="py-2 px-3 text-right">إجراءات</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredUsers.map(user => (
                        <tr key={user.id} className="border-b border-gray-800/50 hover:bg-gray-900/50">
                          <td className="py-2 px-3">
                            <div className="font-medium text-gray-200">{user.username}</div>
                            <div className="text-gray-500 text-xs">{user.full_name}</div>
                          </td>
                          <td className="py-2 px-3 text-gray-400">{user.email}</td>
                          <td className="py-2 px-3">
                            <span className={`${PLAN_COLORS[user.plan?.toLowerCase()] || 'text-gray-400'} font-medium`}>
                              {user.plan?.toUpperCase() || 'FREE'}
                            </span>
                          </td>
                          <td className="py-2 px-3">
                            <span className={STATUS_COLORS[user.status] || 'text-gray-400'}>
                              {user.status === 'active' ? '🟢' : '🔴'} {user.status}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-center">
                            {user.is_2fa_enabled ? '✅' : '—'}
                          </td>
                          <td className="py-2 px-3">
                            <span className={
                              user.kyc_status === 'approved' ? 'text-green-400' :
                              user.kyc_status === 'pending' ? 'text-yellow-400' : 'text-gray-500'
                            }>
                              {user.kyc_status || 'none'}
                            </span>
                          </td>
                          <td className="py-2 px-3">
                            <div className="flex gap-2">
                              <button
                                onClick={() => { setSelectedUser(user); setNewPlan(user.plan || 'free'); setPlanModal(true); }}
                                className="text-yellow-400 hover:text-yellow-300 text-xs border border-yellow-500/30 px-2 py-0.5 rounded"
                              >
                                خطة
                              </button>
                              {user.status === 'active' ? (
                                <button
                                  onClick={() => updateUserStatus(user.id, 'suspended')}
                                  className="text-red-400 hover:text-red-300 text-xs border border-red-500/30 px-2 py-0.5 rounded"
                                >
                                  تعليق
                                </button>
                              ) : (
                                <button
                                  onClick={() => updateUserStatus(user.id, 'active')}
                                  className="text-green-400 hover:text-green-300 text-xs border border-green-500/30 px-2 py-0.5 rounded"
                                >
                                  تفعيل
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div className="text-gray-500 text-xs mt-2">
                    إجمالي: {filteredUsers.length} مستخدم
                  </div>
                </div>
              )}
            </div>
          )}

          {/* KYC Tab */}
          {tab === 'kyc' && (
            <div>
              <h2 className="text-yellow-400 font-bold text-xl mb-4">🪪 مراجعة KYC</h2>
              {kycPending.length === 0 ? (
                <div className="text-gray-500 py-12 text-center bg-gray-900 rounded-lg border border-gray-800">
                  ✅ لا توجد طلبات KYC معلّقة
                </div>
              ) : (
                <div className="space-y-3">
                  {kycPending.map(user => (
                    <div key={user.id} className="bg-gray-900 border border-yellow-500/20 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-gray-200">{user.full_name || user.username}</div>
                          <div className="text-gray-400 text-sm">{user.email}</div>
                          <div className="text-gray-500 text-xs mt-1">
                            انضم: {new Date(user.created_at).toLocaleDateString('ar-SA')}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={async () => {
                              await fetch(`${USER_SVC}/admin/users/${user.id}/kyc`, {
                                method: 'PUT', headers: authHeaders(),
                                body: JSON.stringify({ status: 'approved' }),
                              });
                              fetchUsers();
                            }}
                            className="bg-green-500/20 border border-green-500/40 text-green-400 px-4 py-2 rounded text-sm hover:bg-green-500/30"
                          >
                            ✅ موافقة
                          </button>
                          <button
                            onClick={async () => {
                              await fetch(`${USER_SVC}/admin/users/${user.id}/kyc`, {
                                method: 'PUT', headers: authHeaders(),
                                body: JSON.stringify({ status: 'rejected', notes: 'مرفوض من الإدارة' }),
                              });
                              fetchUsers();
                            }}
                            className="bg-red-500/20 border border-red-500/40 text-red-400 px-4 py-2 rounded text-sm hover:bg-red-500/30"
                          >
                            ❌ رفض
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* System Tab */}
          {tab === 'system' && (
            <div>
              <div className="flex items-center gap-4 mb-4">
                <h2 className="text-yellow-400 font-bold text-xl">⚙️ صحة النظام</h2>
                <button onClick={checkSystemHealth} className="bg-yellow-500/20 border border-yellow-500/40 text-yellow-400 px-3 py-1.5 rounded text-sm hover:bg-yellow-500/30">
                  🔄 فحص الآن
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(systemHealth).map(([name, status]) => (
                  <div key={name} className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex items-center justify-between">
                    <span className="text-gray-300 font-medium">{name}</span>
                    <span className="text-sm">{status}</span>
                  </div>
                ))}
              </div>

              <h3 className="text-gray-300 font-semibold mt-8 mb-3">روابط سريعة</h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: '📚 API Docs', url: `${API}/docs` },
                  { label: '📊 Grafana', url: 'http://localhost:3001' },
                  { label: '🔍 Prometheus', url: 'http://localhost:9090' },
                  { label: '🧪 Backtest Docs', url: 'http://localhost:8002/docs' },
                ].map(link => (
                  <a
                    key={link.label}
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bg-gray-900 border border-gray-800 rounded-lg p-3 text-center text-sm text-gray-300 hover:border-yellow-500/40 hover:text-yellow-400 transition-colors"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Plan Change Modal */}
      {planModal && selectedUser && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-yellow-500/40 rounded-xl p-6 w-80">
            <h3 className="text-yellow-400 font-bold mb-4">تغيير خطة {selectedUser.username}</h3>
            <select
              value={newPlan}
              onChange={e => setNewPlan(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-200 mb-4"
            >
              {['free', 'starter', 'pro', 'vip', 'enterprise'].map(p => (
                <option key={p} value={p}>{p.toUpperCase()}</option>
              ))}
            </select>
            <div className="flex gap-3">
              <button
                onClick={() => updateUserPlan(selectedUser.id, newPlan)}
                className="flex-1 bg-yellow-500/20 border border-yellow-500/40 text-yellow-400 py-2 rounded hover:bg-yellow-500/30"
              >
                تأكيد
              </button>
              <button
                onClick={() => setPlanModal(false)}
                className="flex-1 bg-gray-800 text-gray-400 py-2 rounded hover:bg-gray-700"
              >
                إلغاء
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
