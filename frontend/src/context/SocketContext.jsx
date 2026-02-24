import { createContext, useContext, useEffect, useRef, useCallback, useState } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from './AuthContext';

const SOCKET_URL = import.meta.env.VITE_API_URL || ''; // Route through Vite proxy

const SocketContext = createContext(null);

export function SocketProvider({ children }) {
    const { token } = useAuth();
    const socketRef = useRef(null);
    const [connected, setConnected] = useState(false);

    // Only connect when user is authenticated
    useEffect(() => {
        if (!token) {
            if (socketRef.current) {
                socketRef.current.disconnect();
                socketRef.current = null;
                setConnected(false);
            }
            return;
        }

        const socket = io(SOCKET_URL, {
            transports: ['websocket', 'polling'], // Prioritize WS but allow polling
            auth: { token },
            reconnection: true,
            reconnectionAttempts: 10,
            reconnectionDelay: 2000,
            reconnectionDelayMax: 5000,
            timeout: 20000,
            forceNew: true
        });

        socket.on('connect', () => {
            console.log('[Socket] Connected');
            setConnected(true);
        });

        socket.on('disconnect', () => {
            console.log('[Socket] Disconnected');
            setConnected(false);
        });

        socket.on('connect_error', (err) => {
            console.log('[Socket] Connection error:', err.message);
        });

        socketRef.current = socket;

        return () => {
            socket.disconnect();
            socketRef.current = null;
            setConnected(false);
        };
    }, [token]);

    const joinProject = useCallback((projectId) => {
        if (socketRef.current?.connected) {
            socketRef.current.emit('join_project', { project_id: projectId });
        }
    }, []);

    const leaveProject = useCallback((projectId) => {
        if (socketRef.current?.connected) {
            socketRef.current.emit('leave_project', { project_id: projectId });
        }
    }, []);

    const onProgress = useCallback((callback) => {
        const socket = socketRef.current;
        if (!socket) return () => { };

        const wrappedCallback = (data) => {
            console.log('[Socket] Progress update received:', data);
            callback(data);
        };

        socket.on('progress_update', wrappedCallback);
        return () => socket.off('progress_update', wrappedCallback);
    }, []);

    const onRealtimeTranscript = useCallback((callback) => {
        const socket = socketRef.current;
        if (!socket) return () => { };

        const wrappedCallback = (data) => {
            callback(data);
        };

        socket.on('realtime_transcript', wrappedCallback);
        return () => socket.off('realtime_transcript', wrappedCallback);
    }, []);

    return (
        <SocketContext.Provider value={{ connected, joinProject, leaveProject, onProgress, onRealtimeTranscript, socketRef }}>
            {children}
        </SocketContext.Provider>
    );
}

export function useSocket() {
    const context = useContext(SocketContext);
    if (!context) throw new Error('useSocket must be used within SocketProvider');
    return context;
}
