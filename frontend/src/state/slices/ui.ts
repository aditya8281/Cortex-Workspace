import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface UIState {
  sidebarOpen: boolean;
  currentTab: string;
  notificationCenter: boolean;
  commandPaletteOpen: boolean;
}

const initialState: UIState = {
  sidebarOpen: true,
  currentTab: "chat",
  notificationCenter: false,
  commandPaletteOpen: false,
};

export const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    setCurrentTab: (state, action: PayloadAction<string>) => {
      state.currentTab = action.payload;
    },
    toggleNotificationCenter: (state) => {
      state.notificationCenter = !state.notificationCenter;
    },
    toggleCommandPalette: (state) => {
      state.commandPaletteOpen = !state.commandPaletteOpen;
    },
  },
});

export const { toggleSidebar, setSidebarOpen, setCurrentTab, toggleNotificationCenter, toggleCommandPalette } =
  uiSlice.actions;
export default uiSlice.reducer;
