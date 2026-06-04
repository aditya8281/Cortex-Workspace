import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import type { CortexModel, CortexProvider, CortexRoutingProfile } from "@/types/api";

interface ModelsState {
  models: CortexModel[];
  providers: CortexProvider[];
  routingProfiles: CortexRoutingProfile[];
  selectedModel: CortexModel | null;
  loading: boolean;
  error: string | null;
}

const initialState: ModelsState = {
  models: [],
  providers: [],
  routingProfiles: [],
  selectedModel: null,
  loading: false,
  error: null,
};

export const modelsSlice = createSlice({
  name: "models",
  initialState,
  reducers: {
    setModels: (state, action: PayloadAction<CortexModel[]>) => {
      state.models = action.payload;
    },
    setProviders: (state, action: PayloadAction<CortexProvider[]>) => {
      state.providers = action.payload;
    },
    setRoutingProfiles: (state, action: PayloadAction<CortexRoutingProfile[]>) => {
      state.routingProfiles = action.payload;
    },
    setSelectedModel: (state, action: PayloadAction<CortexModel | null>) => {
      state.selectedModel = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const { setModels, setProviders, setRoutingProfiles, setSelectedModel, setLoading, setError } =
  modelsSlice.actions;
export default modelsSlice.reducer;
