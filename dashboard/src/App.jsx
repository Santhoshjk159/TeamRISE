import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import PredictionPage from './pages/PredictionPage';
import OptimizationPage from './pages/OptimizationPage';
import GoldenSignaturePage from './pages/GoldenSignaturePage';
import CarbonPage from './pages/CarbonPage';
import DigitalTwinPage from './pages/DigitalTwinPage';
import DecisionPage from './pages/DecisionPage';
import ValidationPage from './pages/ValidationPage';

export default function App() {
  return (
    <div className="flex min-h-screen bg-surface-950">
      <Sidebar />
      <main className="flex-1 min-w-0 overflow-y-auto">
        <div className="max-w-[1600px] mx-auto p-6 lg:p-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/predictions" element={<PredictionPage />} />
            <Route path="/optimization" element={<OptimizationPage />} />
            <Route path="/golden-signature" element={<GoldenSignaturePage />} />
            <Route path="/carbon" element={<CarbonPage />} />
            <Route path="/digital-twin" element={<DigitalTwinPage />} />
            <Route path="/decisions" element={<DecisionPage />} />
            <Route path="/validation" element={<ValidationPage />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
