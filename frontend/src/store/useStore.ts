import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, Project, Conversation } from '@/types';

interface AppState {
  // User state
  user: User | null;
  setUser: (user: User | null) => void;
  
  // Current project
  currentProject: Project | null;
  setCurrentProject: (project: Project | null) => void;
  
  // Current conversation
  currentConversation: Conversation | null;
  setCurrentConversation: (conversation: Conversation | null) => void;
  
  // UI state
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
  
  // Theme
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  
  // Reset
  reset: () => void;
}

const initialState = {
  user: null,
  currentProject: null,
  currentConversation: null,
  isSidebarOpen: true,
  theme: 'light' as const,
};

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      ...initialState,
      
      setUser: (user) => set({ user }),
      
      setCurrentProject: (project) => set({ 
        currentProject: project,
        currentConversation: null // Reset conversation when project changes
      }),
      
      setCurrentConversation: (conversation) => set({ currentConversation: conversation }),
      
      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      
      toggleTheme: () => set((state) => ({ 
        theme: state.theme === 'light' ? 'dark' : 'light' 
      })),
      
      reset: () => set(initialState),
    }),
    {
      name: 'dpa-storage',
      partialize: (state) => ({ 
        theme: state.theme,
        isSidebarOpen: state.isSidebarOpen,
        currentProject: state.currentProject 
      }),
    }
  )
);