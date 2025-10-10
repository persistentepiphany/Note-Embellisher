import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext'; // Adjust path
import { AuthForm } from './components/auth-form'; // Adjust path
import { Dashboard } from './components/Dashboard'; // From dashboard_page, adjust
import { NoteSubmission } from './components/NoteSubmission'; // From note_submission, adjust

function App() {
  const { currentUser, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>; // Or a spinner
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={currentUser ? <Navigate to="/dashboard" /> : <AuthForm />}
        />
        <Route
          path="/dashboard"
          element={currentUser ? <Dashboard /> : <Navigate to="/" />}
        />
        <Route
          path="/note-submission"
          element={currentUser ? <NoteSubmission /> : <Navigate to="/" />}
        />
      </Routes>
    </Router>
  );
}

export default App;