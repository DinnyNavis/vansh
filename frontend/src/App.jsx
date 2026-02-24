import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { AuthProvider, useAuth } from './context/AuthContext';
import { SocketProvider } from './context/SocketContext';
import ScrollToTop from './components/ScrollToTop';

// Lazy-loaded pages for faster initial load
const LandingPage = lazy(() => import('./pages/LandingPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Workspace = lazy(() => import('./pages/Workspace'));

const pageTransition = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.25 } },
};

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ivory">
        <div className="animate-pulse-gold">
          <h2 className="font-serif text-2xl text-gold">VANSH</h2>
        </div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" replace />;
}


function AppRoutes() {
  const location = useLocation();
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-ivory">
        <div className="animate-pulse-gold"><h2 className="font-serif text-2xl text-gold">VANSH</h2></div>
      </div>
    }>
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<motion.div {...pageTransition}><LandingPage /></motion.div>} />
          <Route path="/login" element={<motion.div {...pageTransition}><LoginPage /></motion.div>} />
          <Route path="/register" element={<motion.div {...pageTransition}><RegisterPage /></motion.div>} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <motion.div {...pageTransition}><Dashboard /></motion.div>
              </ProtectedRoute>
            }
          />
          <Route
            path="/workspace/:projectId"
            element={
              <ProtectedRoute>
                <motion.div {...pageTransition}><Workspace /></motion.div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AnimatePresence>
    </Suspense>
  );
}

import { ToastProvider } from './context/ToastContext';

export default function App() {
  return (
    <Router>
      <ScrollToTop />
      <AuthProvider>
        <SocketProvider>
          <ToastProvider>
            <AppRoutes />
          </ToastProvider>
        </SocketProvider>
      </AuthProvider>
    </Router>
  );
}
