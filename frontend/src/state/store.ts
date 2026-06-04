import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./slices/auth";
import chatReducer from "./slices/chat";
import modelsReducer from "./slices/models";
import syncReducer from "./slices/sync";
import uiReducer from "./slices/ui";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    chat: chatReducer,
    models: modelsReducer,
    sync: syncReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ["auth/setError", "chat/setError", "models/setError", "sync/setError"],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
