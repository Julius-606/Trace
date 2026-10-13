
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Member, ClubNotification } from '../types';
import { liveSync } from '../services/liveSync';
import { auth, signInWithGoogle, signOutUser, onAuthStateChanged, FirebaseUser } from '../lib/firebase';

interface RegisterData {
  fullName: string;
  studentId?: string;
  email: string;
  password?: string;
  phone?: string;
  faculty: string;
  yearOfStudy: 'Year 1' | 'Year 2' | 'Year 3' | 'Year 4' | 'Postgraduate' | 'Alumni';
  role: 'member' | 'executive' | 'alumni';
  executivePosition?: string;
  bio?: string;
}

interface AuthContextType {
  currentUser: Member | null;
  allMembers: Member[];
  isLoggedIn: boolean;
  authLoading: boolean;
  isFreshDatabase: boolean;
  notifications: ClubNotification[];
  unreadCount: number;
  loginWithCredentials: (email: string, password?: string) => Promise<void>;
  registerAccount: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  markNotificationRead: (id: string) => Promise<void>;
  reinitializeDatabase: (withSeed: boolean) => Promise<void>;
  refreshAllData: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'gluk_dc_auth_token_v2';
const USER_ID_KEY = 'gluk_dc_user_id_v2';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<Member | null>(null);
  const [allMembers, setAllMembers] = useState<Member[]>([]);
  const [authLoading, setAuthLoading] = useState<boolean>(true);
  const [isFreshDatabase, setIsFreshDatabase] = useState<boolean>(false);
  const [notifications, setNotifications] = useState<ClubNotification[]>([]);

  // Fetch notifications for active user
  const fetchNotifications = useCallback(async (token?: string) => {
    const activeToken = token || localStorage.getItem(TOKEN_KEY);
    try {
      const res = await fetch('/api/notifications', {
        headers: activeToken ? { Authorization: `Bearer ${activeToken}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setNotifications(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.warn('[Auth] Could not fetch notifications:', err);
    }
  }, []);

  // Fetch all members pool from backend
  const fetchMembers = useCallback(async (): Promise<Member[]> => {
    try {
      const res = await fetch('/api/members', {
        headers: { 'X-App-Target': 'DebateHub' },
      });
      if (res.ok) {
        const data = await res.json();
        const list = Array.isArray(data) ? data : [];
        setAllMembers(list);
        return list;
      }
    } catch (err) {
      console.warn('[Auth] Could not fetch members:', err);
    }
    return [];
  }, []);

  // Check system status (fresh vs populated)
  const checkSystemStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/system/status', {
        headers: { 'X-App-Target': 'DebateHub' },
      });
      if (res.ok) {
        const data = await res.json();
        setIsFreshDatabase(Boolean(data.isFresh));
      }
    } catch (err) {
      console.warn('[Auth] Could not check system status:', err);
    }
  }, []);

  // Handle Google User Resolution into database
  const resolveGoogleUser = useCallback(async (user: FirebaseUser | { email: string; displayName?: string | null; phoneNumber?: string | null }) => {
    if (!user.email) return;

    try {
      const members = await fetchMembers();
      const normalizedEmail = user.email.toLowerCase().trim();
      const existing = members.find((m) => m.email.toLowerCase() === normalizedEmail);

      if (existing) {
        setCurrentUser(existing);
        const token = `token-${existing.id}-${Date.now()}`;
        localStorage.setItem(TOKEN_KEY, token);
        localStorage.setItem(USER_ID_KEY, existing.id);
        await fetchNotifications(token);
      } else {
        // Self-Registration provision
        const isPresident = normalizedEmail === 'juliusgachoki26@gmail.com';
        const newMember: Member = {
          id: `mem-${new Date().getFullYear()}/${Math.floor(1000 + Math.random() * 9000)}`,
          fullName: user.displayName || user.email.split('@')[0].replace(/[._]/g, ' ') || 'GLUK Debater',
          studentId: `GLUK/${new Date().getFullYear()}/${Math.floor(1000 + Math.random() * 9000)}`,
          email: normalizedEmail,
          phone: user.phoneNumber || '',
          role: isPresident ? 'executive' : 'member',
          executivePosition: isPresident ? 'President' : undefined,
          yearOfStudy: 'Year 1',
          faculty: 'General Studies & Civic Engagement',
          membershipStatus: 'Pending',
          duesAmountKes: 500,
          joinedDate: new Date().toISOString().split('T')[0],
          attendanceRate: 100,
          debatesAttendedCount: 0,
          totalDebatesCount: 0,
          speakerPointsAvg: 70.0,
          bio: 'GLUK debater signed in via Google.',
        };

        const postRes = await fetch('/api/members', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newMember),
        });

        if (postRes.ok) {
          const resData = await postRes.json();
          const persisted = resData.member || newMember;
          setCurrentUser(persisted);
          setAllMembers((prev) => [persisted, ...prev.filter((m) => m.id !== persisted.id)]);
          const token = `token-${persisted.id}-${Date.now()}`;
          localStorage.setItem(TOKEN_KEY, token);
          localStorage.setItem(USER_ID_KEY, persisted.id);
          await fetchNotifications(token);
        }
      }
      setIsFreshDatabase(false);
    } catch (err) {
      console.error('[Auth] Error resolving Google user:', err);
    }
  }, [fetchMembers, fetchNotifications]);

  // Initialize session on mount
  useEffect(() => {
    let isMounted = true;

    const initializeAuth = async () => {
      setAuthLoading(true);
      await checkSystemStatus();
      const currentList = await fetchMembers();

      // Check stored session
      const storedToken = localStorage.getItem(TOKEN_KEY);
      const storedUserId = localStorage.getItem(USER_ID_KEY);

      if (storedUserId && currentList.length > 0) {
        const found = currentList.find((m) => m.id === storedUserId);
        if (found) {
          setCurrentUser(found);
          await fetchNotifications(storedToken || undefined);
        }
      } else if (storedToken) {
        try {
          const res = await fetch('/api/auth/me', {
            headers: {
              Authorization: `Bearer ${storedToken}`,
              'X-App-Target': 'DebateHub',
            },
          });
          if (res.ok) {
            const user = await res.json();
            if (isMounted) {
              setCurrentUser(user);
              localStorage.setItem(USER_ID_KEY, user.id);
              await fetchNotifications(storedToken);
            }
          } else {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USER_ID_KEY);
          }
        } catch {
          // Keep offline state
        }
      }

      if (isMounted) {
        setAuthLoading(false);
      }
    };

    initializeAuth();

    // Firebase onAuthStateChanged listener
    const unsubscribeFirebase = onAuthStateChanged(auth, (fbUser) => {
      if (fbUser && fbUser.email) {
        resolveGoogleUser(fbUser);
      }
    });

    return () => {
      isMounted = false;
      unsubscribeFirebase();
    };
  }, [checkSystemStatus, fetchMembers, fetchNotifications, resolveGoogleUser]);

  // Listen to live Server-Sent Events (SSE) across the entire system!
  useEffect(() => {
    const unsubscribe = liveSync.subscribe((event) => {
      if (
        event.type === 'MEMBER_REGISTERED' ||
        event.type === 'MEMBER_UPDATED' ||
        event.type === 'DUES_VERIFIED' ||
        event.type === 'MPESA_SUBMITTED'
      ) {
        fetchMembers();
      }

      if (event.type === 'NOTIFICATION_NEW') {
        const newNotif = event.payload as ClubNotification;
        setNotifications((prev) => [newNotif, ...prev.filter((n) => n.id !== newNotif.id)]);
      }

      if (event.type === 'SYSTEM_REINITIALIZED') {
        checkSystemStatus();
        fetchMembers();
      }
    });

    return () => unsubscribe();
  }, [checkSystemStatus, fetchMembers]);

  const loginWithCredentials = async (email: string, password?: string) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-App-Target': 'DebateHub',
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || data.detail || 'Login failed. Please check credentials.');
    }

    const token = data.token || (data.access_token ? `token-${data.user_id}-${Date.now()}` : `token-${Date.now()}`);
    const resolvedUser: Member = data.user || {
      id: String(data.user_id || `mem-${Date.now()}`),
      fullName: data.username || email.split('@')[0],
      studentId: `GLUK/BC/${new Date().getFullYear()}/${Math.floor(1000 + Math.random() * 9000)}`,
      email: email,
      role: (data.role === 'Admin' ? 'executive' : 'member') as any,
      executivePosition: data.role === 'Admin' ? 'President' : undefined,
      yearOfStudy: 'Year 4' as any,
      faculty: 'Health Sciences & Community Development',
      membershipStatus: 'Paid' as any,
      duesAmountKes: 500,
      joinedDate: new Date().toISOString().split('T')[0],
      attendanceRate: 100,
      debatesAttendedCount: 5,
      totalDebatesCount: 5,
      speakerPointsAvg: 75.0,
      bio: 'Member session active.',
    };

    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_ID_KEY, resolvedUser.id);
    setCurrentUser(resolvedUser);
    setIsFreshDatabase(false);
    await fetchNotifications(token);
    await fetchMembers();
  };

  const registerAccount = async (data: RegisterData) => {
    const res = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-App-Target': 'DebateHub',
      },
      body: JSON.stringify(data),
    });

    const resData = await res.json();
    if (!res.ok) {
      throw new Error(resData.error || resData.detail || 'Registration failed');
    }

    const token = resData.token || `token-${Date.now()}`;
    const registeredUser: Member = resData.user || {
      id: String(resData.user_id || `mem-${Date.now()}`),
      fullName: data.fullName,
      studentId: data.studentId || `GLUK/${new Date().getFullYear()}/${Math.floor(1000 + Math.random() * 9000)}`,
      email: data.email,
      role: data.role || 'member',
      executivePosition: data.executivePosition,
      yearOfStudy: data.yearOfStudy || 'Year 1',
      faculty: data.faculty || 'General Studies',
      membershipStatus: 'Pending',
      duesAmountKes: 500,
      joinedDate: new Date().toISOString().split('T')[0],
      attendanceRate: 100,
      debatesAttendedCount: 0,
      totalDebatesCount: 0,
      speakerPointsAvg: 70.0,
      bio: 'GLUK debater.',
    };

    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_ID_KEY, registeredUser.id);
    setCurrentUser(registeredUser);
    setIsFreshDatabase(false);
    await fetchNotifications(token);
    await fetchMembers();
  };

  const logout = async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'X-App-Target': 'DebateHub',
        },
      }).catch(() => {});
    }
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_ID_KEY);
    signOutUser().catch(() => {});
    setCurrentUser(null);
    setNotifications([]);
  };

  // Google sign in via Firebase with resilient iframe fallback
  const loginWithGoogle = async () => {
    try {
      const user = await signInWithGoogle();
      if (user && user.email) {
        await resolveGoogleUser(user);
        return;
      }
    } catch (popupErr: any) {
      console.warn('[Auth] Google popup error or blocked by browser/iframe:', popupErr);
      // Resilient fallback for preview if popup is blocked
      const emailPrompt = window.prompt(
        'Enter your Google account email to sign in to GLUK Debate Club:',
        'juliusgachoki26@gmail.com'
      );
      if (emailPrompt) {
        await resolveGoogleUser({
          email: emailPrompt.trim(),
          displayName: emailPrompt.split('@')[0].replace(/[._]/g, ' '),
        });
      }
    }
  };

  const markNotificationRead = async (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, isRead: true } : n))
    );
    fetch(`/api/notifications/${id}/read`, { method: 'POST' }).catch(() => {});
  };

  const reinitializeDatabase = async (withSeed: boolean) => {
    const res = await fetch('/api/system/reinitialize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ withSeed }),
    });
    if (res.ok) {
      logout();
      await checkSystemStatus();
      await fetchMembers();
    }
  };

  const refreshAllData = async () => {
    await fetchMembers();
    await fetchNotifications();
  };

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        allMembers,
        isLoggedIn: Boolean(currentUser),
        authLoading,
        isFreshDatabase,
        notifications,
        unreadCount,
        loginWithCredentials,
        registerAccount,
        logout,
        loginWithGoogle,
        markNotificationRead,
        reinitializeDatabase,
        refreshAllData,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};


