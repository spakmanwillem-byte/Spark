// Gedeeltelijke update - alleen Adres, Werk en Bio sectie
// Plaats dit in de bestaande file op de juiste plekken

// ADRES SECTIE - vervang de huidige adres sectie:
            {/* Adres */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">🏠 Adres</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-300 mb-2">Straat</label>
                  <input
                    type="text"
                    name="straat"
                    value={formData.straat || ''}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="Straatnaam"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Huisnummer</label>
                  <input
                    type="text"
                    name="huisnummer"
                    value={formData.huisnummer || ''}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="123"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Postcode</label>
                  <input
                    type="text"
                    name="postcode"
                    value={formData.postcode || ''}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="1234 AB"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Plaats</label>
                  <input
                    type="text"
                    name="plaats"
                    value={formData.plaats || ''}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="Amsterdam"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Land</label>
                  <input
                    type="text"
                    name="land"
                    value={formData.land || ''}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                  />
                </div>
              </div>
            </div>
