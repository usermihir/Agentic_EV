import { Routes, Route, Navigate, Link } from 'react-router-dom';
import Driver from './pages/Driver';
import Operator from './pages/Operator';

function Header() {
  return (
    <header className="p-4 border-b">
      <nav>
        <Link to="/driver" className="mr-4">Driver</Link>
        <Link to="/operator">Operator</Link>
      </nav>
    </header>
  );
}

export default function App() {
  return (
    <div>
      <Header />
      <main className="p-4">
        <Routes>
          <Route path="/" element={<Navigate to="/driver" replace />} />
          <Route path="/driver" element={<Driver />} />
          <Route path="/operator" element={<Operator />} />
        </Routes>
      </main>
    </div>
  );
}