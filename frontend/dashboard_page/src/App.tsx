import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { Dashboard } from "./components/Dashboard";

export default function App() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header - spans full width */}
      <Header />
      
      {/* Main content area with sidebar and dashboard */}
      <div className="flex">
        {/* Sidebar - forms the vertical part of the "Г" shape */}
        <Sidebar />
        
        {/* Dashboard - main content area */}
        <Dashboard />
      </div>
    </div>
  );
}