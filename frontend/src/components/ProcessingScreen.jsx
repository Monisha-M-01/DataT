import { useEffect, useState, useRef } from 'react'

export default function ProcessingScreen({ jobId, onCompleted }) {
  const [status, setStatus] = useState({ processed: 0, total: 0, status: 'processing' })
  const [pulse, setPulse] = useState(false)
  const prevProcessed = useRef(0)

  useEffect(() => {
    let interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/jobs/${jobId}/status`)
        const data = await response.json()
        
        if (data.processed > prevProcessed.current) {
          setPulse(true)
          setTimeout(() => setPulse(false), 600)
          prevProcessed.current = data.processed
        }
        
        setStatus(data)
        if (data.status === 'completed' || data.status === 'failed' || data.status === 'paused') {
          clearInterval(interval)
          if (data.status === 'completed' || data.status === 'paused') {
            setTimeout(onCompleted, 1000)
          }
        }
      } catch (e) {
        console.error(e)
      }
    }, 1500)
    
    return () => clearInterval(interval)
  }, [jobId, onCompleted])

  return (
    <div className="max-w-4xl mx-auto pt-24 flex flex-col items-center justify-center min-h-[60vh]">
      <div className="font-display text-4xl md:text-5xl text-forge-white mb-20 tracking-wide uppercase">
        {status.processed} OF {status.total || '?'} REFINED
      </div>
      
      {/* Convergence Animation Container */}
      <div className="relative w-full max-w-2xl h-40 flex items-center justify-center overflow-hidden">
        
        {/* Raw inputs side (Chaos) */}
        <div className={`absolute flex flex-col gap-3 transition-all duration-[600ms] ease-[cubic-bezier(0.16,1,0.3,1)] ${pulse ? 'opacity-0 translate-x-16 scale-90 blur-sm' : 'opacity-100 -translate-x-[120px] scale-100 blur-0'}`}>
           <div className="w-24 h-1.5 bg-forge-ash/40"></div>
           <div className="w-36 h-1.5 bg-forge-ash/40 ml-4"></div>
           <div className="w-16 h-1.5 bg-forge-ash/40 -ml-2"></div>
           <div className="w-28 h-1.5 bg-forge-ash/40 ml-6"></div>
           <div className="w-20 h-1.5 bg-forge-ash/40 ml-2"></div>
           <div className="w-32 h-1.5 bg-forge-ash/40 -ml-4"></div>
        </div>

        {/* The Forge / Convergence Point */}
        <div className={`w-12 h-40 border-x border-forge-ember transition-all duration-[600ms] ${pulse ? 'ember-pulse bg-forge-ember/10' : 'border-forge-ash/30 bg-transparent'}`}></div>

        {/* Refined output side (Order) */}
        <div className={`absolute flex flex-col gap-1 transition-all duration-[600ms] ease-[cubic-bezier(0.16,1,0.3,1)] ${pulse ? 'opacity-100 translate-x-[120px] scale-100 blur-0' : 'opacity-0 -translate-x-16 scale-90 blur-sm'}`}>
           {Array.from({ length: 12 }).map((_, i) => (
             <div key={i} className="flex gap-2">
                <div className="w-12 h-[3px] bg-forge-steel"></div>
                <div className="w-32 h-[3px] bg-forge-white"></div>
             </div>
           ))}
        </div>
      </div>
    </div>
  )
}
