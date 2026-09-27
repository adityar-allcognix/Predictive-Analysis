'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession, signOut } from 'next-auth/react';
import { LogOut, Shield } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [policyNumber, setPolicyNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Redirect to signin if not authenticated
  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
    }
  }, [status, router]);

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (showUserMenu && !target.closest('.user-menu-container')) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [showUserMenu]);

  const handleEvaluate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!policyNumber.trim()) return;
    setLoading(true);
    // Store in sessionStorage for security - don't expose policy number in URL
    sessionStorage.setItem('policyNumber', policyNumber.trim());
    router.push('/results');
  };

  const handleSignOut = async () => {
    await signOut({ callbackUrl: '/auth/signin' });
  };

  // Show loading state while checking authentication
  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render the page if not authenticated
  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      {/* Header */}
      <header className="border-b bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-600 rounded-lg">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-gray-800">
                Allcognix
              </h1>
              <p className="text-sm text-gray-500">
                Policy Risk Evaluation Dashboard
              </p>
            </div>
          </div>
          <div className="flex items-center gap-6 text-sm text-gray-600">
            {/* User Menu */}
            <div className="relative user-menu-container">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold">
                  {session.user?.name?.charAt(0).toUpperCase() || 'U'}
                </div>
                <span className="font-medium text-gray-700">{session.user?.name || 'User'}</span>
              </button>
              
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                  <div className="px-4 py-2 border-b border-gray-200">
                    <p className="text-sm font-medium text-gray-900">{session.user?.name}</p>
                    <p className="text-xs text-gray-500">{session.user?.email}</p>
                  </div>
                  <button
                    onClick={handleSignOut}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-7xl mx-auto px-6 py-12 space-y-12">
        {/* Context Bar */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold">
              Policies Evaluated
            </div>
            <div className="text-3xl font-extrabold text-gray-900 mt-2">
              1,284
            </div>
            <div className="text-xs text-blue-700 mt-3 font-medium">
              Last 30 days
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold">
              Avg Evaluation Latency
            </div>
            <div className="text-3xl font-extrabold text-gray-900 mt-2">
              412 ms
            </div>
            <div className="text-xs text-green-700 mt-3 font-medium">
              SLA compliant
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold">
              Risk Flags Triggered
            </div>
            <div className="text-3xl font-extrabold text-gray-900 mt-2">
              7.4%
            </div>
            <div className="text-xs text-yellow-700 mt-3 font-medium">
              System-wide rate
            </div>
          </div>
        </section>

        {/* Workspace */}
        <section className="grid grid-cols-12 gap-10">
          {/* Primary */}
          <div className="col-span-12 lg:col-span-8 space-y-8">
            <div className="bg-white border border-gray-200 rounded-lg shadow-md">
              <div className="px-6 py-5 border-b border-gray-200 bg-gray-100 flex items-center justify-between">
                <h2 className="text-base font-semibold uppercase tracking-wide text-gray-700">
                  Policy Evaluation
                </h2>
                <span className="text-xs text-gray-500">
                  Real-time deterministic engine
                </span>
              </div>

              <form onSubmit={handleEvaluate} className="p-6 space-y-6">
                <div>
                  <label
                    htmlFor="policy-number"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Policy Identifier
                  </label>
                  <input
                    id="policy-number"
                    type="text"
                    value={policyNumber}
                    onChange={(e) => setPolicyNumber(e.target.value)}
                    placeholder="AUTO-MH-2025-000001"
                    className="w-full px-4 py-3 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
                    disabled={loading}
                    required
                  />
                  <p className="mt-2 text-xs text-gray-500">
                    Exact match required.
                  </p>
                </div>

                <div className="flex items-center gap-6">
                  <button
                    type="submit"
                    disabled={loading || !policyNumber.trim()}
                    className="inline-flex items-center px-5 py-2 bg-blue-700 text-white text-sm font-semibold rounded-md hover:bg-blue-600 disabled:opacity-50"
                  >
                    {loading ? 'Evaluating…' : 'Run Risk Evaluation'}
                  </button>
                </div>
              </form>
            </div>

            {/* Recent Evaluations */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-md">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-100">
                <h3 className="text-base font-semibold text-gray-700">
                  Recent Evaluations
                </h3>
              </div>
              <div className="divide-y text-sm">
                {[
                  { id: 'AUTO-MH-2025-000231', risk: 'Low', time: '320 ms' },
                  { id: 'HLTH-IN-2025-000044', risk: 'Medium', time: '410 ms' },
                  { id: 'LIFE-IN-2025-000018', risk: 'High', time: '690 ms' },
                ].map((row) => (
                  <div key={row.id} className="px-6 py-4 flex justify-between">
                    <span className="font-mono text-gray-800">
                      {row.id}
                    </span>
                    <span className="flex items-center gap-6">
                      <span className="text-gray-500">{row.time}</span>
                      <span
                        className={`font-semibold ${
                          row.risk === 'Low'
                            ? 'text-green-700'
                            : row.risk === 'Medium'
                            ? 'text-yellow-600'
                            : 'text-red-700'
                        }`}
                      >
                        {row.risk}
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Secondary */}
          <aside className="col-span-12 lg:col-span-4 space-y-8">
            <div className="bg-white border border-gray-200 rounded-lg shadow-md">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-100">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-700">
                  System Signals
                </h3>
              </div>
              <div className="p-6 text-sm text-gray-600 space-y-4">
                <div className="flex justify-between">
                  <span>Rule Engine</span>
                  <span className="text-green-700 font-semibold">Operational</span>
                </div>
                <div className="flex justify-between">
                  <span>Data Sources</span>
                  <span className="text-green-700 font-semibold">Healthy</span>
                </div>
                <div className="flex justify-between">
                  <span>Audit Logger</span>
                  <span className="text-green-700 font-semibold">Active</span>
                </div>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg shadow-md">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-100">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-700">
                  Risk Distribution (24h)
                </h3>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Low</span>
                    <span>68%</span>
                  </div>
                  <div className="h-2 bg-gray-300 rounded-full">
                    <div className="h-2 bg-green-600 rounded-full w-[68%]" />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Medium</span>
                    <span>22%</span>
                  </div>
                  <div className="h-2 bg-gray-300 rounded-full">
                    <div className="h-2 bg-yellow-500 rounded-full w-[22%]" />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm">
                    <span>High</span>
                    <span>10%</span>
                  </div>
                  <div className="h-2 bg-gray-300 rounded-full">
                    <div className="h-2 bg-red-600 rounded-full w-[10%]" />
                  </div>
                </div>
              </div>
            </div>
          </aside>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t bg-white shadow-inner">
        <div className="max-w-7xl mx-auto px-6 py-4 text-sm text-gray-500 flex justify-between">
          <span>© 2025 Allcognix. All rights reserved.</span>
        </div>
      </footer>
    </div>
  );
}
