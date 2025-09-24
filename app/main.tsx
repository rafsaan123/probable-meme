import React, { useEffect, useState } from 'react';
import BTEBResultApp from './index';
import WelcomeScreen from './welcome';

export default function MainApp() {
  const [showWelcome, setShowWelcome] = useState(true);

  useEffect(() => {
    // Auto-transition after 3 seconds
    const timer = setTimeout(() => {
      setShowWelcome(false);
    }, 3000);

    return () => clearTimeout(timer);
  }, []);

  if (showWelcome) {
    return <WelcomeScreen />;
  }

  return <BTEBResultApp />;
}


