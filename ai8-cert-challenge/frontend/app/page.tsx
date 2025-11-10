'use client'

import { useState, useRef, useEffect } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [openaiKey, setOpenaiKey] = useState('')
  const [cohereKey, setCohereKey] = useState('')
  const [useReranking, setUseReranking] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [apiUrl, setApiUrl] = useState(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState('')
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!input.trim() || !openaiKey) {
      alert('Please enter your OpenAI API key and a message')
      return
    }

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          openai_api_key: openaiKey,
          cohere_api_key: cohereKey,
          use_reranking: useReranking && cohereKey !== '',
        }),
      })

      const data = await response.json()

      if (data.error) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: `Error: ${data.error}` 
        }])
      } else {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: data.response 
        }])
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Error: ${error instanceof Error ? error.message : 'Failed to connect to server'}` 
      }])
    } finally {
      setLoading(false)
    }
  }

  const prepareData = async () => {
    if (!openaiKey) {
      alert('Please enter your OpenAI API key')
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`${apiUrl}/api/prepare?openai_api_key=${openaiKey}`, {
        method: 'POST',
      })

      const data = await response.json()
      alert(data.message || 'Data prepared successfully')
    } catch (error) {
      alert(`Error: ${error instanceof Error ? error.message : 'Failed to prepare data'}`)
    } finally {
      setLoading(false)
    }
  }

  const loadFiles = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/files`)
      const data = await response.json()
      setUploadedFiles(data.files || [])
    } catch (error) {
      console.error('Failed to load files:', error)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.pdf')) {
      alert('Please upload a PDF file')
      return
    }

    setUploading(true)
    setUploadProgress(`Uploading ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)...`)
    
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${apiUrl}/api/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const data = await response.json()
      setUploadProgress('Upload complete! ✓')
      alert(data.message || 'File uploaded successfully')
      await loadFiles()
    } catch (error) {
      setUploadProgress('')
      alert(`Error: ${error instanceof Error ? error.message : 'Failed to upload file'}`)
    } finally {
      setUploading(false)
      setTimeout(() => setUploadProgress(''), 2000)
      e.target.value = '' // Reset input
    }
  }

  const deleteFile = async (filename: string) => {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) return

    try {
      const response = await fetch(`${apiUrl}/api/files/${filename}`, {
        method: 'DELETE',
      })

      const data = await response.json()
      alert(data.message || 'File deleted successfully')
      await loadFiles()
    } catch (error) {
      alert(`Error: ${error instanceof Error ? error.message : 'Failed to delete file'}`)
    }
  }

  useEffect(() => {
    if (apiUrl) {
      loadFiles()
    }
  }, [apiUrl])

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-3xl">🏫</div>
          <h1 className="text-2xl font-bold text-gray-800">Scout</h1>
          <span className="text-sm text-gray-500">School Events Assistant</span>
        </div>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium"
        >
          ⚙️ Settings
        </button>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-blue-50 border-b px-6 py-4">
          <div className="max-w-4xl mx-auto space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                OpenAI API Key *
              </label>
              <input
                type="password"
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cohere API Key (optional, for reranking)
              </label>
              <input
                type="password"
                value={cohereKey}
                onChange={(e) => setCohereKey(e.target.value)}
                placeholder="Enter Cohere API key"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API URL
              </label>
              <input
                type="text"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="http://localhost:8000"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={useReranking}
                  onChange={(e) => setUseReranking(e.target.checked)}
                  disabled={!cohereKey}
                  className="rounded"
                />
                <span className="text-sm text-gray-700">Use Cohere Reranking</span>
              </label>
              <button
                onClick={prepareData}
                disabled={loading || !openaiKey}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                🔄 Prepare Data
              </button>
            </div>

            {/* File Management Section */}
            <div className="border-t pt-3 mt-3">
              <h3 className="text-sm font-medium text-gray-700 mb-2">📄 Newsletter Management</h3>
              
              {/* Upload Button */}
              <div className="mb-3">
                <label className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium w-fit ${
                  uploading 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-green-600 hover:bg-green-700 cursor-pointer'
                } text-white`}>
                  {uploading ? '⏳ Uploading...' : '📤 Upload Newsletter PDF'}
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileUpload}
                    disabled={uploading}
                    className="hidden"
                  />
                </label>
                {uploadProgress && (
                  <p className="text-sm text-blue-600 mt-2 animate-pulse">
                    {uploadProgress}
                  </p>
                )}
              </div>

              {/* File List */}
              <div className="bg-white rounded-lg p-3 max-h-40 overflow-y-auto">
                <p className="text-xs text-gray-500 mb-2">{uploadedFiles.length} files uploaded</p>
                {uploadedFiles.length === 0 ? (
                  <p className="text-sm text-gray-400 italic">No newsletters uploaded yet</p>
                ) : (
                  <ul className="space-y-1">
                    {uploadedFiles.map((file) => (
                      <li key={file} className="flex items-center justify-between text-sm py-1 px-2 hover:bg-gray-50 rounded">
                        <span className="text-gray-700 truncate flex-1">{file}</span>
                        <button
                          onClick={() => deleteFile(file)}
                          className="text-red-600 hover:text-red-800 text-xs ml-2"
                          title="Delete file"
                        >
                          🗑️
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                💡 After uploading, click "🔄 Prepare Data" to process newsletters
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🏫</div>
              <h2 className="text-2xl font-semibold text-gray-800 mb-2">
                Welcome to Scout!
              </h2>
              <p className="text-gray-600 mb-6">
                Ask me about school events and activities
              </p>
              <div className="bg-white rounded-lg p-4 inline-block text-left">
                <p className="text-sm text-gray-700 mb-2 font-medium">Try asking:</p>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• What events are happening this week?</li>
                  <li>• When is Spirit Day?</li>
                  <li>• Are there any upcoming deadlines?</li>
                </ul>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-800 border'
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border rounded-lg px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                  <span className="text-gray-600">Thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t bg-white px-6 py-4">
        <form onSubmit={sendMessage} className="max-w-4xl mx-auto">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Scout about school events..."
              disabled={loading || !openaiKey}
              className="flex-1 px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={loading || !input.trim() || !openaiKey}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>
          {!openaiKey && (
            <p className="text-sm text-amber-600 mt-2">
              ⚠️ Please add your OpenAI API key in Settings to start chatting
            </p>
          )}
        </form>
      </div>
    </div>
  )
}

