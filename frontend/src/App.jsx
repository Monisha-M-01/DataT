import { useState } from 'react'
import UploadScreen from './components/UploadScreen'
import ProcessingScreen from './components/ProcessingScreen'
import ResultsScreen from './components/ResultsScreen'

function App() {
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState('upload')

  return (
    <div className="min-h-screen">
      <main className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {status === 'upload' && <UploadScreen onJobCreated={(id) => { setJobId(id); setStatus('processing'); }} />}
        {status === 'processing' && <ProcessingScreen jobId={jobId} onCompleted={() => setStatus('results')} />}
        {status === 'results' && <ResultsScreen jobId={jobId} />}
      </main>
    </div>
  )
}

export default App
