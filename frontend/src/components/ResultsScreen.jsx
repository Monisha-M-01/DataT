import { useEffect, useState } from 'react'

export default function ResultsScreen({ jobId }) {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterMode, setFilterMode] = useState('all') // 'all', 'success', 'faults'
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch(`http://localhost:8000/jobs/${jobId}/results`)
        const data = await response.json()
        setResults(data.results || [])
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchResults()
  }, [jobId])

  const handleExport = () => {
    window.open(`http://localhost:8000/jobs/${jobId}/export`, '_blank')
  }

  if (loading) return (
    <div className="font-mono text-sm text-forge-ash animate-pulse mt-12">Loading output...</div>
  )

  const totalRows = results.length;
  const faultRows = results.filter(r => r._meta && r._meta.needs_human_review).length;
  const successRows = totalRows - faultRows;

  const displayedResults = results.filter(r => {
    if (filterMode === 'faults' && (!r._meta || !r._meta.needs_human_review)) return false;
    if (filterMode === 'success' && (r._meta && r._meta.needs_human_review)) return false;
    
    if (searchQuery.trim() !== '') {
      const query = searchQuery.toLowerCase();
      const mpn = (r.input.Mfg_Part_Num || '').toLowerCase();
      const desc = (r.input.Part_Desc || '').toLowerCase();
      const outDesc = (r.output.SHORT_DESC || '').toLowerCase();
      
      if (!mpn.includes(query) && !desc.includes(query) && !outDesc.includes(query)) {
        return false;
      }
    }
    
    return true;
  });

  return (
    <div className="w-full">
      <div className="flex justify-between items-end mb-6">
        <div>
          <h2 className="text-3xl font-display uppercase tracking-wider text-forge-white mb-3">Refinement Output</h2>
          <input 
            type="text" 
            placeholder="Search by MPN or Description..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-96 bg-[#0f0e0b] border border-forge-ash/30 text-forge-white px-4 py-2 text-sm font-mono focus:outline-none focus:border-forge-steel placeholder-forge-ash/50 transition-colors hover:border-forge-ash/60"
          />
        </div>
        <button 
          onClick={handleExport}
          className="px-6 py-3 bg-forge-steel text-forge-white font-sans font-medium hover:bg-[#4a5c6e] transition-colors h-11"
        >
          Export Delivery Format
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <button 
          onClick={() => setFilterMode('all')}
          className={`bg-[#0f0e0b] border p-4 flex flex-col items-center justify-center transition-all cursor-pointer ${filterMode === 'all' ? 'border-forge-white bg-forge-white/5 scale-[1.02]' : 'border-forge-ash/30 hover:border-forge-ash/60 hover:bg-forge-ash/5'}`}
        >
          <div className={`text-xs uppercase tracking-widest mb-1 ${filterMode === 'all' ? 'text-forge-white font-bold' : 'text-forge-ash'}`}>Total Processed</div>
          <div className="text-3xl font-display text-forge-white">{totalRows}</div>
        </button>
        <button 
          onClick={() => setFilterMode('success')}
          className={`bg-[#0f0e0b] border p-4 flex flex-col items-center justify-center transition-all cursor-pointer ${filterMode === 'success' ? 'border-forge-verified bg-forge-verified/10 scale-[1.02]' : 'border-forge-verified/40 hover:border-forge-verified/70 hover:bg-forge-verified/5'}`}
        >
          <div className={`text-xs uppercase tracking-widest mb-1 ${filterMode === 'success' ? 'text-forge-verified font-bold' : 'text-forge-verified/80'}`}>Perfect Matches</div>
          <div className="text-3xl font-display text-forge-verified">{successRows}</div>
        </button>
        <button 
          onClick={() => setFilterMode('faults')}
          className={`bg-[#0f0e0b] border p-4 flex flex-col items-center justify-center transition-all cursor-pointer ${filterMode === 'faults' ? 'border-forge-ember bg-forge-ember/10 scale-[1.02]' : 'border-forge-ember/40 hover:border-forge-ember/70 hover:bg-forge-ember/5'}`}
        >
          <div className={`text-xs uppercase tracking-widest mb-1 ${filterMode === 'faults' ? 'text-forge-ember font-bold' : 'text-forge-ember/80'}`}>Needs Human Review</div>
          <div className="text-3xl font-display text-forge-ember">{faultRows}</div>
        </button>
      </div>

      <div className="bg-[#0f0e0b] border border-forge-ash/30">
        <table className="min-w-full text-left font-mono text-xs">
          <thead className="border-b border-forge-ash/30 text-forge-white bg-black/40">
            <tr>
              <th className="px-6 py-4 font-semibold border-r border-forge-ash/30 w-[40%] uppercase tracking-wider">Raw Input</th>
              <th className="px-6 py-4 font-semibold uppercase tracking-wider">Structured Output</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-forge-ash/10">
            {displayedResults.map((row, i) => {
              const input = row.input
              const output = row.output
              const meta = row._meta
              
              return (
                <tr key={i} className="align-top hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-5 border-r border-forge-ash/30 text-forge-ash w-[40%]">
                    <div className="grid grid-cols-4 gap-2">
                      <div className="col-span-1 text-forge-ash/70 font-semibold">MPN</div>
                      <div className="col-span-3 truncate text-forge-white/80">{input.Mfg_Part_Num || '-'}</div>
                      <div className="col-span-1 text-forge-ash/70 font-semibold">Desc</div>
                      <div className="col-span-3 truncate text-forge-white/80">{input.Part_Desc || '-'}</div>
                      <div className="col-span-1 text-forge-ash/70 font-semibold">Brands</div>
                      <div className="col-span-3 truncate text-forge-white/80">
                        {[input.E1_Brand, input.Unilog_Brand, input.DIB_Brand, input.Part_Manuf].filter(Boolean).join(' | ') || '-'}
                      </div>
                    </div>
                  </td>
                  
                  <td className="px-6 py-5 w-[60%] relative">
                    <div className="grid grid-cols-4 gap-x-2 gap-y-3">
                      <div className="col-span-1 text-forge-steel font-semibold">Brand</div>
                      <div className="col-span-3 text-forge-white flex items-center">
                        <div className="w-6 h-[1px] bg-forge-steel/50 mr-3"></div>
                        {output.BRAND_NAME || '-'}
                      </div>
                      
                      <div className="col-span-1 text-forge-steel font-semibold">Category</div>
                      <div className="col-span-3 text-forge-white flex items-center">
                        <div className="w-6 h-[1px] bg-forge-steel/50 mr-3"></div>
                        {output.CATEGORY || '-'}
                      </div>

                      <div className="col-span-1 text-forge-steel font-semibold">Short Desc</div>
                      <div className="col-span-3 text-forge-white flex items-center truncate">
                        <div className="w-6 h-[1px] bg-forge-steel/50 mr-3"></div>
                        <span className="truncate pr-8">{output.SHORT_DESC || '-'}</span>
                      </div>
                    </div>

                    {meta.needs_human_review ? (
                      <div className="mt-6 pl-[25%] text-[10px] relative">
                        {meta.quota_exhausted ? (
                          <div className="ember-leader ml-10 border border-red-500 bg-red-950/40 p-3 relative z-10 shadow-lg">
                            <div className="font-semibold mb-1 uppercase tracking-wider text-red-400">
                              QUOTA EXHAUSTED - RESUME AFTER RESET
                            </div>
                            <div className="text-red-300 opacity-90">{meta.review_reason}</div>
                            <div className="mt-2 text-forge-ash/70 truncate border-t border-red-500/20 pt-1">Free tier API limit reached.</div>
                          </div>
                        ) : (
                          <div className="text-forge-ember">
                            <div className="ember-leader ml-10 border border-forge-ember bg-forge-dark p-3 relative z-10 shadow-lg">
                              <div className="font-semibold mb-1 uppercase tracking-wider text-forge-white">
                                NEEDS YOUR EYE <span className="text-forge-ember opacity-80">| {(meta.confidence_score * 100).toFixed(0)}% CONF</span>
                              </div>
                              <div className="text-forge-ember opacity-90">{meta.review_reason}</div>
                              {meta.unresolved_fields && meta.unresolved_fields.length > 0 && (
                                <div className="mt-1">UNRESOLVED: {meta.unresolved_fields.join(', ')}</div>
                              )}
                              {meta.source_url_used && (
                                <div className="mt-2 text-forge-ash truncate border-t border-forge-ash/20 pt-1">SRC: {meta.source_url_used}</div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="absolute top-5 right-5 text-forge-verified">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="square" strokeLinejoin="miter" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
