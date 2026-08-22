import { useState, useCallback } from 'react'
import { API_URL } from '../config'

export default function UploadScreen({ onJobCreated }) {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true)
    else if (e.type === "dragleave") setDragActive(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0])
    }
  }

  const handleFileSelection = (selectedFile) => {
    setFile(selectedFile)
    if (selectedFile) {
      const reader = new FileReader()
      reader.onload = (event) => {
        const text = event.target.result
        const lines = text.split('\n').filter(l => l.trim()).slice(0, 6)
        const parsedPreview = lines.map(line => line.split(','))
        setPreview(parsedPreview)
      }
      reader.readAsText(selectedFile)
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setIsUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await fetch(`${API_URL}/jobs`, {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      onJobCreated(data.job_id)
    } catch (error) {
      console.error('Upload error', error)
      setIsUploading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto mt-12">
      <div className="mb-16">
        <h1 className="text-6xl md:text-7xl font-display text-forge-white leading-[1.1] mb-6">
          Six fields in.<br/>
          <span className="text-forge-ember">A complete record out.</span>
        </h1>
        <p className="text-xl font-sans text-forge-ash max-w-2xl">
          Drop raw catalog data into the forge. Watch it resolve into verified, structured delivery formats.
        </p>
      </div>
      
      <div 
        className={`forge-mouth relative p-12 flex flex-col items-center justify-center text-center cursor-pointer mb-12 ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input 
          type="file" 
          accept=".csv" 
          onChange={(e) => handleFileSelection(e.target.files[0])}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
        />
        <div className="font-mono text-lg text-forge-white mb-2">
          {file ? `[ ${file.name} ]` : '[ Drop raw material here ]'}
        </div>
        {!file && <div className="font-sans text-sm text-forge-ash">or click to select CSV</div>}
      </div>

      {preview.length > 0 && (
        <div className="mb-12 border border-forge-ash/30 bg-[#12110E] p-1">
          <table className="min-w-full font-mono text-xs text-left">
            <thead className="border-b border-forge-ash/30 text-forge-white">
              <tr>
                {preview[0].map((header, i) => (
                  <th key={i} className="px-4 py-3">{header}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-forge-ash/10 text-forge-ash">
              {preview.slice(1).map((row, i) => (
                <tr key={i}>
                  {row.map((cell, j) => (
                    <td key={j} className="px-4 py-2 truncate max-w-[200px]">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {file && (
        <div className="flex justify-end">
          <button 
            onClick={handleUpload} 
            disabled={isUploading}
            className={`px-8 py-4 font-display text-xl uppercase tracking-wider transition-all
              ${isUploading 
                ? 'bg-forge-ash/20 text-forge-ash cursor-not-allowed border border-forge-ash' 
                : 'bg-forge-ember text-forge-dark hover:bg-[#ff6e36] shadow-[0_0_20px_rgba(232,93,36,0.3)] hover:shadow-[0_0_30px_rgba(232,93,36,0.5)]'}`}
          >
            {isUploading ? 'Igniting...' : 'Begin the refinement'}
          </button>
        </div>
      )}
    </div>
  )
}
