'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';

interface RiskComponent {
  component_name: string;
  normalized_score: number;
  weight: number;
  weighted_score: number;
  details: any;
}

interface PreventiveAction {
  rule_id: string;
  action_type: string;
  priority: number;
  rationale: string;
  action_payload: any;
}

interface RiskEvaluation {
  risk_evaluation_id: string;
  policy_number: string;
  policy_type: string;
  evaluated_at: string;
  loss_risk_index: number;
  risk_band: string;
  components: RiskComponent[];
  preventive_actions: PreventiveAction[];
  fired_rules: string[];
  input_snapshot: any;
  explanation: any;
}

interface CustomerInfo {
  customer_id: string;
  full_name: string;
  email: string;
  phone_number: string;
}

export default function ResultsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  // Read policy number from sessionStorage for security - not from URL
  const [policyNumber, setPolicyNumber] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RiskEvaluation | null>(null);
  const [customer, setCustomer] = useState<CustomerInfo | null>(null);

  useEffect(() => {
    const storedPolicy = sessionStorage.getItem('policyNumber');
    if (!storedPolicy) {
      router.push('/');
      return;
    }
    setPolicyNumber(storedPolicy);

    if (!policyNumber) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch('http://localhost:8000/risk/evaluate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ policy_number: policyNumber }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
          throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setResult(data);
        
        // Fetch customer information if we have customer_id
        if (data.input_snapshot?.policy?.customer_id) {
          try {
            const customerResponse = await fetch(
              `http://localhost:8000/customers/${data.input_snapshot.policy.customer_id}`
            );
            if (customerResponse.ok) {
              const customerData = await customerResponse.json();
              setCustomer(customerData);
            }
          } catch (err) {
            console.error('Failed to fetch customer info:', err);
            // Don't fail the whole page if customer fetch fails
          }
        }
      } catch (err: any) {
        setError(err.message || 'Failed to evaluate policy');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [policyNumber, router]);

  // Cleanup sessionStorage on component unmount
  useEffect(() => {
    return () => {
      // Optional: clear on unmount if desired
      // sessionStorage.removeItem('policyNumber');
    };
  }, []);

  const getRiskColor = (band: string) => {
    switch (band) {
      case 'LOW':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'MEDIUM':
        return 'text-orange-700 bg-orange-50 border-orange-200';
      case 'HIGH':
        return 'text-red-700 bg-red-50 border-red-200';
      default:
        return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  const getScoreColor = (score: number) => {
    if (score < 35) return 'bg-green-500';
    if (score < 70) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="min-h-screen bg-stone-50">
      {/* Header */}
      <header className="border-b border-stone-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-stone-900">Loss Risk Index</h1>
              <p className="text-sm text-stone-600 mt-1">Deterministic Predictive Analytics</p>
            </div>
            <Link
              href="/"
              className="px-4 py-2 text-sm font-medium text-stone-700 hover:text-stone-900 border border-stone-300 rounded-md hover:bg-stone-50 transition-colors"
            >
              ← New Evaluation
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-stone-900"></div>
              <p className="mt-4 text-stone-600">Evaluating policy...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {result && (
          <div className="space-y-6">
            {/* Risk Overview */}
            <div className="bg-white rounded-lg border border-stone-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-stone-200 bg-stone-50">
                <h3 className="text-lg font-semibold text-stone-900">Risk Assessment</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Policy</div>
                    <div className="text-2xl font-bold text-stone-900">{result.policy_number}</div>
                    <div className="text-sm text-stone-600 mt-1">{result.policy_type}</div>
                  </div>

                  <div>
                    <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Loss Risk Index</div>
                    <div className="text-2xl font-bold text-stone-900">{result.loss_risk_index}</div>
                    <div className="text-sm text-stone-600 mt-1">0–100 Scale</div>
                  </div>

                  <div>
                    <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-2">Risk Band</div>
                    <span className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-semibold border ${getRiskColor(result.risk_band)}`}>
                      {result.risk_band}
                    </span>
                  </div>
                </div>

                <div className="mt-6">
                  <div className="flex justify-between text-xs font-medium text-stone-600 mb-2">
                    <span>0 (Low Risk)</span>
                    <span>100 (High Risk)</span>
                  </div>
                  <div className="w-full h-3 bg-stone-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getScoreColor(result.loss_risk_index)} transition-all duration-500`}
                      style={{ width: `${result.loss_risk_index}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Policy Holder Information */}
            {result.input_snapshot?.policy && (
              <div className="bg-white rounded-lg border border-stone-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-stone-200 bg-stone-50">
                  <h3 className="text-lg font-semibold text-stone-900">Policy Holder Information</h3>
                </div>
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {customer && (
                      <>
                        <div>
                          <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Policy Holder Name</div>
                          <div className="text-lg font-semibold text-stone-900">{customer.full_name}</div>
                        </div>
                        <div>
                          <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Email</div>
                          <div className="text-sm text-stone-900">{customer.email}</div>
                        </div>
                        <div>
                          <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Phone Number</div>
                          <div className="text-sm text-stone-900">{customer.phone_number}</div>
                        </div>
                      </>
                    )}
                    {result.input_snapshot.policy.customer_id && (
                      <div>
                        <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Customer ID</div>
                        <div className="text-sm text-stone-900">{result.input_snapshot.policy.customer_id}</div>
                      </div>
                    )}
                    {result.input_snapshot.policy.insured_id && (
                      <div>
                        <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Insured ID</div>
                        <div className="text-sm text-stone-900">{result.input_snapshot.policy.insured_id}</div>
                      </div>
                    )}
                    {result.input_snapshot.policy.product_line && (
                      <div>
                        <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Product Line</div>
                        <div className="text-sm text-stone-900 capitalize">{result.input_snapshot.policy.product_line.replace(/-/g, ' ')}</div>
                      </div>
                    )}
                    {result.input_snapshot.policy.region_code && (
                      <div>
                        <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Region</div>
                        <div className="text-sm text-stone-900">{result.input_snapshot.policy.region_code}</div>
                      </div>
                    )}
                    {result.input_snapshot.policy.asset_type && (
                      <div>
                        <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Asset Type</div>
                        <div className="text-sm text-stone-900 capitalize">{result.input_snapshot.policy.asset_type}</div>
                      </div>
                    )}
                    {result.input_snapshot.policy.coverage_limit && (
                      <div>
                        <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Coverage Limit</div>
                        <div className="text-sm text-stone-900">₹{result.input_snapshot.policy.coverage_limit.toLocaleString('en-IN')}</div>
                      </div>
                    )}
                    {result.input_snapshot.policy.effective_date && (
                      <div>
                        <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Effective Date</div>
                        <div className="text-sm text-stone-900">{new Date(result.input_snapshot.policy.effective_date).toLocaleDateString()}</div>
                      </div>
                    )}
                    {result.input_snapshot.policy.expiry_date && (
                      <div>
                        <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Expiry Date</div>
                        <div className="text-sm text-stone-900">{new Date(result.input_snapshot.policy.expiry_date).toLocaleDateString()}</div>
                      </div>
                    )}
                  </div>

                  {result.input_snapshot.health_profile && (
                    <div className="mt-6 pt-6 border-t border-stone-200">
                      <h4 className="text-sm font-semibold text-stone-900 mb-4">Health Profile</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {result.input_snapshot.health_profile.member_age !== undefined && (
                          <div>
                            <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Member Age</div>
                            <div className="text-sm text-stone-900">{result.input_snapshot.health_profile.member_age} years</div>
                          </div>
                        )}
                        {result.input_snapshot.health_profile.chronic_flags && (
                          <div className="md:col-span-2">
                            <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-2">Chronic Conditions</div>
                            <div className="flex flex-wrap gap-2">
                              {Object.entries(result.input_snapshot.health_profile.chronic_flags).map(([condition, value]) => (
                                <span
                                  key={condition}
                                  className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                                    value ? 'bg-orange-100 text-orange-800' : 'bg-green-100 text-green-800'
                                  }`}
                                >
                                  {condition.replace(/_/g, ' ')}: {value ? 'Yes' : 'No'}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {result.input_snapshot.life_profile && (
                    <div className="mt-6 pt-6 border-t border-stone-200">
                      <h4 className="text-sm font-semibold text-stone-900 mb-4">Life Profile</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {result.input_snapshot.life_profile.insured_age !== undefined && (
                          <div>
                            <div className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-1">Insured Age</div>
                            <div className="text-sm text-stone-900">{result.input_snapshot.life_profile.insured_age} years</div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {result.input_snapshot.claims && result.input_snapshot.claims.length > 0 && (
                    <div className="mt-6 pt-6 border-t border-stone-200">
                      <h4 className="text-sm font-semibold text-stone-900 mb-4">Claims History ({result.input_snapshot.claims.length})</h4>
                      <div className="space-y-3">
                        {result.input_snapshot.claims.slice(0, 5).map((claim: any, index: number) => (
                          <div key={index} className="flex justify-between items-start p-3 bg-stone-50 rounded-lg">
                            <div>
                              <div className="text-sm font-medium text-stone-900">{claim.claim_type || 'Claim'}</div>
                              {claim.description && <div className="text-xs text-stone-600 mt-1">{claim.description}</div>}
                              {claim.loss_date && <div className="text-xs text-stone-500 mt-1">Date: {new Date(claim.loss_date).toLocaleDateString()}</div>}
                            </div>
                            {claim.paid_amount !== undefined && (
                              <div className="text-sm font-semibold text-stone-900">₹{claim.paid_amount.toLocaleString('en-IN')}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Risk Calculation Explanation
            <div className="bg-white rounded-lg border border-stone-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-stone-200 bg-stone-50">
                <h3 className="text-lg font-semibold text-stone-900">How Risk is Calculated</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  <p className="text-sm text-stone-700">
                    The Loss Risk Index (LRI) is a deterministic score from 0-100 that combines multiple risk components with predefined weights.
                  </p>
                  
                  <div>
                    <h4 className="text-sm font-semibold text-stone-900 mb-2">Risk Components & Weights:</h4>
                    <ul className="text-sm text-stone-700 space-y-2 list-disc list-inside">
                      {result.components.map((component) => (
                        <li key={component.component_name}>
                          <span className="font-medium capitalize">{component.component_name.replace(/_/g, ' ')}</span>: {(component.weight * 100).toFixed(0)}% weight
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h4 className="text-sm font-semibold text-stone-900 mb-2">Calculation Method:</h4>
                    <ol className="text-sm text-stone-700 space-y-2 list-decimal list-inside">
                      <li>Each component is scored individually (0-100)</li>
                      <li>Component scores are multiplied by their respective weights</li>
                      <li>Weighted scores are summed to produce the final LRI</li>
                      <li>Rules are evaluated to determine risk band (LOW/MEDIUM/HIGH) and preventive actions</li>
                    </ol>
                  </div>

                  <div className="bg-stone-50 rounded-lg p-4">
                    <p className="text-xs font-mono text-stone-700">
                      LRI = {result.components.map((c, i) => 
                        `${c.component_name}(${c.normalized_score}) × ${(c.weight * 100).toFixed(0)}%`
                      ).join(' + ')}
                    </p>
                    <p className="text-xs font-mono text-stone-700 mt-2">
                      = {result.components.map((c) => c.weighted_score.toFixed(1)).join(' + ')} = <span className="font-bold">{result.loss_risk_index}</span>
                    </p>
                  </div>

                  <div>
                    <h4 className="text-sm font-semibold text-stone-900 mb-2">Risk Bands:</h4>
                    <ul className="text-sm text-stone-700 space-y-1 list-disc list-inside">
                      <li><span className="font-medium text-green-700">LOW</span>: LRI 0-35</li>
                      <li><span className="font-medium text-orange-700">MEDIUM</span>: LRI 35-70</li>
                      <li><span className="font-medium text-red-700">HIGH</span>: LRI 70-100</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div> */}

            {/* Component Scores */}
            <div className="bg-white rounded-lg border border-stone-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-stone-200 bg-stone-50">
                <h3 className="text-lg font-semibold text-stone-900">Risk Components</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {result.components.map((component) => (
                    <div key={component.component_name} className="border border-stone-200 rounded-lg p-4">
                      <div className="flex justify-between items-center mb-3">
                        <div>
                          <h4 className="text-sm font-semibold text-stone-900 capitalize">
                            {component.component_name.replace(/_/g, ' ')}
                          </h4>
                          <p className="text-xs text-stone-500 mt-1">Weight: {(component.weight * 100).toFixed(0)}%</p>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-stone-900">{component.normalized_score}</div>
                          <div className="text-xs text-stone-500">Score</div>
                        </div>
                      </div>
                      <div className="w-full h-2 bg-stone-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${getScoreColor(component.normalized_score)} transition-all duration-300`}
                          style={{ width: `${component.normalized_score}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Preventive Actions */}
            {result.preventive_actions.length > 0 && (
              <div className="bg-white rounded-lg border border-stone-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-stone-200 bg-stone-50">
                  <h3 className="text-lg font-semibold text-stone-900">Preventive Actions</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {result.preventive_actions.map((action, index) => (
                      <div key={index} className="flex gap-4 p-4 border border-stone-200 rounded-lg">
                        <div className="flex-shrink-0">
                          <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center">
                            <span className="text-sm font-bold text-orange-700">{action.priority}</span>
                          </div>
                        </div>
                        <div className="flex-1">
                          <h4 className="text-sm font-semibold text-stone-900">
                            {action.action_type.replace(/_/g, ' ')}
                          </h4>
                          <p className="text-sm text-stone-600 mt-1">{action.rationale}</p>
                          <div className="mt-2">
                            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-stone-100 text-stone-700">
                              {action.rule_id}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="bg-white rounded-lg border border-stone-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-stone-200 bg-stone-50">
                <h3 className="text-lg font-semibold text-stone-900">Evaluation Metadata</h3>
              </div>
              <div className="p-6">
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <dt className="font-medium text-stone-500">Evaluation ID</dt>
                    <dd className="mt-1 text-stone-900 font-mono text-xs">{result.risk_evaluation_id}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-stone-500">Evaluated At</dt>
                    <dd className="mt-1 text-stone-900">{new Date(result.evaluated_at).toLocaleString()}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-stone-500">Ruleset</dt>
                    <dd className="mt-1 text-stone-900">{result.explanation.model.ruleset_name} v{result.explanation.model.version}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-stone-500">Fired Rules</dt>
                    <dd className="mt-1 text-stone-900">{result.fired_rules.length > 0 ? result.fired_rules.join(', ') : 'None'}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-stone-200 bg-white mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-sm text-stone-500 text-center">
            Deterministic, Auditable, Extensible • Rule-Based Risk Engine
          </p>
        </div>
      </footer>
    </div>
  );
}
