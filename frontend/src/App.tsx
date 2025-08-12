import React from "react";
import { Home } from './pages/Home';
import { Loader } from './components/Loader';

export default function App() {
  const [ready, setReady] = React.useState(false);

  React.useEffect(() => {
    const t = setTimeout(() => setReady(true), 150)
    return () => clearTimeout(t)
  }, [])

  if (!ready) return <Loader label="Starting app..." />

  return <Home />

}
