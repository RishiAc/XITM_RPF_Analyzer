import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { supabase } from "../SupaBase/supabaseClient";
import { authConfig } from "../config/authConfig";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAdmin = useMemo(() => {
    if (!user?.email) return false;
    return authConfig.adminEmails.includes(user.email.toLowerCase());
  }, [user]);

  const initializeSession = useCallback(async () => {
    setIsLoading(true);
    try {
      const {
        data: { session: activeSession },
        error,
      } = await supabase.auth.getSession();

      if (error) {
        console.error("Error retrieving session:", error);
        setSession(null);
        setUser(null);
        return;
      }

      setSession(activeSession);
      setUser(activeSession?.user ?? null);
    } catch (err) {
      console.error("Unexpected error retrieving session:", err);
      setSession(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    initializeSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession);
      setUser(newSession?.user ?? null);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [initializeSession]);

  const signOut = useCallback(async () => {
    try {
      await supabase.auth.signOut();
      setSession(null);
      setUser(null);
    } catch (error) {
      console.error("Error during sign out:", error);
    }
  }, []);

  const value = useMemo(
    () => ({
      session,
      user,
      isAdmin,
      isLoading,
      refreshSession: initializeSession,
      signOut,
    }),
    [session, user, isAdmin, isLoading, initializeSession, signOut]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};


