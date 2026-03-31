import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { LoginForm } from "./components/auth/LoginForm";
import { DashboardPage } from "./components/dashboard/DashboardPage";

// Protected Route Component
function ProtectedRoute({ children }) {
  const { isLoggedIn, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-amber-500/30 border-t-amber-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Laden...</p>
        </div>
      </div>
    );
  }

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

// Public Route (redirect if logged in)
function PublicRoute({ children }) {
  const { isLoggedIn, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (isLoggedIn) {
    return <Navigate to="/" replace />;
  }

  return children;
}

// Placeholder Page for modules that are not yet implemented
function PlaceholderPage({ title, description }) {
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-8">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <span className="text-3xl">🚧</span>
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">{title}</h1>
        <p className="text-slate-400 mb-6">{description}</p>
        <p className="text-sm text-slate-500">
          Deze module wordt binnenkort toegevoegd.
        </p>
      </div>
    </div>
  );
}

// App Routes
function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginForm />
          </PublicRoute>
        }
      />
      
      {/* Protected Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />

      {/* Placeholder Routes - for future modules */}
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <PlaceholderPage 
              title="Gesprekken" 
              description="Chat met Spark en bekijk je gespreksgeschiedenis."
            />
          </ProtectedRoute>
        }
      />
      <Route
        path="/knowledge"
        element={
          <ProtectedRoute>
            <PlaceholderPage 
              title="Kennisbank" 
              description="Beheer en doorzoek je kennis entries."
            />
          </ProtectedRoute>
        }
      />
      <Route
        path="/calendar"
        element={
          <ProtectedRoute>
            <PlaceholderPage 
              title="Agenda" 
              description="Bekijk je afspraken en taken."
            />
          </ProtectedRoute>
        }
      />
      <Route
        path="/spark/*"
        element={
          <ProtectedRoute>
            <PlaceholderPage 
              title="Spark AI" 
              description="Spark Brain, triggers en emoties configuratie."
            />
          </ProtectedRoute>
        }
      />
      <Route
        path="/modules/*"
        element={
          <ProtectedRoute>
            <PlaceholderPage 
              title="Modules" 
              description="Achievements, Wallet, Community en meer."
            />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/*"
        element={
          <ProtectedRoute>
            <PlaceholderPage 
              title="Beheer" 
              description="Gebruikersbeheer, analytics en instellingen."
            />
          </ProtectedRoute>
        }
      />

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
