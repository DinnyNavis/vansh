import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../utils/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('vansh_token'));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (token) {
            api
                .get('/auth/me')
                .then((res) => {
                    setUser(res.data.user);
                })
                .catch(() => {
                    localStorage.removeItem('vansh_token');
                    localStorage.removeItem('vansh_user');
                    setToken(null);
                    setUser(null);
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, [token]);

    const login = useCallback(async (email, password) => {
        const res = await api.post('/auth/login', { email, password });
        const { token: newToken, user: userData } = res.data;
        localStorage.setItem('vansh_token', newToken);
        localStorage.setItem('vansh_user', JSON.stringify(userData));
        setToken(newToken);
        setUser(userData);
        return userData;
    }, []);

    const register = useCallback(async (name, email, password) => {
        const res = await api.post('/auth/register', { name, email, password });
        const { token: newToken, user: userData } = res.data;
        localStorage.setItem('vansh_token', newToken);
        localStorage.setItem('vansh_user', JSON.stringify(userData));
        setToken(newToken);
        setUser(userData);
        return userData;
    }, []);

    const logout = useCallback(() => {
        localStorage.removeItem('vansh_token');
        localStorage.removeItem('vansh_user');
        setToken(null);
        setUser(null);
    }, []);

    return (
        <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
}
