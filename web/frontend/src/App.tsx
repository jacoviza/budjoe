import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import Shell from './components/layout/Shell';
import AccountsPage from './pages/AccountsPage';
import AccountDetailPage from './pages/AccountDetailPage';
import NotificationsPage from './pages/NotificationsPage';
import ActionsPage from './pages/ActionsPage';
import DuplicatesPage from './pages/DuplicatesPage';

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Shell>
          <Routes>
            <Route path="/accounts" element={<AccountsPage />} />
            <Route path="/accounts/:id" element={<AccountDetailPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/actions" element={<ActionsPage />} />
            <Route path="/duplicates" element={<DuplicatesPage />} />
            <Route path="/" element={<Navigate to="/accounts" replace />} />
          </Routes>
        </Shell>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
