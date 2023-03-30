import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import axios from 'axios';

import SpikeSorting from './pages/SpikeSorting';
import Sidebar from './components/Sidebar';

const App: React.FC = () => {
  const [dandisets, setDandisets] = useState<string[]>([]);

  const fetchDandisets = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/dandi/get-dandisets-labels');
      setDandisets(response.data.labels);
    } catch (error) {
      console.error('Failed to fetch DANDIsets:', error);
    }
  };

  useEffect(() => {
    fetchDandisets();
  }, []);

  return (
    <Router>
      <div style={{ display: 'flex' }}>
        <Sidebar />
        <Routes>
          <Route path="/sorting" element={<SpikeSorting dandisets_labels={dandisets} />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
