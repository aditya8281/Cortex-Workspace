import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import type { SyncRun, WorkspaceIntelligence } from "@/types/api";

export interface SyncState {
  syncRuns: SyncRun[];
  currentRun: SyncRun | null;
  intelligence: WorkspaceIntelligence | null;
  loading: boolean;
  error: string | null;
  isIndexing: boolean;
}

const initialState: SyncState = {
  syncRuns: [],
  currentRun: null,
  intelligence: null,
  loading: false,
  error: null,
  isIndexing: false,
};

const syncSlice = createSlice({
  name: "sync",
  initialState,
  reducers: {
    setSyncRuns: (state, action: PayloadAction<SyncRun[]>) => {
      state.syncRuns = action.payload;
    },
    setCurrentRun: (state, action: PayloadAction<SyncRun | null>) => {
      state.currentRun = action.payload;
    },
    setIntelligence: (state, action: PayloadAction<WorkspaceIntelligence>) => {
      state.intelligence = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setIsIndexing: (state, action: PayloadAction<boolean>) => {
      state.isIndexing = action.payload;
    },
  },
});

export const { setSyncRuns, setCurrentRun, setIntelligence, setLoading, setError, setIsIndexing } = syncSlice.actions;
export default syncSlice.reducer;
