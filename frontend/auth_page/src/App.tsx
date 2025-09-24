import { AuthForm } from "./components/auth-form";

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <AuthForm />
      </div>
    </div>
  );
}