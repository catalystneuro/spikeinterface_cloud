import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import axios from 'axios';

import SpikeSorting from './pages/spikesorting/SpikeSorting';
import RunsPage from './pages/runs/RunsPage';
import Sidebar from './components/Sidebar';

const App: React.FC = () => {
  const [dandisets, setDandisets] = useState<string[]>([]);

  const fetchDandisets = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/dandi/get-dandisets-labels');
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
          <Route path="/runs" element={<RunsPage />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
