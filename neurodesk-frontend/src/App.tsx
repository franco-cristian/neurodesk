import { useNeuroStore } from './store/useNeuroStore';
import { LoginScreen } from './components/LoginScreen';
import { DashboardLayout } from './components/DashboardLayout';
import { UserProfilePanel } from './components/panels/UserProfilePanel';
import { LiveLogPanel } from './components/panels/LiveLogPanel';
import { ChatInterface } from './components/panels/ChatInterface';

function App() {
  const isAuthenticated = useNeuroStore((state) => state.isAuthenticated);

  if (!isAuthenticated) return <LoginScreen />;

  return (
    <DashboardLayout 
      leftPanel={<UserProfilePanel />}
      centerPanel={<ChatInterface />}
      rightPanel={<LiveLogPanel />}
    />
  );
}

export default App;