
import { useEffect, useState } from "react";
import { supabase } from "../lib/supabase";
import SplashScreen from "./SplashScreen";
import Login from "./Login";
import Signup from "./Signup";
import "./Auth.css";

export default function AuthGate({ children }) {
  const [showSplash, setShowSplash] = useState(true);
  const [session, setSession] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [page, setPage] = useState("login");

  useEffect(() => {
    const splashTimer = setTimeout(() => {
      setShowSplash(false);
    }, 3000);

    supabase.auth.getSession().then(({ data, error }) => {
      if (error) {
        console.error("Session check failed:", error.message);
      }

      setSession(data?.session ?? null);
      setAuthReady(true);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession);
      setAuthReady(true);
    });

    return () => {
      clearTimeout(splashTimer);
      subscription.unsubscribe();
    };
  }, []);

  if (showSplash || !authReady) {
    return <SplashScreen />;
  }

  if (!session) {
    return page === "signup" ? (
      <Signup onLogin={() => setPage("login")} />
    ) : (
      <Login onSignup={() => setPage("signup")} />
    );
  }

  return (
    <>
      <div className="auth-session-bar">
        <span>{session.user.email}</span>
        <button onClick={() => supabase.auth.signOut()}>
          Sign Out
        </button>
      </div>

      {children}
    </>
  );
}
