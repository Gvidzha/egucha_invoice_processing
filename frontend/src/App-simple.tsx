import './styles.css'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Invoice OCR Processor - TEST
          </h1>
          <p className="text-sm text-gray-600">
            Pavadzīmju apstrāde ar OCR un mašīnmācīšanos
          </p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Test lapa
          </h2>
          <p className="text-gray-600">
            Ja šī lapa parādās, tad React darbojas pareizi.
          </p>
        </div>
      </main>
    </div>
  )
}

export default App
